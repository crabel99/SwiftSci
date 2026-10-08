import Foundation
import Darwin
import CryptoKit
import MLX
import SwiftML
import SwiftPreprocessing

enum RetainedRegressionWorkflow {
    static func fixture(rows: Int, seed: UInt64, columns width: Int = 64) throws -> PreparedNumericBatch {
        let columns: [[Double]] = (0..<width).map { column in
            var state = seed &+ UInt64(column + 1) &* 104729
            return (0..<rows).map { _ in
                state = state &* 6364136223846793005 &+ 1442695040888963407
                return Double(Int((state >> 32) & 4095) - 2048) / 1024
            }
        }
        return try PreparedNumericBatch(columnNames: (0..<width).map { "x\($0)" }, columns: columns)
    }
    static func truth(_ batch: PreparedNumericBatch) -> [Double] {
        (0..<batch.rowCount).map { row in
            var value = 3.0
            for c in 0..<batch.columnCount { value += batch[row,c]! * Double(c % 7 - 3) / 16 }
            return value
        }
    }
    static func fitted(columns: Int = 64) async throws -> (StandardScaler, [Double], Double) {
        let training = try fixture(rows: 512, seed: 41, columns: columns)
        var scaler = StandardScaler()
        try scaler.fit(training)
        let model = LinearRegression(device: .cpu)
        try await model.fit(features: scaler.transform(training), targets: truth(training))
        let parameters = await model.getWeightsAndBias()
        return (scaler, parameters.weights!, parameters.bias!)
    }
}
