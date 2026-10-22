from pathlib import Path
import json,hashlib,subprocess,select,sys
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-wide-profile-20261022');S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');D=P/'build/production';rec=json.loads((D/'build.json').read_text())
assert all(hashlib.sha256((S/p).read_bytes()).hexdigest()==sha for p,sha in rec['sources'].items())
s=(P/'ResourceProbe.swift').read_text().split('@MainActor @main struct ReferenceProbe')[0]
s+='''@inline(never) func readRows(_ url: URL, _ options: CSVReadOptions) async throws -> Int {
    let frame = try await DataFrame(csv: url, options: options)
    return frame.shape.rows
}
@MainActor @main struct LoopProfile {
    static func main() async throws {
        let args = CommandLine.arguments
        let input = try JSONDecoder().decode(Input.self, from: Data(contentsOf: URL(fileURLWithPath: args[1])))
        var options = CSVReadOptions()
        options.nullValues = Set(input.null_tokens)
        options.delimiter = Character(input.delimiter)
        options.columnConversionMode = .serial
        let mapping: [String: ColumnDType] = ["String":.utf8,"Double":.float64,"Int64":.int64,"Date":.date32,"Bool":.boolean]
        options.columnTypeOverrides = Dictionary(uniqueKeysWithValues: zip(input.names,input.types).map { ($0.0,mapping[$0.1]!) })
        let url = URL(fileURLWithPath: input.path)
        do {
            let frame = try await DataFrame(csv: url, options: options)
            precondition(validate(frame,input: input,mode: "known")["passed"] as? Bool == true)
        }
        FileHandle.standardOutput.write(Data("ready\\n".utf8))
        _ = readLine()
        var rows = 0
        for _ in 0..<Int(args[2])! { rows += try await readRows(url,options) }
        print(rows)
    }
}
''';source=R/'LoopProfile.swift';source.write_text(s)
cmd=[str(source) if a.endswith('/ResourceProbe.swift') else a for a in rec['commands'][1]];binary=R/'LoopProfile';cmd[cmd.index('-o')+1]=str(binary)
p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
receipt=dict(command=cmd,harness_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),module_receipt_sha256=hashlib.sha256((D/'build.json').read_bytes()).hexdigest());(R/'profile-build.json').write_text(json.dumps(receipt,indent=2)+'\n')
sys.path.insert(0,str(S/'Benchmarks/Tools'));from execution_policy import worker_environment,PRODUCTION_MODE
for case,contract,reps in [('wide','/private/tmp/swiftsci-csv-cpu-profile-20261021/inputs/Aotizhongxin.json',1000),('energy','/private/tmp/swiftsci-csv-cpu-profile-20261021/inputs/energy.json',30)]:
 proc=None
 try:
  with (R/(case+'.stderr')).open('w') as err:
   proc=subprocess.Popen([str(binary),contract,str(reps)],env=worker_environment(PRODUCTION_MODE),stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=err,text=True)
   assert select.select([proc.stdout],[],[],30)[0] and proc.stdout.readline().strip()=='ready'
   proc.stdin.write('go\n');proc.stdin.flush()
   cmd=['sample',str(proc.pid),'3','1','-file',str(R/(case+'.sample.txt'))]
   p=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
   assert p.returncode==0,p.stderr
   out,_=proc.communicate(timeout=60);assert proc.returncode==0
   expected=json.loads(Path(contract).read_text())['rows']*reps;assert out.strip()==str(expected),(out,expected)
   (R/(case+'-profile.json')).write_text(json.dumps(dict(command=cmd,pid=proc.pid,stdout=p.stdout,stderr=p.stderr,row_total=expected,driver_stdout=out,scope='Diagnostic samples only. One full independent native-output validation before ready; repeated reads release each frame through a separate async function. Serial column conversion; no timing acceptance claim.'),indent=2)+'\n');print(case,'profile completed',flush=True)
 finally:
  if proc is not None and proc.poll() is None:
   proc.kill();proc.communicate(timeout=10)
