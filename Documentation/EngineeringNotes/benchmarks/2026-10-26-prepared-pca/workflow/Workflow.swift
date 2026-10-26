import Foundation
import Darwin
import SwiftDataFrame
import SwiftPreprocessing
import SwiftCluster

func usage() -> (Double, Double, Int64) {
    var value = rusage()
    getrusage(RUSAGE_SELF, &value)
    let user = Double(value.ru_utime.tv_sec) + Double(value.ru_utime.tv_usec) / 1e6
    let system = Double(value.ru_stime.tv_sec) + Double(value.ru_stime.tv_usec) / 1e6
    return (user, system, Int64(value.ru_maxrss))
}

func currentRSS() -> UInt64 {
    var info = mach_task_basic_info_data_t()
    var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info_data_t>.size / MemoryLayout<natural_t>.size)
    let status = withUnsafeMutablePointer(to: &info) { pointer in
        pointer.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
            task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), $0, &count)
        }
    }
    precondition(status == KERN_SUCCESS)
    return info.resident_size
}

struct Result: Encodable {
    let mode: String
    let solver: String
    let elapsed: Double
    let userCPU: Double
    let systemCPU: Double
    let peakRSSBytes: Int64
    let retainedRSSBytes: UInt64
    let mean: [Double]
    let components: [[Double]]
    let variance: [Double]
    let ratios: [Double]
    let training: [Double]
    let query: [Double]
    let sourceRows: [Int]
}

@main struct Workflow {
    static func main() async throws {
        let file = URL(fileURLWithPath: CommandLine.arguments[1])
        let width = Int(CommandLine.arguments[2])!
        let k = Int(CommandLine.arguments[3])!
        let solver = CommandLine.arguments[4]
        let mode = CommandLine.arguments[5]
        let names = (0..<width).map { "x\($0)" }
        var options = CSVReadOptions()
        options.doubleStorage = .compact
        options.columnConversionMode = .serial
        options.columnTypeOverrides = Dictionary(uniqueKeysWithValues: names.map { ($0, ColumnDType.float64) })
        let before = usage(), start = DispatchTime.now().uptimeNanoseconds
        let frame = try await DataFrame(csv: file, options: options)
        let source = try frame.prepareNumericBatch(names)
        let split = source.rowCount * 4 / 5
        let trainIndices = Array(0..<split)
        let queryIndices = Array(split..<source.rowCount) + [split, split]
        let train = try source.selectingRows(trainIndices)
        let query = try source.selectingRows(queryIndices)
        var scaler = StandardScaler()
        let model = try PCA(nComponents: k, svdSolver: solver == "full" ? .full : .randomized, device: .cpu)
        let trainOutput: [Double], queryOutput: [Double], provenance: [Int]
        #if PREPARED_PCA
        if mode != "legacy" {
            try scaler.fit(train)
            let scaledTrain = try scaler.transform(consuming: consume train)
            let scaledQuery = try scaler.transform(consuming: consume query)
            if mode == "batch" {
                let training = try await model.fitTransform(scaledTrain)
                let projected = try await model.transform(scaledQuery)
                trainOutput = try training.matrix().values
                queryOutput = try projected.matrix().values
                provenance = projected.originalRowIndices
            } else {
                let order: NumericMatrixOrder = mode == "row" ? .rowMajor : .columnMajor
                let training = try await model.fitTransform(scaledTrain.matrix(order: order))
                let projected = try await model.transform(scaledQuery.matrix(order: order))
                trainOutput = (0..<training.rowCount).flatMap { row in (0..<k).map { training[row, $0] } }
                queryOutput = (0..<projected.rowCount).flatMap { row in (0..<k).map { projected[row, $0] } }
                provenance = projected.originalRowIndices
            }
        } else {
            let rows = train.rowValues()
            try scaler.fit(rows)
            trainOutput = try await model.fitTransform(scaler.transform(rows)).flatMap { $0 }
            queryOutput = try await model.transform(scaler.transform(query.rowValues())).flatMap { $0 }
            provenance = query.originalRowIndices
        }
        #else
        let rows = train.rowValues()
        try scaler.fit(rows)
        trainOutput = try await model.fitTransform(scaler.transform(rows)).flatMap { $0 }
        queryOutput = try await model.transform(scaler.transform(query.rowValues())).flatMap { $0 }
        provenance = query.originalRowIndices
        #endif
        let mean = await model.mean!, components = await model.components!
        let variance = await model.explainedVariance!, ratios = await model.explainedVarianceRatio!
        let elapsed = Double(DispatchTime.now().uptimeNanoseconds - start) / 1e9
        let after = usage()
        let result = Result(mode: mode, solver: solver, elapsed: elapsed,
                            userCPU: after.0 - before.0, systemCPU: after.1 - before.1,
                            peakRSSBytes: after.2, retainedRSSBytes: currentRSS(), mean: mean, components: components,
                            variance: variance, ratios: ratios, training: trainOutput,
                            query: queryOutput, sourceRows: provenance)
        FileHandle.standardOutput.write(try JSONEncoder().encode(result))
        FileHandle.standardOutput.write(Data([10]))
        withExtendedLifetime((source, model, result)) {}
    }
}
