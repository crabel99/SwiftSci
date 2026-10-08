import Darwin
import Foundation

/// Opt-in debugger checkpoints. The profiling controller must resume this process.
/// No production caller invokes pressure relief or suspends for inspection.
enum MemoryResidencyProbe {
    private static var directory: String? { ProcessInfo.processInfo.environment["SWIFTSCI_RESIDENCY_DIR"] }

    static func snapshot() -> [String: Int] {
        var record = RetainedGPUBenchmark.memory()
        var statistics = malloc_statistics_t()
        malloc_zone_statistics(nil, &statistics)
        record["malloc_in_use_bytes"] = Int(statistics.size_in_use)
        record["malloc_allocated_bytes"] = Int(statistics.size_allocated)
        record["malloc_blocks_in_use"] = Int(statistics.blocks_in_use)
        var info = task_vm_info_data_t()
        var count = mach_msg_type_number_t(MemoryLayout<task_vm_info_data_t>.size / MemoryLayout<integer_t>.size)
        let status = withUnsafeMutablePointer(to: &info) { pointer in
            pointer.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                task_info(mach_task_self_, task_flavor_t(TASK_VM_INFO), $0, &count)
            }
        }
        precondition(status == KERN_SUCCESS)
        record["physical_footprint_bytes"] = Int(info.phys_footprint)
        record["pid"] = Int(getpid())
        return record
    }

}
