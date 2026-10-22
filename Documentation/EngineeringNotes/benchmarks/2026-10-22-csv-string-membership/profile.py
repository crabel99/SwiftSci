from pathlib import Path
import json,hashlib,subprocess,select,sys
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE
D=R/'profiles';D.mkdir(exist_ok=False);binary=R/'LoopProfile';contracts=[Path(p) for p in json.loads((R/'contracts.json').read_text())]
for contract in contracts:
 inp=json.loads(contract.read_text());reps=30 if inp['rows']>1000000 else 1600;proc=None
 try:
  with (D/(inp['id']+'.stderr')).open('w') as err:
   proc=subprocess.Popen([str(binary),str(contract),str(reps)],env=worker_environment(PRODUCTION_MODE),stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=err,text=True)
   assert select.select([proc.stdout],[],[],45)[0] and proc.stdout.readline().strip()=='ready'
   proc.stdin.write('go\n');proc.stdin.flush();cmd=['sample',str(proc.pid),'3','1','-file',str(D/(inp['id']+'.sample.txt'))]
   p=subprocess.run(cmd,capture_output=True,text=True,timeout=45);assert p.returncode==0,p.stderr
   out,_=proc.communicate(timeout=120);assert proc.returncode==0,(out,proc.returncode)
   expected=inp['rows']*reps;assert out.strip()==str(expected),(out,expected)
   (D/(inp['id']+'.json')).write_text(json.dumps(dict(command=cmd,pid=proc.pid,stdout=p.stdout,stderr=p.stderr,contract=str(contract),repetitions=reps,row_total=expected,driver_stdout=out,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),scope='Diagnostic thread-stack samples during complete public reads. Native output validation before ready. Serial column conversion, separate async function releases each frame. Sample counts are not process CPU percentages, executed instruction counts, cache counters or acceptance timing.'),indent=2)+'\n');print(inp['id'],'profile completed',flush=True)
 finally:
  if proc is not None and proc.poll() is None:proc.kill();proc.communicate(timeout=10)
