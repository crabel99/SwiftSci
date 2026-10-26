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
}
private enum Invalid: Error { case arguments, fixture, scaling, provenance, output, admission, recovery }
private enum Route: String, CaseIterable, Sendable { case direct, prepared, fused }
private struct Sample: Codable, Sendable {
    let route: String
    let variant: Int
    let caller: Int
    let predictionSeconds: Double
    let values: [Double]
    let originalRowIndices: [Int]
    let maximumAbsoluteError: Double
    let mismatchedValues: Int
    let inputPackingBytes: Int
    let outputCopyBytes: Int
    let outputSHA256: String
}
private struct ScopeResult: Sendable {
    let samples: [Sample]
    let retained: CoreMLPreparedMatrix
    let preparation: CoreMLMatrixInputPreparation
}
private func seconds(_ start: ContinuousClock.Instant) -> Double {
    let duration = start.duration(to: .now).components
    return Double(duration.seconds) + Double(duration.attoseconds) / 1e18
}
private func sample(_ prediction: CoreMLPrediction, route: String, variant: Int, caller: Int,
                    elapsed: Double, rows: [Int], expected: [Double], inputBytes: Int) throws -> Sample {
    guard prediction.values.rowCount == rows.count, prediction.values.columnCount == 1,
          prediction.values.originalRowIndices == rows else { throw Invalid.provenance }
    guard prediction.inputPackingBytes == inputBytes,
          prediction.outputCopyBytes == rows.count * MemoryLayout<Double>.stride else { throw Invalid.output }
    var values: [Double] = []
    var error = 0.0
    var mismatches = 0
    for row in rows.indices {
        guard let value = prediction.values[row, 0], value.isFinite else { throw Invalid.output }
        values.append(value)
        let difference = abs(value - expected[row])
        error = max(error, difference)
        if difference > 1e-5 + 1e-5 * abs(expected[row]) { mismatches += 1 }
    }
    let hash = values.withUnsafeBytes { SHA256.hash(data: Data($0)).map { String(format: "%02x", $0) }.joined() }
    return Sample(route: route, variant: variant, caller: caller, predictionSeconds: elapsed,
        values: values, originalRowIndices: rows, maximumAbsoluteError: error, mismatchedValues: mismatches,
        inputPackingBytes: prediction.inputPackingBytes, outputCopyBytes: prediction.outputCopyBytes, outputSHA256: hash)
}
private func runScopes(compiled: URL, policy: String, names: [String], raw: [PreparedNumericBatch],
    scaled: [PreparedNumericBatch], expected: [[Double]], plan: StandardPreprocessingPlan,
    elementBytes: Int, poolBudget: MemoryBudget, inputBudget: MemoryBudget) async throws -> [Sample] {
    let configuration = try CoreMLMatrixPool.Configuration(maximumConcurrentPredictions: 2,
        retainedBytes: 64 * 1_048_576, requestBytes: 8 * 1_048_576)
    let units: MLComputeUnits = policy == "cpu" ? .cpuOnly : .cpuAndNeuralEngine
    let inputBytes = raw[0].rowCount * names.count * elementBytes
    let scope = try await CoreMLMatrixPool.withPool(compiledModelURL: compiled, inputColumns: names,
        outputName: "result", computeUnits: units, budget: poolBudget, configuration: configuration) { pool in
        let preparation = try await pool.inputPreparation()
        var prepared: [CoreMLPreparedMatrix] = []
        var fused: [CoreMLPreparedMatrix] = []
        for variant in raw.indices {
            prepared.append(try await pool.prepare(scaled[variant], budget: inputBudget))
            fused.append(try await preparation.prepare(raw[variant], preprocessing: plan, budget: inputBudget))
        }
        let preparedInputs = prepared
        let fusedInputs = fused
        var records: [Sample] = []
        for variant in raw.indices {
            for route in Route.allCases {
                let start = ContinuousClock.now
                let result: CoreMLPrediction
                switch route {
                case .direct: result = try await pool.predict(scaled[variant])
                case .prepared: result = try await pool.predict(preparedInputs[variant])
                case .fused: result = try await pool.predict(fusedInputs[variant])
                }
                records.append(try sample(result, route: route.rawValue, variant: variant, caller: -1,
                    elapsed: seconds(start), rows: raw[variant].originalRowIndices,
                    expected: expected[variant], inputBytes: inputBytes))
            }
        }
        let baselines = raw.indices.map { variant in records.first { $0.variant == variant }!.values }
        guard records.allSatisfy({ $0.values == baselines[$0.variant] }) else { throw Invalid.output }
        try await withThrowingTaskGroup(of: [Sample].self) { group in
            for caller in 0..<4 {
                group.addTask {
                    var samples: [Sample] = []
                    for iteration in 0..<6 {
                        let variant = (iteration + caller) % raw.count
                        let route = Route.allCases[iteration % Route.allCases.count]
                        let start = ContinuousClock.now
                        let result: CoreMLPrediction
                        switch route {
                        case .direct: result = try await pool.predict(scaled[variant])
                        case .prepared: result = try await pool.predict(preparedInputs[variant])
                        case .fused: result = try await pool.predict(fusedInputs[variant])
                        }
                        let record = try sample(result, route: route.rawValue, variant: variant, caller: caller,
                            elapsed: seconds(start), rows: raw[variant].originalRowIndices,
                            expected: expected[variant], inputBytes: inputBytes)
                        guard record.values == baselines[variant] else { throw Invalid.output }
                        samples.append(record)
                    }
                    return samples
                }
            }
            for try await values in group { records.append(contentsOf: values) }
        }
        var invalidColumns = scaled[0].columnNames.indices.map { column in
            (0..<scaled[0].rowCount).map { scaled[0][$0, column]! }
        }
        invalidColumns[0][0] = Double.greatestFiniteMagnitude
        let invalidInput = try PreparedNumericBatch(columnNames: names, columns: invalidColumns)
        var rejected = false
        do { _ = try await pool.predict(invalidInput) }
        catch SwiftMLError.invalidParameter(_) { rejected = true }
        guard rejected else { throw Invalid.recovery }
        var invalidRawColumns = raw[0].columnNames.indices.map { column in
            (0..<raw[0].rowCount).map { raw[0][$0, column]! }
        }
        invalidRawColumns[0][0] = .infinity
        let invalidRaw = try PreparedNumericBatch(columnNames: names, columns: invalidRawColumns)
        rejected = false
        do { _ = try await preparation.prepare(invalidRaw, preprocessing: plan, budget: inputBudget) }
        catch SwiftMLError.invalidParameter(_) { rejected = true }
        guard rejected else { throw Invalid.recovery }
        let start = ContinuousClock.now
        let recovered = try await pool.predict(fusedInputs[0])
        let recovery = try sample(recovered, route: "afterRejection", variant: 0, caller: -1,
            elapsed: seconds(start), rows: raw[0].originalRowIndices, expected: expected[0], inputBytes: inputBytes)
        guard recovery.values == baselines[0] else { throw Invalid.recovery }
        records.append(recovery)
        return ScopeResult(samples: records, retained: fusedInputs[0], preparation: preparation)
    }
    guard await poolBudget.reservedBytes == 0, await inputBudget.reservedBytes > 0 else { throw Invalid.admission }
    let additional = try await CoreMLMatrixPool.withPool(compiledModelURL: compiled, inputColumns: names,
        outputName: "result", computeUnits: units, budget: poolBudget, configuration: configuration) { pool in
        let start = ContinuousClock.now
        let result = try await pool.predict(scope.retained)
        let retained = try sample(result, route: "crossPoolRetained", variant: 0, caller: -1,
            elapsed: seconds(start), rows: raw[0].originalRowIndices, expected: expected[0], inputBytes: inputBytes)
        let owner = try await scope.preparation.prepare(raw[2], preprocessing: plan, budget: inputBudget)
        let secondStart = ContinuousClock.now
        let second = try await pool.predict(owner)
        let prepared = try sample(second, route: "crossPoolPreparation", variant: 2, caller: -1,
            elapsed: seconds(secondStart), rows: raw[2].originalRowIndices, expected: expected[2], inputBytes: inputBytes)
        guard retained.values == scope.samples.first(where: { $0.variant == 0 })!.values,
              prepared.values == scope.samples.first(where: { $0.variant == 2 })!.values else { throw Invalid.output }
        return [retained, prepared]
    }
    return scope.samples + additional
}

@main struct ProgramWorkflowProbe {
    static func main() async throws {
        let arguments = CommandLine.arguments
        guard arguments.count == 7, ["cpu", "neural"].contains(arguments[4]),
              let elementBytes = Int(arguments[5]), [2, 4].contains(elementBytes) else { throw Invalid.arguments }
        let rawURL = URL(fileURLWithPath: arguments[1]), fixtureURL = URL(fileURLWithPath: arguments[2])
        let modelURL = URL(fileURLWithPath: arguments[3]), outputURL = URL(fileURLWithPath: arguments[6])
        let rawData = try Data(contentsOf: rawURL), fixtureData = try Data(contentsOf: fixtureURL)
        let raw = try JSONDecoder().decode(Raw.self, from: rawData)
        let fixture = try JSONDecoder().decode(Fixture.self, from: fixtureData)
        guard let trainingIDs = raw.splits["train"], let testIDs = raw.splits["test"],
              testIDs.count == fixture.expected.count else { throw Invalid.fixture }
        let names = fixture.columns.indices.map { "feature_\($0)" }
        let columns = names.indices.map { column in raw.features.map { $0[column] } }
        let all = try PreparedNumericBatch(columnNames: names, columns: columns)
        let training = try all.selectingRows(trainingIDs), test = try all.selectingRows(testIDs)
        let fitStart = ContinuousClock.now
        let plan = try StandardPreprocessingPlan(training: training)
        var scaler = StandardScaler()
        try scaler.fit(training)
        let fitSeconds = seconds(fitStart)
        let scaled = try scaler.transform(test)
        var maximumScalingError = 0.0
        for column in names.indices {
            for row in testIDs.indices {
                maximumScalingError = max(maximumScalingError, abs(scaled[row, column]! - fixture.columns[column][row]))
            }
        }
        guard maximumScalingError < 1e-10 else { throw Invalid.scaling }
        let orders = [Array(testIDs.indices), Array(testIDs.indices.reversed()),
            testIDs.indices.map { ($0 / 2 * 7 + 3) % testIDs.count }]
        let rawVariants = try orders.map { try test.selectingRows($0) }
        let scaledVariants = try orders.map { try scaled.selectingRows($0) }
        let expected = orders.map { order in order.map { fixture.expected[$0] } }
        let compileStart = ContinuousClock.now
        let compiled = try await MLModel.compileModel(at: modelURL)
        let compileSeconds = seconds(compileStart)
        defer { try? FileManager.default.removeItem(at: compiled) }
        let poolBudget = try MemoryBudget(limit: 256 * 1_048_576)
        let inputBudget = try MemoryBudget(limit: 32 * 1_048_576)
        let workflowStart = ContinuousClock.now
        let samples = try await runScopes(compiled: compiled, policy: arguments[4], names: names,
            raw: rawVariants, scaled: scaledVariants, expected: expected, plan: plan,
            elementBytes: elementBytes, poolBudget: poolBudget, inputBudget: inputBudget)
        let workflowSeconds = seconds(workflowStart)
        let deadline = ContinuousClock.now.advanced(by: .seconds(5))
        while await inputBudget.reservedBytes != 0, ContinuousClock.now < deadline {
            try await Task.sleep(for: .milliseconds(1))
        }
        guard await poolBudget.reservedBytes == 0, await poolBudget.queuedCount == 0,
              await inputBudget.reservedBytes == 0, await inputBudget.queuedCount == 0 else { throw Invalid.admission }
        var usage = rusage()
        guard getrusage(RUSAGE_SELF, &usage) == 0 else { throw Invalid.output }
        let record: [String: Any] = ["policy": arguments[4], "transportElementBytes": elementBytes,
            "rows": testIDs.count, "columns": names.count,
            "rawSHA256": SHA256.hash(data: rawData).map { String(format: "%02x", $0) }.joined(),
            "fixtureSHA256": SHA256.hash(data: fixtureData).map { String(format: "%02x", $0) }.joined(),
            "maximumScalingError": maximumScalingError, "fitSeconds": fitSeconds,
            "compileSeconds": compileSeconds, "workflowSeconds": workflowSeconds,
            "poolPeakReservedBytes": await poolBudget.peak, "inputPeakReservedBytes": await inputBudget.peak,
            "finalPoolReservedBytes": await poolBudget.reservedBytes,
            "finalInputReservedBytes": await inputBudget.reservedBytes,
            "invalidInputRecoveryVerified": true, "crossPoolOwnerAndPreparationVerified": true,
            "concurrentCallers": 4, "poolSlots": 2, "processPeakRSSBytes": Int64(usage.ru_maxrss),
            "thermalState": ProcessInfo.processInfo.thermalState.rawValue,
            "timingScope": "Prediction latency includes queueing, slot input copy or packing, native prediction and owned output; validation excluded. Workflow includes model load, preparation, validation and cross-pool checks. Compilation may reuse caches.",
            "samples": try JSONSerialization.jsonObject(with: JSONEncoder().encode(samples))]
        try JSONSerialization.data(withJSONObject: record, options: [.prettyPrinted, .sortedKeys]).write(to: outputURL)
    }
}
