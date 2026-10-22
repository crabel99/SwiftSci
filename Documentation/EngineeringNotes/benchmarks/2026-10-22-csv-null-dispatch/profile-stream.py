from pathlib import Path
import subprocess,json,hashlib,select,sys
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-number-loop-20261022');S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=(R/'stream-profiles/driver.swift').read_text()
D=R/'stream-profiles'
for label,root in [('parent',P/'build/production'),('candidate',R/'build/production')]:
 rec=json.loads((root/'build.json').read_text());source=D/(label+'.swift');source.write_text(base)
 cmd=[str(source) if a.endswith('/ResourceProbe.swift') else a for a in rec['commands'][1]];binary=D/label;cmd[cmd.index('-o')+1]=str(binary)
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
 (D/(label+'-build.json')).write_text(json.dumps(dict(command=cmd,source_sha256=h(source),binary_sha256=h(binary),module_receipt_sha256=h(root/'build.json')),indent=2)+'\n')
 for policy in ['serial','parallel']:
  name=label+'-'+policy;proc=None
  try:
   with (D/(name+'.stderr')).open('w') as err:
    contract='/private/tmp/swiftsci-csv-cpu-profile-20261021/inputs/energy.json'
    proc=subprocess.Popen([str(binary),contract,policy],env=worker_environment(PRODUCTION_MODE),stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=err,text=True)
    assert select.select([proc.stdout],[],[],60)[0] and proc.stdout.readline().strip()=='ready'
    proc.stdin.write('go\n');proc.stdin.flush();command=['sample',str(proc.pid),'3','1','-file',str(D/(name+'.sample.txt'))]
    p=subprocess.run(command,capture_output=True,text=True,timeout=30);assert p.returncode==0,p.stderr
    output,_=proc.communicate(timeout=60);assert proc.returncode==0;assert int(output.strip())>0
    (D/(name+'.json')).write_text(json.dumps(dict(command=command,returncode=p.returncode,pid=proc.pid,stdout=p.stdout,stderr=p.stderr,driver_rows=int(output.strip()),scope='Diagnostic samples only. Full validation before loop, row checks during eight-second loop, every frame leaves a separate async function. No accepted resource timing.'),indent=2)+'\n');print(name,'profile completed',flush=True)
  finally:
   if proc is not None and proc.poll() is None:proc.kill();proc.communicate(timeout=10)
