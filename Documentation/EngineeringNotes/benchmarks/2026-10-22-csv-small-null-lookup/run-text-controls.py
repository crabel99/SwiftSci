from pathlib import Path
import json,subprocess,hashlib,statistics as st,sys
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-loop-profile-20261022');W=Path('/private/tmp/swiftsci-csv-wide-profile-20261022');Q=Path('/private/tmp/swiftsci-csv-plan-profile-20261022');S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state
engines=['parent-parallel','parallel','parent-serial','serial'];bins={e:(P if e.startswith('parent-') else R)/'build/production/ResourceProbe' for e in engines}
orders=[engines[i:]+engines[:i] for i in range(4)]+[list(reversed(engines[i:]+engines[:i])) for i in range(4)]
cases=[(Path(p).stem,Path(p),'known') for p in json.loads((R/'text-contracts.json').read_text())]
# Empty-token-set density variants have identical bytes and semantics. Time each
# unique byte/schema/null contract once instead of counting duplicate evidence.
unique=[];seen=set()
for case,path,mode in cases:
 inp=json.loads(path.read_text())
 key=(inp['source_sha256'],tuple(sorted(inp['null_tokens'])),tuple(inp['types']),mode)
 if key not in seen:unique.append((case,path,mode));seen.add(key)
cases=unique
assert len(cases)==32
records=[];D=R/'text-controls';D.mkdir(exist_ok=False)
plan=dict(binaries={e:dict(path=str(b),sha256=hashlib.sha256(b.read_bytes()).hexdigest()) for e,b in bins.items()},orders=orders,cases=[(c,str(p),m) for c,p,m in cases],controller_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(D/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
with (D/'workers.jsonl').open('x') as out:
 for case,path,mode in cases:
  inp=json.loads(path.read_text());assert hashlib.sha256(Path(inp['path']).read_bytes()).hexdigest()==inp.get('source_sha256',inp.get('sha256'))
  for rnd,order in enumerate(orders):
   assert power_state()['source']=='AC'
   for e in order:
    args=[str(path),mode,'fresh','1']+(['serial'] if e in ['serial','parent-serial'] else []);p=subprocess.run([str(bins[e]),*args],env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=120);assert p.returncode==0,p.stderr
    d=json.loads(p.stdout);assert d['validated'];assert [a['nulls'] for a in d['checks']['columns']]==inp['null_counts'];d.update(case=case,engine=e,round=rnd);records.append(d);out.write(json.dumps(d)+'\n');out.flush()
  print(case,{e:round(st.median(d['samples'][0]['total_cpu_ns'] for d in records if d['case']==case and d['engine']==e)/1e6,3) for e in engines},flush=True)
summary=[dict(case=c,engine=e,medians={k:st.median(d['samples'][0][k] for d in records if d['case']==c and d['engine']==e) for k in ['total_cpu_ns','total_ns','process_peak_held_bytes']}) for c,p,m in cases for e in engines]
(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(len(records),'validated workers',flush=True)

flags=[]
for a in summary:
 if a['engine'] not in ['parallel','serial']:continue
 b=next(b for b in summary if b['engine']=='parent-'+a['engine'] and b['case']==a['case'])
 if a['medians']['total_cpu_ns']>b['medians']['total_cpu_ns']*1.10:flags.append(dict(candidate=a,parent=b,reason='CPU review limit'))
 if a['medians']['process_peak_held_bytes']>b['medians']['process_peak_held_bytes']*1.05+8*2**20:flags.append(dict(candidate=a,parent=b,reason='Memory review limit'))
(D/'review-flags.json').write_text(json.dumps(flags,indent=2)+'\n');print(len(flags),'review flags',flush=True)
