// Design only; not compiled with production sources.
struct CSVASCIIPrefixStringDecoder: CSVValueDecoder, Sendable {
    private let nullValues: Set<String>
    private let lowStarts: UInt64
    private let highStarts: UInt64
    init?(nullValues: Set<String>, selectedRowCount: Int) {
        fatalError("not implemented: bounded token-plus-byte ASCII scan")
    }
    func decode(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> CSVDecodedValue<String> {
        fatalError("not implemented: parsed negative-prefix rejection, then original Set equality")
    }
}
// CSVColumnPlan.conversion(type:selectedRowCount:) selects one existing concrete
// decoder or CSVASCIIPrefixStringDecoder once per attempt. Readers do not choose it.
