import Foundation
import SwiftPreprocessing
import SwiftCluster
import SwiftML

private enum ControlError: Error { case invalidFixture, missingState }

@main
struct LegacyWorkflowProbe {
    static func main() async throws {
        let data = try Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1]))
        guard let fixture = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let raw = fixture["rawRows"] as? [[Any]],
              let targets = fixture["sourceTargets"] as? [Double],
              let trainIDs = fixture["trainingSourceRows"] as? [Int],
              let queryIDs = fixture["querySourceRows"] as? [Int] else { throw ControlError.invalidFixture }
        let rows: [[Double]] = raw.map { row in row.map { ($0 as? NSNumber)?.doubleValue ?? .nan } }
        let train = trainIDs.map { rows[$0] }
        let query = queryIDs.map { rows[$0] }
        var imputer = Imputer(strategy: .mean)
        try imputer.fit(train)
        let imputedTrain = try imputer.transform(train)
        let imputedQuery = try imputer.transform(query)
        var scaler = StandardScaler()
        try scaler.fit(imputedTrain)
        let scaledTrain = try scaler.transform(imputedTrain)
        let scaledQuery = try scaler.transform(imputedQuery)
        let pca = try PCA(nComponents: 2, svdSolver: .full, device: .cpu)
        let trainScores = try await pca.fitTransform(scaledTrain)
        let queryScores = try await pca.transform(scaledQuery)
        let classifier = LogisticRegression(device: .cpu)
        try await classifier.fit(features: trainScores, targets: trainIDs.map { targets[$0] }, learningRate: 0.125, epochs: 64)
        let probabilities = try await classifier.predictProbability(features: queryScores)
        let predictions = try await classifier.predict(features: queryScores)
        guard let replacements = imputer.statistics, let means = scaler.mean, let deviations = scaler.std,
              let pcaMean = await pca.mean, let components = await pca.components,
              let variance = await pca.explainedVariance, let weights = await classifier.getWeights(),
              let bias = await classifier.getBias() else { throw ControlError.missingState }
        let result: [String: Any] = [
            "imputationStatistics": replacements, "scalingMean": means, "scalingStd": deviations,
            "scaledTraining": scaledTrain, "scaledQuery": scaledQuery,
            "pcaMean": pcaMean, "pcaComponents": components, "pcaVariance": variance,
            "trainingScores": trainScores, "queryScores": queryScores,
            "weights": weights, "bias": bias, "probabilities": probabilities, "predictions": predictions
        ]
        FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys]))
        FileHandle.standardOutput.write(Data([10]))
    }
}
