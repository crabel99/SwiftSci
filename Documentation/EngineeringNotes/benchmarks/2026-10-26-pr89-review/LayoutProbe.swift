import Foundation

@main struct LayoutProbe {
    static func main() throws {
        let valid = try PCAFullSVDLayout(rows: 4, columns: 3)
        guard valid.rows == 4, valid.columns == 3, valid.rank == 3,
              valid.leftCount == 12, valid.rightCount == 9, valid.integerWorkspaceCount == 24 else {
            fatalError("Small economy-SVD layout changed")
        }
        let large = try PCAFullSVDLayout(rows: 24_000, columns: 24_000)
        guard large.leftCount == 576_000_000, large.rightCount == 576_000_000 else {
            fatalError("Backend-supported layout changed")
        }
        for (rows, columns) in [(Int(Int32.max), Int(Int32.max)), (Int(Int32.max) + 1, 2), (2, 0)] {
            do {
                _ = try PCAFullSVDLayout(rows: rows, columns: columns)
                fputs("FAIL: unsupported SVD workspace accepted for \(rows)x\(columns)\n", stderr)
                exit(1)
            } catch is ClusterError {
                print("Rejected unsupported workspace \(rows)x\(columns)")
            }
        }
        print("PASS: supported layouts preserved; dimension and buffer byte overflow rejected without allocation")
    }
}
