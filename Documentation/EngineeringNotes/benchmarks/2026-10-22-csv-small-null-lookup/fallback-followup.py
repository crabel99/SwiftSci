from pathlib import Path
import hashlib,json,subprocess,statistics as st,sys
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-loop-profile-20261022');S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state,environment,verify_uninstrumented
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
engines=['parent','row-null','batch-null'];bins={'parent':P/'build/production/ResourceProbe','row-null':R/'build/production/ResourceProbe','batch-null':R/'build/batch-null/ResourceProbe'}
for b in bins.values():verify_uninstrumented(b)
orders=[engines[i:]+engines[:i] for i in range(3)]+[list(reversed(engines[i:]+engines[:i])) for i in range(3)]
names=['all-string-default-nulls-0','all-string-default-nulls-50','all-string-default-nulls-90','default-nulls-0','four-nulls-50','large-nulls-0','all-string-large-nulls-0','all-string-none-nulls-0']
cases=[(n,R/'text-inputs'/(n+'.json'),42) for n in names]
p=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021/inputs/Aotizhongxin.json');d=json.loads(p.read_text());d['id']='Aotizhongxin-default';d['null_tokens']=['','NA','na','N/A','n/a','null','NULL','NaN','nan','None'];q=R/'Aotizhongxin-default.json';q.write_text(json.dumps(d,indent=2)+'\n');cases.append(('Aotizhongxin-default',q,6))
D=R/'fallback-followup';D.mkdir(exist_ok=False)
plan=dict(binaries={e:dict(path=str(b),sha256=h(b)) for e,b in bins.items()},orders=orders,cases=[(n,str(p),rounds) for n,p,rounds in cases],controller_sha256=h(Path(__file__)),environment=environment(),scope='Follow-up of default/large-set CPU variation. Additional fresh-process samples, native hash randomization. All original results retained. No source or policy changes.')
(D/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');records=[]
with (D/'workers.jsonl').open('x') as out:
 for case,path,rounds in cases:
  inp=json.loads(path.read_text());assert h(Path(inp['path']))==inp.get('sha256',inp.get('source_sha256'))
  for policy in ['parallel','serial']:
   for rnd in range(rounds):
    assert power_state()['source']=='AC'
    for e in orders[rnd%len(orders)]:
     p=subprocess.run([str(bins[e]),str(path),'known','fresh','1',policy],env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=120);assert p.returncode==0,p.stderr
     d=json.loads(p.stdout);assert d['validated'];assert [c['nulls'] for c in d['checks']['columns']]==inp['null_counts'];d.update(case=case,policy=policy,engine=e,round=rnd);records.append(d);out.write(json.dumps(d)+'\n');out.flush()
   print(case,policy,{e:round(st.median(d['samples'][0]['total_cpu_ns'] for d in records if (d['case'],d['policy'],d['engine'])==(case,policy,e))/1e6,3) for e in engines},flush=True)
summary=[]
for case,path,rounds in cases:
 for policy in ['parallel','serial']:
  for e in engines:
   rs=[d['samples'][0] for d in records if (d['case'],d['policy'],d['engine'])==(case,policy,e)]
   summary.append(dict(case=case,policy=policy,engine=e,samples=len(rs),medians={k:st.median(r[k] for r in rs) for k in ['total_cpu_ns','total_ns','process_peak_held_bytes']}))
(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(len(records),'validated follow-up workers',flush=True)
