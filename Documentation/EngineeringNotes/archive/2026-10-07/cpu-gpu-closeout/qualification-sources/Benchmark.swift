import Cmlx
import Foundation
import Darwin
import CryptoKit
import Metal
import MLX
import SwiftPreprocessing

@main
struct RetainedGPUBenchmark {
    static func estimate(_ bytes: Int) throws -> MemoryEstimate { try MemoryEstimate(capacities: [bytes]) }
    static func milliseconds(_ start: ContinuousClock.Instant) -> Double {
        let d = start.duration(to: .now).components
        return Double(d.seconds) * 1000 + Double(d.attoseconds) / 1e15
    }
    static func memory() -> [String: Int] {
        var info = mach_task_basic_info()
        var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size / MemoryLayout<integer_t>.size)
        let status = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), $0, &count)
            }
        }
        precondition(status == KERN_SUCCESS)
        var usage = rusage()
        precondition(getrusage(RUSAGE_SELF, &usage) == 0)
        return ["rss_bytes": Int(info.resident_size), "peak_rss_bytes": Int(usage.ru_maxrss),
                "mlx_active_bytes": Memory.activeMemory, "mlx_cache_bytes": Memory.cacheMemory]
    }
    @MainActor static func main() async throws {
        precondition(CommandLine.arguments[1] == "pipeline-service")
        try await PipelineServiceWorkflow.run()
    }
}
