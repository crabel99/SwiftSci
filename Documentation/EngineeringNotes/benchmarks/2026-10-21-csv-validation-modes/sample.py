from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parent;E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');C=Path('/private/tmp/swiftsci-csv-eager-checks-20261021')
s=(R/'StreamProbe.swift').read_text().split('@MainActor @main struct StreamProbe')[0]
s+='''@MainActor @main struct SamplingLoop {
    static func main() async throws {
        let input = try JSONDecoder().decode(Input.self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1])))
        var options = CSVReadOptions()
        options.columnTypeOverrides = ["date": .date32]
        options.columnDateFormats = input.date_formats ?? [:]
        let url = URL(fileURLWithPath: input.path)
        var total = 0
        for _ in 0..<1500 {
            total += try await consume(DataFrame.readCSVStream(contentsOf: url, chunkSize: 10_000, options: options))
        }
        print(total)
    }
}
''';(R/'SamplingLoop.swift').write_text(s)
for label,root,name in [('original',C,'indexed'),('current',E,'count-only')]:
 receipt=json.loads((root/'build'/name/'build.json').read_text());cmd=[str(R/'SamplingLoop.swift') if a.endswith('/ResourceProbe.swift') else a for a in receipt['commands'][1]];binary=R/('SamplingLoop-'+label);cmd[cmd.index('-o')+1]=str(binary)
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
 (R/('sample-'+label+'-build.json')).write_text(json.dumps(dict(command=cmd,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest()),indent=2)+'\n')
# Profile fresh processes from frozen modules, one at a time. These are diagnostic, not accepted timings.
for label in ['original','current']:
 with (R/('sample-'+label+'-stdout.log')).open('w') as out, (R/('sample-'+label+'-stderr.log')).open('w') as err:
  proc=subprocess.Popen([str(R/('SamplingLoop-'+label)),str(R/'date-100000-1.json')],stdout=out,stderr=err)
  sampling=subprocess.run(['sample',str(proc.pid),'3','1','-file',str(R/('sample-'+label+'.txt'))],capture_output=True,text=True)
  (R/('sample-'+label+'-receipt.json')).write_text(json.dumps(dict(pid=proc.pid,exit_code=sampling.returncode,stdout=sampling.stdout,stderr=sampling.stderr),indent=2)+'\n')
  assert sampling.returncode==0,sampling.stderr
  assert proc.wait(timeout=60)==0
 print(label,'profile complete',flush=True)
