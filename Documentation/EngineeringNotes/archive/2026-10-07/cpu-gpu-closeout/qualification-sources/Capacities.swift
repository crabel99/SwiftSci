import Darwin
import Foundation
enum BudgetRegressionWorkflow {
    static func capacities(rows: Int, columns: Int, padded: Bool) -> [String: Int] {
        let page = Int(getpagesize())
        let payload = rows * columns * MemoryLayout<Float>.stride
        let allocation = (payload + page - 1) / page * page
        // Explicit capacities plus a fixed allowance, not a backend allocator guarantee.
        return [
            "raw_and_transformed": rows * columns * MemoryLayout<Double>.stride * 2,
            "packed_allocation": allocation,
            "logical_copy": !padded && payload % page != 0 ? allocation : 0,
            "outputs_and_readback": rows * 24,
            "scaler_scratch_and_metadata": 64 * 1024,
            "backend_allowance": 8 * 1024 * 1024,
        ]
    }

}
