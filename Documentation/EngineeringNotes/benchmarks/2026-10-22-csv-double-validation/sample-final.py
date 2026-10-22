from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parent;D=R/'build/production';receipt=json.loads((D/'build.json').read_text());binary=R/'SamplingNumeric-production'
cmd=[str(R/'SamplingNumeric.swift') if a.endswith('/ResourceProbe.swift') else a for a in receipt['commands'][1]];cmd[cmd.index('-o')+1]=str(binary)
p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
(R/'sample-production-build.json').write_text(json.dumps(dict(command=cmd,harness_sha256=hashlib.sha256((R/'SamplingNumeric.swift').read_bytes()).hexdigest(),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),module_receipt_sha256=hashlib.sha256((D/'build.json').read_bytes()).hexdigest()),indent=2)+'\n')
with (R/'sample-production-stdout.log').open('w') as out,(R/'sample-production-stderr.log').open('w') as err:
 proc=subprocess.Popen([str(binary),str(R/'numeric-100000-1-1.json')],stdout=out,stderr=err)
 p=subprocess.run(['sample',str(proc.pid),'3','1','-file',str(R/'sample-production.txt')],capture_output=True,text=True);assert p.returncode==0,p.stderr
 assert proc.wait(timeout=60)==0
 (R/'sample-production-receipt.json').write_text(json.dumps(dict(pid=proc.pid,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2)+'\n')
assert (R/'sample-production-stdout.log').read_text().strip()=='300000000'
with (R/'disassembly-production.txt').open('w') as f:subprocess.run(['otool','-tvV',str(binary)],stdout=f,check=True)
raw=subprocess.check_output(['nm','-n',str(binary)],text=True);ls=[l for l in raw.splitlines() if 'appendDouble' in l or 'appendValidatedDoubles' in l];(R/'numeric-symbols-production.txt').write_text(subprocess.check_output(['xcrun','swift-demangle','--compact'],input='\n'.join(ls),text=True)+'\n')
print('Final public-API profile complete; diagnostic only, not accepted CPU timings')
