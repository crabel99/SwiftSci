import Foundation
import MLX
import SwiftML
import SwiftPreprocessing

@main struct MinimalProbe {
    static func main() async throws {
        GPU.metallib = URL(fileURLWithPath: "/private/tmp/swiftsci-prepared-pca-20261026/baseline-standardized/derived/Build/Products/Release/mlx-swift_Cmlx.bundle/Contents/Resources/default.metallib")
        let model = LogisticRegression(device: .gpu)
        try await model.fit(features: [[0.0]], targets: [0.0], learningRate: 0.25, epochs: 1)
        let bias = await model.getBias()!
        print("One zero feature, target 0, one update: GPU bias \(bias), analytical BCE bias -0.125")
        guard abs(bias - (-0.125)) < 1e-6 else { exit(1) }
    }
}
