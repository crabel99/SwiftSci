import json, collections, hashlib
from pathlib import Path
root=Path('/Users/LOCAL_USER/Documents/src/SwiftSci');out=Path('/private/tmp/swiftsci-suite-neural')
runs=[('suite-neural-03','neural-conformance',{('neural-gpu-rope-cached','swiftsci')}),('suite-neural-loader-02','neural-loader-conformance',{('neural-cpu-public-loader','swiftsci'),('neural-gpu-public-loader','swiftsci')}),('suite-neural-cpu-01','neural-cpu-conformance',set()),('suite-neural-smoke-01','smoke',set())]
results=[]
for name,profile,failures in runs:
 d=root/'Benchmarks/Runs'/name;p=json.loads((root/'Benchmarks/Specs/profiles'/(profile+'.json')).read_text());events=[json.loads(s) for s in (d/'events.jsonl').read_text().splitlines()]
 expected={(c['id'],e,b) for c in p['cases'] for e in ('swiftsci','pandas') for b in range(p['batches'])}
 actual=[(e['case_id'],e['engine'],e['batch']) for e in events];assert len(actual)==len(set(actual)) and set(actual)==expected
 failed={(e['case_id'],e['engine']) for e in events if e['status']!='passed'};assert failed==failures
 errors=[]
 for e in events:
  if e['status']=='passed':assert len(e['result']['samples'])==p['samples'] and all(s['validated'] for s in e['result']['samples'])
  else:
   response=json.loads((d/(e['case_id']+'-'+e['engine']+'-'+str(e['batch'])+'.response.json')).read_text())
   assert response['status']=='failed' and response['case_key']==e['case_key']
   errors.append(dict(e,worker_error=response['error']))
   text=response['error']
   assert ('Output mismatch' in text if 'rope-cached' in e['case_id'] else 'parameter was not replaced exactly' in text)
 cert=json.loads((d/'certificate.json').read_text());assert cert['status']==('failed' if failures else 'passed')
 assert cert['run_sha256']==hashlib.sha256((d/'run.json').read_bytes()).hexdigest()
 log=(out/(name+'-audit.log')).read_text();assert ('Certificate mismatch' if failures else 'PASS: complete validated run') in log
 results.append(dict(run=name,profile=profile,complete_case_coverage=True,cases=len(events),passed=len(events)-len(errors),failed=len(errors),validated_samples=sum(len(e.get('result',{}).get('samples',[])) for e in events if e['status']=='passed'),failures=errors,certificate=cert['status'],audit='rejected failed certificate' if failures else 'passed'))
n=json.loads((out/'negative-workers/summary.json').read_text());assert len(n)==72;assert collections.Counter(x['status'] for x in n)=={'passed':16,'failed':56}
for x in n:assert (x['status']=='passed')==(x['variant'] in ('control','future-token'))
(out/'results.json').write_text(json.dumps(dict(runs=results,negative_controls=dict(total=72,passed=16,rejected=56),controller_tests=105,earlier_unprepared_run='suite-neural-02 did not execute; excluded from coverage and runtime claims'),indent=2)+'\n')
print('Verified all planned event sets, exact failure identities, successful sample counts, certificate hashes, audits and 72 controls.')
