from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-batch-profile-20261022');E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021')
s=(R/'ResourceProbe.swift').read_text().split('@MainActor @main struct ReferenceProbe')[0]
s+='''@MainActor @main struct SamplingNumeric {
    static func main() async throws {
        let input = try JSONDecoder().decode(Input.self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1])))
        var options = CSVReadOptions()
        options.nullValues = Set(input.null_tokens)
        options.delimiter = Character(input.delimiter)
        let url = URL(fileURLWithPath: input.path)
        var total = 0
        for _ in 0..<3000 {
            let frame = try await DataFrame(csv: url, options: options)
            total += frame.shape.rows
        }
        print(total)
    }
}
''';(R/'SamplingNumeric.swift').write_text(s)
for label,d in [('original',E/'build/indexed'),('current',P/'build/production')]:
 record=json.loads((d/'build.json').read_text());cmd=[str(R/'SamplingNumeric.swift') if a.endswith('/ResourceProbe.swift') else a for a in record['commands'][1]];b=R/('SamplingNumeric-'+label);cmd[cmd.index('-o')+1]=str(b)
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
 (R/('sample-'+label+'-build.json')).write_text(json.dumps(dict(command=cmd,harness_sha256=hashlib.sha256((R/'SamplingNumeric.swift').read_bytes()).hexdigest(),binary_sha256=hashlib.sha256(b.read_bytes()).hexdigest(),module_receipt_sha256=hashlib.sha256((d/'build.json').read_bytes()).hexdigest()),indent=2)+'\n')
for label in ['original','current']:
 with (R/('sample-'+label+'-stdout.log')).open('w') as out,(R/('sample-'+label+'-stderr.log')).open('w') as err:
  proc=subprocess.Popen([str(R/('SamplingNumeric-'+label)),str(R/'numeric-100000-1-1.json')],stdout=out,stderr=err)
  p=subprocess.run(['sample',str(proc.pid),'3','1','-file',str(R/('sample-'+label+'.txt'))],capture_output=True,text=True)
  assert p.returncode==0,p.stderr
  assert proc.wait(timeout=60)==0
  (R/('sample-'+label+'-receipt.json')).write_text(json.dumps(dict(pid=proc.pid,command=['sample',str(proc.pid),'3','1'],exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2)+'\n')
 assert (R/('sample-'+label+'-stdout.log')).read_text().strip()=='300000000'
 print(label,'profile complete',flush=True)
