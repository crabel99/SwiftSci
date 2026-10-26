import Foundation
import MLX
import SwiftDataFrame
import SwiftML
import SwiftPreprocessing

private struct Fixture: Decodable {
    struct Splits: Decodable { let train: [Int]; let validation: [Int]; let test: [Int] }
    struct Training: Decodable { let learning_rate: Double; let epochs: Int }
    let feature_names: [String]
    let features: [[Double]]
    let targets: [Double]
    let splits: Splits
    let training: Training
}

private struct Result: Encodable {
    let weights: [Double]
    let bias: Double
    let probabilities: [[[Double]]]
    let labels: [[Int]]
    let row_positions: [[Int]]
}

@main struct PublicClassificationProbe {
    static func main() async throws {
        let args = CommandLine.arguments
        GPU.metallib = URL(fileURLWithPath: args[2])
        let fixture = try JSONDecoder().decode(Fixture.self, from: Data(contentsOf: URL(fileURLWithPath: args[1])))
        let indices = [fixture.splits.train, fixture.splits.validation, fixture.splits.test]
        let model = LogisticRegression(device: .gpu)
        var probabilities = [[[Double]]]()
        var labels = [[Int]]()
        var positions = indices
        let targets = indices.map { rows in rows.map { fixture.targets[$0] } }
        var scaler = StandardScaler()
        #if PREPARED
        if args[3] == "prepared" {
            var columns = fixture.feature_names.indices.map { column in fixture.features.map { $0[column] } }
            columns.append(fixture.targets)
            let source = try PreparedNumericBatch(columnNames: fixture.feature_names + ["target"], columns: columns)
            let supervised = try PreparedSupervisedBatch(source, targetColumn: "target")
            let selected = try indices.map { try supervised.selectingRows($0) }
            try scaler.fit(selected[0].features)
            let scaled = try selected.map { try scaler.transform($0.features) }
            try await model.fit(features: scaled[0], targets: selected[0].targets,
                                learningRate: Float(fixture.training.learning_rate), epochs: fixture.training.epochs)
            let erased: any ClassifierEstimator = model
            for batch in scaled {
                probabilities.append(try await erased.predictProbability(features: batch))
                labels.append(try await erased.predict(features: batch))
            }
            positions = scaled.map { $0.originalRowIndices }
        } else {
            let rows = indices.map { rows in rows.map { fixture.features[$0] } }
            try scaler.fit(rows[0])
            let scaled = try rows.map { try scaler.transform($0) }
            try await model.fit(features: scaled[0], targets: targets[0],
                                learningRate: Float(fixture.training.learning_rate), epochs: fixture.training.epochs)
            for matrix in scaled {
                probabilities.append(try await model.predictProbability(features: matrix))
                labels.append(try await model.predict(features: matrix))
            }
        }
        #else
        let rows = indices.map { rows in rows.map { fixture.features[$0] } }
        try scaler.fit(rows[0])
        let scaled = try rows.map { try scaler.transform($0) }
        try await model.fit(features: scaled[0], targets: targets[0],
                            learningRate: Float(fixture.training.learning_rate), epochs: fixture.training.epochs)
        for matrix in scaled {
            probabilities.append(try await model.predictProbability(features: matrix))
            labels.append(try await model.predict(features: matrix))
        }
        #endif
        guard await model.resolvedDevice == .gpu else { fatalError("Expected GPU training") }
        let parameters = await model.getWeightsAndBias()
        let result = Result(weights: parameters.weights!, bias: parameters.bias!,
                            probabilities: probabilities, labels: labels, row_positions: positions)
        print(String(decoding: try JSONEncoder().encode(result), as: UTF8.self))
    }
}
