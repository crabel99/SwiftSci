from pathlib import Path
import json,subprocess,hashlib,os,select,signal
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-wide-profile-20261022')
s=(R/'ResourceProbe.swift').read_text();pos=s.index('@MainActor @main struct ReferenceProbe');s=s[:pos]+'''@MainActor @main struct AllocationProbe {
    static func main() async throws {
        let input = try JSONDecoder().decode(Input.self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1])))
        var options = CSVReadOptions()
        options.nullValues = Set(input.null_tokens)
        options.delimiter = Character(input.delimiter)
        options.columnConversionMode = .serial
        let mapping: [String: ColumnDType] = ["String":.utf8,"Double":.float64,"Int64":.int64,"Date":.date32,"Bool":.boolean]
        options.columnTypeOverrides = Dictionary(uniqueKeysWithValues: zip(input.names, input.types).map { ($0.0,mapping[$0.1]!) })
        var frame: DataFrame? = try await DataFrame(csv: URL(fileURLWithPath: input.path), options: options)
        let checks = validate(frame!, input: input, mode: "known")
        precondition(checks["passed"] as? Bool == true)
        frame = nil
        FileHandle.standardOutput.write(Data("ready\\n".utf8))
        _ = readLine()
    }
}
''';(R/'AllocationProbe.swift').write_text(s)
for label,d in [('parent',P/'build/production'),('consume',R/'build/consume'),('header',R/'build/header')]:
 rec=json.loads((d/'build.json').read_text());cmd=[str(R/'AllocationProbe.swift') if x.endswith('/ResourceProbe.swift') else x for x in rec['commands'][1]];binary=R/('AllocationProbe-'+label);cmd[cmd.index('-o')+1]=str(binary)
 proc=subprocess.run(cmd,capture_output=True,text=True);assert proc.returncode==0,proc.stderr
 (R/('allocation-'+label+'-build.json')).write_text(json.dumps(dict(command=cmd,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),harness_sha256=hashlib.sha256((R/'AllocationProbe.swift').read_bytes()).hexdigest(),module_receipt_sha256=hashlib.sha256((d/'build.json').read_bytes()).hexdigest()),indent=2)+'\n')
 env=dict(os.environ,MallocStackLogging='1',MallocStackLoggingNoCompact='1')
 with (R/('allocation-'+label+'.stderr')).open('w') as err:
  proc=subprocess.Popen([str(binary),'/private/tmp/swiftsci-csv-cpu-profile-20261021/inputs/Aotizhongxin.json'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,env=env,text=True)
  try:
   assert select.select([proc.stdout],[],[],30)[0], 'Allocation child did not become ready'
   assert proc.stdout.readline().strip()=='ready'
   cmd=['malloc_history',str(proc.pid),'-allEvents','-noContent']
   with (R/('allocation-'+label+'-events.txt')).open('w') as log:
    result=subprocess.run(cmd,stdout=log,stderr=subprocess.PIPE,text=True,timeout=30)
   (R/('allocation-'+label+'-result.json')).write_text(json.dumps(dict(command=cmd,exit_code=result.returncode,stderr=result.stderr),indent=2)+'\n')
   print(label,'history exit',result.returncode,flush=True)
   if result.returncode:print(result.stderr[:1500],flush=True)
  finally:
   if proc.poll() is None:
    proc.communicate('done\n',timeout=10)
   assert proc.returncode==0,proc.returncode
