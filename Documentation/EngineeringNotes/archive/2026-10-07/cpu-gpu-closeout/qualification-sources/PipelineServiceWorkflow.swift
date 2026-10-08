import CryptoKit
import Foundation
import MLX
import SwiftML
import SwiftPreprocessing

/// Continuous admitted requests through the public pipeline, with no idle periods
/// or cache clearing inside the measured window. Configuration stays immutable.
enum PipelineServiceWorkflow {
    struct Result: Sendable, Encodable {
        let id: Int
        let rows: Int
        let digest: [UInt8]
        let maxError: Double
        let queueMS: Double
        let serviceMS: Double

        enum CodingKeys: String, CodingKey { case id, rows, outputSHA256, maxError, queueMS, serviceMS }
        func encode(to encoder: any Encoder) throws {
            var container = encoder.container(keyedBy: CodingKeys.self)
            try container.encode(id, forKey: .id)
            try container.encode(rows, forKey: .rows)
            try container.encode(digest.map { String(format: "%02x", $0) }.joined(), forKey: .outputSHA256)
            try container.encode(maxError, forKey: .maxError)
            try container.encode(queueMS, forKey: .queueMS)
            try container.encode(serviceMS, forKey: .serviceMS)
        }
    }

    private static func sourceFingerprint(_ batch: PreparedNumericBatch) -> SHA256.Digest {
        var hash = SHA256()
        for column in batch.columns {
            column.values.withUnsafeBytes { hash.update(data: Data($0)) }
            hash.update(data: Data([column.validity == nil ? 0 : 1]))
            column.validity?.withUnsafeBytes { hash.update(data: Data($0)) }
            [column.nullCount].withUnsafeBytes { hash.update(data: Data($0)) }
        }
        return hash.finalize()
    }

    static func execute(id: Int, rows: Int, columns: Int, pipeline: RegressionPipeline,
                        owned: Bool, queueMS: Double, preprocessing: ImputedRegressionPreparation? = nil, verifySource: Bool = false) async throws -> Result {
        let start = ContinuousClock.now
        let raw = try preprocessing == nil
            ? RetainedRegressionWorkflow.fixture(rows: rows, seed: 937 + UInt64(id) * 97, columns: columns)
            : ImputedRegressionPreparation.fixture(rows: rows, columns: columns, request: id)
        let expected = preprocessing == nil ? RetainedRegressionWorkflow.truth(raw) : ImputedRegressionPreparation.truth(raw)
        let source = verifySource && !owned ? sourceFingerprint(raw) : nil
        let retained: PreparedNumericBatch?
        let prediction: [Double]
        if owned {
            retained = nil
            if let preprocessing {
                let clean = try preprocessing.transform(consume raw, owned: true)
                prediction = try await pipeline.predict(consuming: consume clean)
            } else {
                prediction = try await pipeline.predict(consuming: consume raw)
            }
        } else {
            retained = raw
            if let preprocessing {
                let clean = try preprocessing.transform(raw, owned: false)
                prediction = try await pipeline.predict(consuming: consume clean)
            } else {
                prediction = try await pipeline.predict(features: raw)
            }
        }
        precondition(prediction.count == rows && prediction.allSatisfy(\.isFinite))
        let error = zip(prediction, expected).reduce(0.0) { max($0, abs($1.0 - $1.1)) }
        precondition(error <= 1e-4)
        let hash = prediction.withUnsafeBytes { Array(SHA256.hash(data: Data($0))) }
        if let retained, let source { precondition(sourceFingerprint(retained) == source) }
        withExtendedLifetime((retained, expected, prediction)) {}
        return Result(id: id, rows: rows, digest: hash, maxError: error,
                      queueMS: queueMS, serviceMS: RetainedGPUBenchmark.milliseconds(start))
    }

    static func serve(pipeline: RegressionPipeline, rows: [Int], columns: Int,
                      requests: Int, owned: Bool, budget: MemoryBudget, preprocessing: ImputedRegressionPreparation? = nil, startID: Int = 0, verifySource: Bool = false) async throws -> [Result] {
        try await withThrowingTaskGroup(of: Result.self) { group in
            func submit(_ id: Int) {
                let count = rows[id % rows.count]
                group.addTask {
                    var capacities = BudgetRegressionWorkflow.capacities(rows: count, columns: columns, padded: false)
                    capacities["analytic_oracle"] = count * MemoryLayout<Double>.stride
                    let estimate = try MemoryEstimate(capacities: Array(capacities.values))
                    let queued = ContinuousClock.now
                    return try await budget.withReservation(estimate) {
                        try await execute(id: id, rows: count, columns: columns, pipeline: pipeline, owned: owned,
                                          queueMS: RetainedGPUBenchmark.milliseconds(queued), preprocessing: preprocessing, verifySource: verifySource)
                    }
                }
            }
            for id in startID..<(startID + min(2, requests)) { submit(id) }
            var next = startID + min(2, requests), results: [Result] = []
            for try await result in group {
                results.append(result)
                if next < startID + requests { submit(next); next += 1 }
            }
            return results.sorted { $0.id < $1.id }
        }
    }

    @MainActor
    static func run() async throws {
        precondition([7, 8, 9].contains(CommandLine.arguments.count))
        let verifySource = CommandLine.arguments.count == 9
        precondition(!verifySource || CommandLine.arguments[8] == "verify-source")
        let scalerName = CommandLine.arguments.count >= 8 ? CommandLine.arguments[7] : "standard"
        precondition(["standard", "minmax", "imputer-minmax"].contains(scalerName))
        let storage = CommandLine.arguments[2], schedule = CommandLine.arguments[3]
        let largest = Int(CommandLine.arguments[4])!, columns = Int(CommandLine.arguments[5])!
        let requests = Int(CommandLine.arguments[6])!
        precondition(["copy", "owned"].contains(storage) && ["fixed", "mixed"].contains(schedule))
        precondition((1...65536).contains(largest) && (1...65).contains(columns) && (2...32768).contains(requests))
        precondition(schedule != "mixed" || largest == 65536)
        let rows = schedule == "fixed" ? [largest] : [8191, 65535, 16383, 65536]
        let limit = 256 * 1024 * 1024
        Memory.cacheLimit = limit
        let scalers: [any PreprocessingTransformer]
        let preprocessing: ImputedRegressionPreparation?
        let weights: [Double], bias: Double
        if scalerName == "imputer-minmax" {
            let fitted = try await ImputedRegressionPreparation.fitted(columns: columns)
            preprocessing = fitted.0
            weights = fitted.1
            bias = fitted.2
            scalers = []
        } else if scalerName == "minmax" {
            let training = try RetainedRegressionWorkflow.fixture(rows: 512, seed: 41, columns: columns)
            var fitted = MinMaxScaler(range: (-2, 3))
            try fitted.fit(training)
            let model = LinearRegression(device: .cpu)
            try await model.fit(features: fitted.transform(training), targets: RetainedRegressionWorkflow.truth(training))
            let parameters = await model.getWeightsAndBias()
            scalers = [Pipeline(steps: [fitted])]
            preprocessing = nil
            weights = parameters.weights!
            bias = parameters.bias!
        } else {
            let fitted = try await RetainedRegressionWorkflow.fitted(columns: columns)
            scalers = [Pipeline(steps: [fitted.0])]
            weights = fitted.1
            bias = fitted.2
            preprocessing = nil
        }
        var pipeline: RegressionPipeline? = autoreleasepool {
            RegressionPipeline(transformers: scalers,
                estimator: LinearRegression(weights: weights, bias: bias, device: .gpu))
        }
        _ = try await execute(id: 0, rows: 64, columns: columns, pipeline: pipeline!, owned: storage == "owned", queueMS: 0, preprocessing: preprocessing)
        MLX.Stream.gpu.synchronize()
        Memory.clearCache()
        let before = MemoryResidencyProbe.snapshot()
        let budget = try MemoryBudget(limit: limit)
        let start = ContinuousClock.now
        var results: [Result] = [], windows: [[String: Int]] = []
        let windowCount = preprocessing == nil ? 1 : min(4, requests)
        for window in 0..<windowCount {
            let first = window * requests / windowCount
            let count = (window + 1) * requests / windowCount - first
            results += try await serve(pipeline: pipeline!, rows: rows, columns: columns,
                requests: count, owned: storage == "owned", budget: budget,
                preprocessing: preprocessing, startID: first, verifySource: verifySource)
            guard preprocessing != nil else { continue }
            MLX.Stream.gpu.synchronize()
            var state = MemoryResidencyProbe.snapshot()
            state["completed_requests"] = results.count
            state["reserved_bytes"] = await budget.reservedBytes
            state["queued_count"] = await budget.queuedCount
            precondition(state["reserved_bytes"] == 0 && state["queued_count"] == 0)
            precondition(state["mlx_active_bytes"] == before["mlx_active_bytes"])
            windows.append(state)
        }
        MLX.Stream.gpu.synchronize()
        let elapsed = RetainedGPUBenchmark.milliseconds(start)
        let measured = MemoryResidencyProbe.snapshot()
        let remaining = await budget.reservedBytes, queued = await budget.queuedCount
        precondition(remaining == 0 && queued == 0)
        precondition(measured["mlx_active_bytes"] == before["mlx_active_bytes"])
        precondition(measured["rss_bytes"]! < 2 * 1024 * 1024 * 1024)
        precondition(measured["physical_footprint_bytes"]! < 2 * 1024 * 1024 * 1024)
        pipeline = nil
        MLX.Stream.gpu.synchronize()
        Memory.clearCache()
        let closed = MemoryResidencyProbe.snapshot()
        precondition(closed["mlx_active_bytes"] == 0 && closed["mlx_cache_bytes"] == 0)
        let capacities = rows.map { count in
            var c = BudgetRegressionWorkflow.capacities(rows: count, columns: columns, padded: false)
            c["analytic_oracle"] = count * MemoryLayout<Double>.stride
            return c
        }
        let parameterHash = (weights + [bias]).withUnsafeBytes {
            SHA256.hash(data: Data($0)).map { String(format: "%02x", $0) }.joined()
        }
        let requestJSON = try JSONSerialization.jsonObject(with: JSONEncoder().encode(results))
        try MemoryReuseWorkflow.emit(["mode": "pipeline-service", "scaler": scalerName, "storage": storage, "schedule": schedule,
            "row_schedule": rows, "parameters_sha256": parameterHash, "columns": columns, "request_count": requests, "max_concurrent": 2,
            "limit_bytes": limit, "cache_limit_bytes": Memory.cacheLimit, "estimate_capacities": capacities,
            "peak_reserved_bytes": await budget.peak, "reserved_after": remaining, "queued_after": queued,
            "elapsed_ms": elapsed, "requests_per_second": Double(requests) * 1000 / elapsed,
            "requests": requestJSON, "source_verification_enabled": verifySource,
            "source_checks": verifySource && storage == "copy" ? requests : 0, "windows": windows, "before": before, "measured": measured, "closed": closed])
    }
}
