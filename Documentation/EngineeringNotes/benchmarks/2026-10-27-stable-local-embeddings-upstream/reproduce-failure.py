from pathlib import Path
import hashlib,json,os,subprocess
r=Path(__file__).resolve().parent;probe=r/'baseline-repro/probe';env={k:v for k,v in os.environ.items() if k not in ['SWIFT_DETERMINISTIC_HASHING','SWIFT_HASH_SEED']};counts={'technology':0,'food':0};failure=None
for attempt in range(1,1001):
 d=json.loads(subprocess.check_output([str(probe)],env=env,text=True));counts[d['prediction']]+=1
 if d['prediction']=='food':failure=dict(attempt=attempt,output=d);break
report=dict(status='reproduced' if failure else 'not_reproduced_in_bound',runs=sum(counts.values()),predictions=counts,first_failure=failure,binary_sha256=hashlib.sha256(probe.read_bytes()).hexdigest(),controller_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(r/'classification-failure.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='first_failure'},indent=2));assert failure is not None
