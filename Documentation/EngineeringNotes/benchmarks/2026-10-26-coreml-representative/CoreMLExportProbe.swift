import CoreML
import Foundation
import SwiftML

@main struct CoreMLExportProbe {
    static func main() async throws {
        let directory = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let artifact = directory.appendingPathComponent("ThreeClasses.mlmodel")
        let layer = LayerWeights(W: [-1, 0, 1], b: [0, 0, 0], inDim: 1, outDim: 3)
        let data = CoreMLExporter.exportBinaryMLPClassifier(
            inputNames: ["x"], outputName: "probabilities", layers: [layer])
        try data.write(to: artifact)
        do {
            let compiled = try await MLModel.compileModel(at: artifact)
            print("COMPILED \(compiled.path)")
        } catch {
            FileHandle.standardError.write(Data("Multiclass export failed Core ML compilation: \(error)\n".utf8))
            exit(1)
        }
    }
}
