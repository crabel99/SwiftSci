import Foundation
import SwiftDataFrame
import SwiftStats

func emit(_ name: String, _ fields: [String: Any]) throws {
    var record = fields
    record["probe"] = name
    let data = try JSONSerialization.data(withJSONObject: record, options: [.sortedKeys])
    print(String(decoding: data, as: UTF8.self))
}
func npy<T>(_ values: [T], descriptor: String, shape: String, fortran: Bool) -> Data {
    var data = Data([0x93,0x4e,0x55,0x4d,0x50,0x59,1,0])
    let dictionary = "{'descr': '\(descriptor)', 'fortran_order': \(fortran ? "True" : "False"), 'shape': \(shape), }"
    let paddedCount = ((10 + dictionary.utf8.count + 1 + 63) / 64) * 64 - 10
    let header = dictionary + String(repeating: " ", count: paddedCount - dictionary.utf8.count - 1) + "\n"
    let n = UInt16(header.utf8.count)
    data.append(UInt8(n & 255)); data.append(UInt8(n >> 8))
    data.append(contentsOf: header.utf8)
    values.withUnsafeBytes { data.append(contentsOf: $0) }
    return data
}

let x: [Double?] = [1,nil,3,4]
let y: [Double?] = [2,4,nil,8]
let df = try DataFrame(columns: [TypedColumn(name:"x", values:x), TypedColumn(name:"y", values:y)])
let correlation = try df.correlationMatrix()
let actualCorrelation = correlation[column:"y", as:Double.self]![0]!
let paired = zip(x,y).compactMap { a,b -> (Double,Double)? in guard let a,let b else {return nil}; return (a,b) }
let expectedCorrelation = try Stats.pearsonCorrelation(paired.map{$0.0}, paired.map{$0.1})
try emit("correlation_row_alignment", ["input_x":["1","nil","3","4"],"input_y":["2","4","nil","8"], "joint_rows":[0,3], "expected_pairwise":expectedCorrelation,"actual":actualCorrelation,"matches_pairwise":abs(expectedCorrelation-actualCorrelation)<1e-12])

let fortranBytes = npy([1.0,4.0,2.0,5.0,3.0,6.0], descriptor:"<f8", shape:"(2, 3)", fortran:true)
let fortran = try NPYReader.read(data:fortranBytes)
let fortranDF = try fortran.toDataFrame()
let actualRows = try fortranDF.toFeatureMatrix(fortranDF.columnNames)
let expectedRows:[[Double]] = [[1,2,3],[4,5,6]]
try emit("npy_fortran_order", ["shape":fortran.shape,"descriptor":fortran.descr,"fortran_order":fortran.fortranOrder,"payload":[1,4,2,5,3,6],"expected_rows":expectedRows,"actual_rows":actualRows,"matches":actualRows==expectedRows])

let ints:[Int64] = [9007199254740992,9007199254740993,9007199254740994]
let intArray = try NPYReader.read(data:npy(ints,descriptor:"<i8",shape:"(3,)",fortran:false))
let intDF = try intArray.toDataFrame()
let actualInts = intDF[column:"value",as:Double.self]!.values.map { Int64($0!) }
try emit("npy_int64_precision", ["descriptor":intArray.descr,"input":ints.map(String.init),"raw_to_int64":intArray.toInt64s().map(String.init),"dataframe_dtype":intDF[column:"value"]!.dtype.description,"dataframe_as_integer_strings":actualInts.map(String.init),"matches_exact":actualInts==ints])

for column:any AnyColumn in [TypedColumn<Float>(name:"v",values:[1,2]),TypedColumn<Int32>(name:"v",values:[1,2]),TypedColumn<Int>(name:"v",values:[1,2])] {
    let frame = try DataFrame(columns:[column])
    do { let m = try frame.toFeatureMatrix(["v"]); try emit("matrix_numeric_type",["swift_type":String(describing:type(of:column)),"accepted":true,"matrix":m]) }
    catch { try emit("matrix_numeric_type",["swift_type":String(describing:type(of:column)),"accepted":false,"error":String(describing:error)]) }
}
