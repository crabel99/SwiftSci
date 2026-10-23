from pathlib import Path
import hashlib,json,subprocess,statistics as st,sys
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state,environment,verify_uninstrumented
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
panel=json.loads((R/'metadata-calibration-panel.json').read_text());cases=panel['cases'];engines=['cleanup','twin','metadata'];roots={e:R/'build'/('cleanup' if e=='twin' else e) for e in engines}
orders=([engines[i:]+engines[:i] for i in range(3)]+[list(reversed(engines[i:]+engines[:i])) for i in range(3)])*20
assert len(orders)==panel['workers_per_label_per_case']==120
D=R/'metadata-calibration';D.mkdir(exist_ok=False);receipts={};v=json.loads((R/'variants.json').read_text())
for e,d in roots.items():
 rec=json.loads((d/'build.json').read_text());src=Path(v['cleanup' if e=='twin' else e]['path']);assert all(h(src/p)==sha for p,sha in rec['sources'].items())
 receipts[e]={'module_receipt_sha256':h(d/'build.json'),'binaries':{}}
 for binary in ['ResourceProbe','StreamRepeatProbe']:
  verify_uninstrumented(d/binary);receipts[e]['binaries'][binary]={'path':str(d/binary),'sha256':h(d/binary)}
assert receipts['cleanup']['binaries']==receipts['twin']['binaries']
(D/'plan.json').write_text(json.dumps(dict(panel=panel,receipts=receipts,orders=orders,environment=environment(),controller_sha256=h(Path(__file__)),scope='Actual metadata source head, native hashing only. Same bytes/schema/nulls/scope/policy/chunks. Two warmups and five reads; one median per worker. A/A must pass; no changed thresholds or flag waivers. CPU mean additionally reported, never substituted for historical median review.'),indent=2)+'\n')
rs=[]
with (D/'workers.jsonl').open('x') as out:
 for case in cases:
  path=Path(case['path']);inp=json.loads(path.read_text());assert h(Path(inp['path']))==inp['source_sha256']
  for rnd,order in enumerate(orders):
   assert power_state()['source']=='AC'
   for e in order:
    env=worker_environment(PRODUCTION_MODE);assert not env.get('SWIFT_DETERMINISTIC_HASHING')
    binary='ResourceProbe' if case['scope']=='eager' else 'StreamRepeatProbe'
    args=[str(path),'known','timing','5',case['policy']] if binary=='ResourceProbe' else [str(path),str(inp['rows']),case['policy']]
    p=subprocess.run([binary,*args],executable=str(roots[e]/binary),env=env,capture_output=True,text=True,timeout=120);assert p.returncode==0,p.stderr
    d=json.loads(p.stdout);assert d['validated'] and len(d['samples'])==5
    d.update({k:case[k] for k in ['case','scope','policy']});d.update(engine=e,round=rnd,comparison_sample={k:st.median(x[k] for x in d['samples']) for k in d['samples'][0]})
    rs.append(d);out.write(json.dumps(d)+'\n');out.flush()
  print(case['scope'],case['case'],case['policy'],{e:round(st.median(x['comparison_sample']['total_cpu_ns'] for x in rs if all(x[k]==case[k] for k in ['case','scope','policy']) and x['engine']==e)/1e6,3) for e in engines},flush=True)
summary=[];flags=[]
for case in cases:
 for e in engines:
  xs=[r['comparison_sample'] for r in rs if all(r[k]==case[k] for k in ['case','scope','policy']) and r['engine']==e];m='process_peak_held_bytes' if case['scope']=='eager' else 'peak_after_bytes'
  summary.append(dict(**{k:case[k] for k in ['case','scope','policy']},engine=e,workers=len(xs),medians={k:st.median(x[k] for x in xs) for k in ['total_cpu_ns','total_ns',m]},mean_cpu_ns=st.mean(x['total_cpu_ns'] for x in xs)))
for a in summary:
 if a['engine']=='cleanup':continue
 b=next(b for b in summary if b['engine']=='cleanup' and all(b[k]==a[k] for k in ['case','scope','policy']))
 if a['medians']['total_cpu_ns']>b['medians']['total_cpu_ns']*1.10:flags.append(dict(candidate=a,parent=b,reason='CPU review limit'))
 m='process_peak_held_bytes' if a['scope']=='eager' else 'peak_after_bytes'
 if a['medians'][m]>b['medians'][m]*1.05+8*2**20:flags.append(dict(candidate=a,parent=b,reason='Memory review limit'))
(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(D/'review-flags.json').write_text(json.dumps(flags,indent=2)+'\n')
(D/'decision.json').write_text(json.dumps(dict(aa_passed=not any(f['candidate']['engine']=='twin' for f in flags),candidate_passed=not any(f['candidate']['engine']=='metadata' for f in flags),flags=len(flags)),indent=2)+'\n')
print(len(rs),'validated workers;',len(flags),'review flags',flush=True)
