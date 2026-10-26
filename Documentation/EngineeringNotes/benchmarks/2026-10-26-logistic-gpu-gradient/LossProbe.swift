import Foundation
import MLX

@main struct LossProbe {
    static func main() {
        GPU.metallib = URL(fileURLWithPath: "/private/tmp/swiftsci-prepared-pca-20261026/baseline-standardized/derived/Build/Products/Release/mlx-swift_Cmlx.bundle/Contents/Resources/default.metallib")
        for target: Float in [0, 0.25, 1] {
            let targets = MLXArray([target, target, target])
            let logits = MLXArray([-2.0, 0.0, 2.0] as [Float])
            for smooth in [false, true] {
                let f = valueAndGrad({ (args: [MLXArray]) -> [MLXArray] in
                    [smooth ? mean(logAddExp(MLXArray(Float(0)), args[0]) - args[0] * targets)
                            : Losses.binaryCrossEntropy(logits: args[0], targets: targets)]
                }, argumentNumbers: [0])
                let (value, gradients) = f([logits])
                eval(value, gradients)
                print("target=\(target) smooth=\(smooth) loss=\(value[0].item(Float.self)) gradients=\(gradients[0].asArray(Float.self))")
            }
        }
        for primitive in ["maximum", "abs"] {
            let f = valueAndGrad({ (args: [MLXArray]) -> [MLXArray] in
                [primitive == "maximum" ? maximum(args[0], 0.0) : abs(args[0])]
            }, argumentNumbers: [0])
            let (_, gradients) = f([MLXArray(Float(0))])
            print("\(primitive) derivative at zero: \(gradients[0].item(Float.self))")
        }
    }
}
