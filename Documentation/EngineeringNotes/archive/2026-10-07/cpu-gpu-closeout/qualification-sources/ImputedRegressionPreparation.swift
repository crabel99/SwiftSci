import Foundation
import SwiftML
import SwiftPreprocessing

/// Training-only missing-value preprocessing before the finite regression boundary.
struct ImputedRegressionPreparation: Sendable {
    let pipeline: Pipeline

    static func fixture(rows: Int, columns: Int, request: Int) throws -> PreparedNumericBatch {
        var batch = try RetainedRegressionWorkflow.fixture(rows: rows, seed: 937 + UInt64(request) * 97, columns: columns)
        for c in 0..<columns {
            // Shift held-out observations beyond the training range. Refitting on
            // a request would change predictions and fail the independent oracle.
            batch.columns[c].values.withUnsafeMutableBufferPointer { values in
                for r in values.indices {
                    values[r] += 4
                    if c % 3 != 0 && (r + request) % 97 == 0 { values[r] = .nan }
                }
            }
            if c % 3 != 0 {
                let missing = (0..<rows).filter { ($0 + request) % 101 == 0 }
                try batch.updateColumn(at: c, rows: missing, values: [Double?](repeating: nil, count: missing.count))
            }
        }
        return batch
    }

    static func truth(_ batch: PreparedNumericBatch) -> [Double] {
        (0..<batch.rowCount).map { row in
            var y = 3.0
            for c in 0..<batch.columnCount {
                let x = batch[row,c] ?? .nan
                y += (x.isNaN ? 0 : x) * Double(c % 7 - 3) / 16
            }
            return y
        }
    }

    static func fitted(columns: Int) async throws -> (Self, [Double], Double) {
        let half = try RetainedRegressionWorkflow.fixture(rows: 256, seed: 41, columns: columns)
        var training = try PreparedNumericBatch(columnNames: half.columnNames, columns: half.columns.enumerated().map { c, column in
            let positive = column.values.enumerated().map { r, x in c % 3 != 0 && r % 31 == 0 ? Double.nan : x }
            return positive + positive.map { -$0 }
        })
        for c in 0..<columns where c % 3 != 0 {
            try training.updateColumn(at: c, rows: [0,256], values: [nil,nil])
        }
        // Paired binary fractions make each training mean exactly zero, giving
        // the oracle a known replacement independent of Imputer's implementation.
        var imputer = Imputer()
        try imputer.fit(training)
        precondition(imputer.statistics! == Array(repeating: 0, count: columns))
        var preprocessing = Pipeline(steps: [Imputer(), MinMaxScaler(range: (-2,3))])
        try preprocessing.fit(training)
        let targets = truth(training)
        let clean = try preprocessing.transform(consuming: consume training)
        let estimator = LinearRegression(device: .cpu)
        let regression = RegressionPipeline(estimator: estimator)
        try await regression.fit(consuming: consume clean, targets: targets)
        let parameters = await estimator.getWeightsAndBias()
        return (Self(pipeline: preprocessing), parameters.weights!, parameters.bias!)
    }

    func transform(_ raw: consuming PreparedNumericBatch, owned: Bool) throws -> PreparedNumericBatch {
        let addresses = raw.columns.map { $0.values.withUnsafeBufferPointer { UInt(bitPattern: $0.baseAddress!) } }
        let output: PreparedNumericBatch
        if owned { output = try pipeline.transform(consuming: consume raw) }
        else { output = try pipeline.transform(raw) }
        if owned {
            precondition(output.columns.enumerated().allSatisfy { c, column in
                column.values.withUnsafeBufferPointer { UInt(bitPattern: $0.baseAddress!) == addresses[c] }
            })
        }
        return output
    }
}
