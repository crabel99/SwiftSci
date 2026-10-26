import Foundation
import SwiftCluster
import SwiftDataFrame

@main struct BaselineMeanProbe {
    static func main() async throws {
        for solver in [SVDSolver.full, .randomized] {
            let model = try PCA(nComponents: 1, svdSolver: solver, device: .cpu)
            let input: [[Double]] = [[1, 2], [3, 4], [-1, 1]]
            let expected = try await model.fitTransform(input)
            let before = await model.mean
            let large = Double.greatestFiniteMagnitude
            do {
                try await model.fit([[large, 0], [large, 0]])
                fatalError("Finite mean overflow was accepted")
            } catch let error as ClusterError {
                guard case .invalidParameter = error else { throw error }
            }
            let after = await model.mean
            let actual = try await model.transform(input)
            guard before == after, actual == expected else { fatalError("Rejected fit changed the model") }
        }
        print("PASS: submitted PCA rejects finite mean overflow and preserves its successful fit")
    }
}
