import CoreML
import CryptoKit
import Darwin
import Foundation
import SwiftDataFrame
import SwiftML
import SwiftPreprocessing

private struct Raw: Decodable {
    let features: [[Double]]
    let splits: [String: [Int]]
}
private struct Fixture: Decodable {
    let columns: [[Double]]
    let expected: [Double]
    let layers: [LayerWeights]
}
private func seconds(_ start: ContinuousClock.Instant) -> Double {
    let duration = start.duration(to: .now).components
    return Double(duration.seconds) + Double(duration.attoseconds) / 1e18
}
private enum Invalid: Error { case fixture, scaling, provenance, admission, output }

@main struct RepresentativeWorkflowProbe {
    static func main() async throws {
        let args = CommandLine.arguments
        guard args.count == 4 else { throw Invalid.fixture }
        let rawURL = URL(fileURLWithPath: args[1])
        let fixtureURL = URL(fileURLWithPath: args[2])
        let output = URL(fileURLWithPath: args[3])
        let rawData = try Data(contentsOf: rawURL)
        let fixtureData = try Data(contentsOf: fixtureURL)
        let raw = try JSONDecoder().decode(Raw.self, from: rawData)
        let fixture = try JSONDecoder().decode(Fixture.self, from: fixtureData)
        let names = fixture.columns.indices.map { "feature_\($0)" }
        let constructionStart = ContinuousClock.now
        let columns: [[Double]] = names.indices.map { column in raw.features.map { $0[column] } }
        let all = try PreparedNumericBatch(columnNames: names, columns: columns)
        guard let trainingIDs = raw.splits["train"], let testIDs = raw.splits["test"] else { throw Invalid.fixture }
        let training = try all.selectingRows(trainingIDs)
        let test = try all.selectingRows(testIDs)
        let constructionSeconds = seconds(constructionStart)
        let fitStart = ContinuousClock.now
        var scaler = StandardScaler()
        try scaler.fit(training)
        let fitSeconds = seconds(fitStart)
        let scaled = try scaler.transform(test)
        guard scaled.rowCount == fixture.expected.count else { throw Invalid.fixture }
        var scalingError = 0.0
        for row in 0..<scaled.rowCount {
            for column in names.indices {
                scalingError = max(scalingError, abs(scaled[row, column]! - fixture.columns[column][row]))
            }
        }
        guard scalingError < 1e-10 else { throw Invalid.scaling }
        let exportStart = ContinuousClock.now
        let artifact = CoreMLExporter.exportBinaryMLPRegressor(inputNames: ["features"], outputName: "result", layers: fixture.layers)
        let exportSeconds = seconds(exportStart)
        let modelURL = output.deletingPathExtension().appendingPathExtension("mlmodel")
        try artifact.write(to: modelURL)
        let compileStart = ContinuousClock.now
        let compiled = try await MLModel.compileModel(at: modelURL)
        let compileSeconds = seconds(compileStart)
        defer { try? FileManager.default.removeItem(at: compiled) }
        let loadStart = ContinuousClock.now
        let predictor = try CoreMLPredictor(compiledModelURL: compiled, inputColumns: names,
            outputName: "result", computeUnits: .cpuOnly)
        let loadSeconds = seconds(loadStart)
        let budget = try MemoryBudget(limit: 256 * 1_048_576)
        var samples: [[String: Any]] = []
        var first: [String: Any] = [:]
        var referenceExceedances = 0
        var outputHashes = Set<String>()
        var beforeUsage = rusage()
        guard getrusage(RUSAGE_SELF, &beforeUsage) == 0 else { throw Invalid.output }
        for iteration in 0..<36 {
            let start = ContinuousClock.now
            let prepared = try scaler.transform(test)
            let preparationSeconds = seconds(start)
            let result = try await predictor.predict(prepared, budget: budget,
                workspaceBytes: 8 * 1_048_576, maximumBatchSize: min(test.rowCount, 32))
            let wallSeconds = seconds(start)
            guard result.values.originalRowIndices == testIDs else { throw Invalid.provenance }
            guard await budget.reservedBytes == 0 else { throw Invalid.admission }
            var values = [Double]()
            var largestError = 0.0
            var mismatches = 0
            for row in 0..<test.rowCount {
                guard let value = result.values[row, 0], value.isFinite else { throw Invalid.output }
                values.append(value)
                let difference = abs(value - fixture.expected[row])
                largestError = max(largestError, difference)
                if difference > 1e-5 + 1e-5 * abs(fixture.expected[row]) { mismatches += 1 }
            }
            if mismatches > 0 { referenceExceedances += 1 }
            let hash = values.withUnsafeBytes { SHA256.hash(data: Data($0)).map { String(format: "%02x", $0) }.joined() }
            outputHashes.insert(hash)
            let sample: [String: Any] = ["preparationSeconds": preparationSeconds,
                "wallSeconds": wallSeconds, "maximumAbsoluteError": largestError,
                "mismatchedValues": mismatches, "inputPackingBytes": result.inputPackingBytes,
                "outputCopyBytes": result.outputCopyBytes, "outputSHA256": hash,
                "thermalState": ProcessInfo.processInfo.thermalState.rawValue]
            if iteration == 0 { first = sample }
            if iteration >= 4 { samples.append(sample) }
        }
        guard outputHashes.count == 1 else { throw Invalid.output }
        var usage = rusage()
        guard getrusage(RUSAGE_SELF, &usage) == 0 else { throw Invalid.output }
        let userCPU = Double(usage.ru_utime.tv_sec - beforeUsage.ru_utime.tv_sec)
            + Double(usage.ru_utime.tv_usec - beforeUsage.ru_utime.tv_usec) / 1e6
        let systemCPU = Double(usage.ru_stime.tv_sec - beforeUsage.ru_stime.tv_sec)
            + Double(usage.ru_stime.tv_usec - beforeUsage.ru_stime.tv_usec) / 1e6
        let report: [String: Any] = ["rawSHA256": SHA256.hash(data: rawData).map { String(format: "%02x", $0) }.joined(),
            "fixtureSHA256": SHA256.hash(data: fixtureData).map { String(format: "%02x", $0) }.joined(),
            "modelSHA256": SHA256.hash(data: artifact).map { String(format: "%02x", $0) }.joined(),
            "rows": test.rowCount, "columns": names.count, "originalRowIndices": testIDs,
            "constructionSeconds": constructionSeconds, "fitSeconds": fitSeconds, "exportSeconds": exportSeconds,
            "compileSeconds": compileSeconds, "loadSeconds": loadSeconds, "maximumScalingDifference": scalingError,
            "first": first, "samples": samples, "referenceExceedances": referenceExceedances,
            "budgetPeak": await budget.peak, "reservedBytesAfterPrediction": await budget.reservedBytes,
            "processPeakRSSBytes": Int64(usage.ru_maxrss), "computePolicy": "cpuOnly",
            "selfUserCPUSeconds": userCPU, "selfSystemCPUSeconds": systemCPU,
            "cpuScope": "36 requests including validation, hashing and telemetry; this process only, excludes Core ML service CPU work",
            "wallScope": "StandardScaler.transform on held-out raw prepared input through public example prediction and owned output; validation is outside timing",
            "deploymentScope": "export, compile, load separate; compilation may use Core ML caches; source decoding excluded"]
        try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys]).write(to: output)
    }
}
