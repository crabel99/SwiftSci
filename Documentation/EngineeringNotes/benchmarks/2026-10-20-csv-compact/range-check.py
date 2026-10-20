from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parent
original=R/'compact/Sources/SwiftDataFrame/IO/SystemsCSVParser.swift'
wrapper='''\nextension SystemsCSVParser {
    internal func testAutomaticRange(buffer: UnsafeBufferPointer<UInt8>, range: Range<Int>) -> CSVRecordIndex {
        scanIndex(buffer: buffer, range: range)
    }
}
'''
parser=R/'BoundaryParser.swift';parser.write_text(original.read_text()+wrapper)
sources=[R/'compact/Sources/SwiftDataFrame/IO/CSVRecordIndex.swift',parser,R/'RangeChecks.swift']
cmd=['xcrun','swiftc','-O','-whole-module-optimization','-swift-version','6','-target','arm64-apple-macos14.0','-parse-as-library',*[str(s) for s in sources],'-o',str(R/'RangeChecks')]
p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
p=subprocess.run([str(R/'RangeChecks')],capture_output=True,text=True);assert p.returncode==0,p.stderr
assert parser.read_text()==original.read_text()+wrapper
record=dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,test_only_wrapper=wrapper,original_parser_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),source_hashes={str(s):hashlib.sha256(s.read_bytes()).hexdigest() for s in sources})
(R/'range-checks.json').write_text(json.dumps(record,indent=2)+'\n');print(p.stdout)
