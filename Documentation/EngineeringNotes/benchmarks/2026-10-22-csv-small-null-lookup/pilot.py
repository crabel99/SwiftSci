from pathlib import Path
import hashlib,json,subprocess,statistics as st,sys
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-loop-profile-20261022');W=Path('/private/tmp/swiftsci-csv-wide-profile-20261022');E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state,verify_uninstrumented,environment
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
engines=['parent','lazy-null','linear-null','pair-null'];bins={'parent':P/'build/production/ResourceProbe',**{e:R/'build'/e/'ResourceProbe' for e in engines[1:]}}
for e,b in bins.items():
 verify_uninstrumented(b);rec=json.loads(b.with_name('build.json').read_text());assert h(b)==rec['binary_sha256'];root=S if e=='parent' else R/(e+'-trial');assert all(h(root/p)==sha for p,sha in rec['sources'].items())
orders=[engines[i:]+engines[:i] for i in range(len(engines))]
cases=[(c,E/'inputs'/(c+'.json'),m) for c,m in [('bike-day','known'),('bike-hour','known'),('unique-shuffled','known'),('Aotizhongxin','known'),('Wanliu','known'),('energy','known'),('energy','infer'),('energy-date-full','known'),('late-bool','infer'),('late-text','infer')]]
cases += [(f'width{n}-rows{r}',W/'width-inputs'/f'width-{n}-rows-{r}.json','known') for n,r in [(1,257),(18,257),(64,257),(4,32769),(18,32769),(64,32769)]]
cases += [(Path(p).stem,Path(p),'known') for p in json.loads((R/'text-contracts.json').read_text())]
assert not (R/'pilot.json').exists();records=[]
plan=dict(orders=orders,binaries={e:dict(path=str(b),sha256=h(b)) for e,b in bins.items()},cases=[(c,str(p),m) for c,p,m in cases],environment=environment(),controller_sha256=h(Path(__file__)))
(R/'pilot-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
with (R/'pilot-workers.jsonl').open('x') as out:
 for case,path,mode in cases:
  inp=json.loads(path.read_text());assert h(Path(inp['path']))==inp.get('sha256',inp.get('source_sha256'))
  for policy in ['parallel','serial']:
   for rnd,order in enumerate(orders):
    assert power_state()['source']=='AC'
    with Path(inp['path']).open('rb') as f:
     while f.read(1024*1024):pass
    for e in order:
     p=subprocess.run([str(bins[e]),str(path),mode,'fresh','1',policy],env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=120);assert p.returncode==0,(case,e,p.stderr)
     d=json.loads(p.stdout);assert d['validated'],(case,e,d);assert [c['nulls'] for c in d['checks']['columns']]==inp['null_counts']
     record=dict(case=case,mode=mode,policy=policy,engine=e,round=rnd,result=d);records.append(record);out.write(json.dumps(record)+'\n');out.flush()
   print(case,mode,policy,{e:round(st.median(d['result']['samples'][0]['total_cpu_ns'] for d in records if (d['case'],d['mode'],d['policy'],d['engine'])==(case,mode,policy,e))/1e6,3) for e in engines},flush=True)
(R/'pilot.json').write_text(json.dumps(dict(records=records,**plan),indent=2)+'\n');print(len(records),'validated trial reads',flush=True)
