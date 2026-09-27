import hashlib,json,subprocess
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');out=Path('/private/tmp/swiftsci-suite-finish');directory=root/'Benchmarks/Runs/finish-acceptance-02'
a=json.loads((directory/'acceptance.json').read_text());policy=json.loads((root/'Benchmarks/Specs/acceptance.json').read_text())
assert a['status'] in ('passed','failed') and len(a['profiles'])==len(policy['profiles'])==22
assert [p['profile'] for p in a['profiles']]==[p['profile'] for p in policy['profiles']]
assert a['coverage_complete'],[(p['profile'],p.get('error'),p.get('infrastructure_errors')) for p in a['profiles'] if not p['coverage_complete']]
assert a['source']['commit']==subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
rows=[]
for p in a['profiles']:
 d=directory/p['profile'];r=json.loads((d/'run.json').read_text());c=json.loads((d/'certificate.json').read_text())
 assert r['plan']['source']==a['source']==c['source']
 assert r['plan']['engines']['swiftsci']['build']['source']['tree_sha256']==a['source']['tree_sha256']
 assert hashlib.sha256((d/'run.json').read_bytes()).hexdigest()==p['run_sha256']==c['run_sha256']
 assert hashlib.sha256((d/'certificate.json').read_bytes()).hexdigest()==p['certificate_sha256']
 rows.append(dict(profile=p['profile'],status=p['status'],engine_cases=p['engine_cases'],passed=p['passed'],failed=len(p['failures']),failures=p['failures']))
assert all(p['status']=='passed' for p in rows if p['profile'] in ('vision-conformance','boundary-conformance','boundary-cpu-conformance','boundary-sweep'))
record=dict(commit=a['source']['commit'],source_tree_sha256=a['source']['tree_sha256'],contract_sha256=a['contract_sha256'],acceptance_sha256=hashlib.sha256((directory/'acceptance.json').read_bytes()).hexdigest(),coverage_complete=True,profiles=rows,total_engine_cases=sum(p['engine_cases'] for p in rows),passed_engine_cases=sum(p['passed'] for p in rows),failed_engine_cases=sum(p['failed'] for p in rows))
(out/'results.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='profiles'},indent=2))
