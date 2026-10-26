import Foundation
import SwiftDataFrame
import SwiftPreprocessing
import SwiftCluster
import SwiftML

private enum WorkflowError: Error { case missingFittedState, invariant(String) }

@main
struct ScientificWorkflow {
    static func main() async throws {
        // Replace this fixture with your named feature columns and target column.
        let signal: [Double] = [-4, -3, -2, -1, 1, 2, 3, 4, -2.5, 2.5, 0.5, -0.5]
        let companion: [Double] = [-7, -5, .nan, -1, 2, 3, 6, 8, -4.5, 5, .nan, 1]
        let constant = [Double](repeating: 7, count: signal.count)
        let targets: [Double] = [0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0]
        var source = try PreparedNumericBatch(
            columnNames: ["signal", "companion", "constant", "class"],
            columns: [signal, companion, constant, targets])
        try source.updateColumn(at: 1, rows: [2], values: [nil])
        let originalBits = (0..<source.columnCount).map { column in
            source.columnValues(at: column).map { $0?.bitPattern }
        }

        // Select features and targets together before fitting anything.
        let supervised = try PreparedSupervisedBatch(source, targetColumn: "class")
        let trainingIDs = Array(0..<8)
        let queryIDs = [10, 8, 10, 9, 11]
        let training = try supervised.selectingRows(trainingIDs)
        let query = try supervised.selectingRows(queryIDs)

        var imputer = Imputer(strategy: .mean)
        try imputer.fit(training.features)
        let imputedTraining = try imputer.transform(training.features)
        let imputedQuery = try imputer.transform(query.features)
        var scaler = StandardScaler()
        try scaler.fit(imputedTraining)
        let scaledTraining = try scaler.transform(imputedTraining)
        let scaledQuery = try scaler.transform(imputedQuery)

        // Fit PCA and the classifier on training rows. Query rows only transform/predict.
        let pca = try PCA(nComponents: 2, svdSolver: .full, device: .cpu)
        let trainingScores = try await pca.fitTransform(scaledTraining)
        let queryScores = try await pca.transform(scaledQuery)
        let classifier = LogisticRegression(device: .cpu)
        try await classifier.fit(features: trainingScores, targets: training.targets,
                                 learningRate: 0.125, epochs: 64)
        let probabilities = try await classifier.predictProbability(features: queryScores)
        let predictions = try await classifier.predict(features: queryScores)

        guard let replacements = imputer.statistics, let means = scaler.mean, let deviations = scaler.std,
              let pcaMean = await pca.mean, let components = await pca.components,
              let variance = await pca.explainedVariance,
              let weights = await classifier.getWeights(), let bias = await classifier.getBias() else {
            throw WorkflowError.missingFittedState
        }
        let currentBits = (0..<source.columnCount).map { column in
            source.columnValues(at: column).map { $0?.bitPattern }
        }
        guard originalBits == currentBits, queryScores.originalRowIndices == queryIDs,
              trainingScores.originalRowIndices == trainingIDs,
              probabilities.count == queryIDs.count, predictions.count == queryIDs.count else {
            throw WorkflowError.invariant("Source snapshot or output row alignment changed")
        }

        // Prediction arrays have no row IDs. Associate them using the score batch.
        let outputRows: [[String: Any]] = queryIDs.indices.map { row in
            ["sourceRow": queryScores.originalRowIndices[row], "target": query.targets[row],
             "prediction": predictions[row], "probabilityClass1": probabilities[row][1]]
        }
        let rawRows: [[Any]] = signal.indices.map { row in
            let value: Any = companion[row].isNaN ? NSNull() : companion[row]
            return [signal[row], value, constant[row]]
        }
        let result: [String: Any] = [
            "schemaVersion": 1, "trainingSourceRows": trainingIDs, "querySourceRows": queryIDs,
            "featureNames": training.features.columnNames, "scoreNames": queryScores.columnNames,
            "rawRows": rawRows, "sourceTargets": targets, "trainingTargets": training.targets,
            "queryTargets": query.targets, "imputationStatistics": replacements,
            "scalingMean": means, "scalingStd": deviations,
            "scaledTraining": try scaledTraining.matrix(missing: .reject).rowValues(),
            "scaledQuery": try scaledQuery.matrix(missing: .reject).rowValues(),
            "pcaMean": pcaMean, "pcaComponents": components, "pcaVariance": variance,
            "trainingScores": try trainingScores.matrix(missing: .reject).rowValues(),
            "queryScores": try queryScores.matrix(missing: .reject).rowValues(),
            "weights": weights, "bias": bias, "probabilities": probabilities,
            "predictions": predictions, "outputRows": outputRows,
            "learningRate": 0.125, "epochs": 64, "sourceSnapshotPreserved": originalBits == currentBits
        ]
        let data = try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys])
        FileHandle.standardOutput.write(data)
        FileHandle.standardOutput.write(Data([10]))
    }
}
