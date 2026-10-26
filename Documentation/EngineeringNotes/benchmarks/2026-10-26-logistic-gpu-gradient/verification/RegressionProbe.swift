import Foundation
import MLX
import SwiftML
import SwiftPreprocessing

@main struct BaselineLogisticProbe {
    static func main() async throws {
        GPU.metallib = URL(fileURLWithPath: CommandLine.arguments[1])
        let rows: [[Double]] = (0..<1_000).map { index -> [Double] in
            let first = Double(index % 17) - 8.0
            let second = Double((index * 7) % 19) - 9.0
            return [first / 4.0, second / 5.0]
        }
        let targets: [Double] = rows.map { row -> Double in
            row[0] * 0.8 - row[1] * 0.35 > 0.15 ? 1.0 : 0.0
        }
        var cases = [[String: Any]]()
        let devices: [ExecutionDevice] = [.cpu, .gpu, .auto, .ane]
        for device in devices {
            for epochs in [0, 1, 4] {
                let model = LogisticRegression(device: device)
                try await model.fit(features: rows, targets: targets, learningRate: 0.05, epochs: epochs)
                let parameters = await model.getWeightsAndBias()
                let probabilities = try await model.predictProbability(features: Array(rows.prefix(16)))
                cases.append(["requested": String(describing: device), "epochs": epochs,
                              "weights": parameters.weights!, "bias": parameters.bias!,
                              "positive": probabilities.map { $0[1] }])
            }
        }
        let supplied = LogisticRegression(weights: [1], bias: 0, device: .cpu)
        let nan = try await supplied.predictProbability(features: [[.nan]])
        let data = try JSONSerialization.data(withJSONObject: ["cases": cases, "legacy_nan": nan], options: [.prettyPrinted, .sortedKeys])
        print(String(decoding: data, as: UTF8.self))
    }
}
