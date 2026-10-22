from pathlib import Path
import hashlib,json,subprocess,statistics as st,sys
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-number-loop-20261022');V=Path('/private/tmp/swiftsci-csv-loop-profile-20261022');W=Path('/private/tmp/swiftsci-csv-wide-profile-20261022');E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state,environment,verify_uninstrumented
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
engines=['current','inline-pair','set-iteration','set-isolated']
bins={'current':P/'build/production/ResourceProbe',**{e:R/'build'/e/'ResourceProbe' for e in engines[1:]}}
roots={'current':S,**{e:R/(e+'-trial') for e in engines[1:]}}
for e,b in bins.items():
 verify_uninstrumented(b);rec=json.loads(b.with_name('build.json').read_text());assert h(b)==rec['binary_sha256'];assert all(h(roots[e]/p)==sha for p,sha in rec['sources'].items())
orders=[engines[i:]+engines[:i] for i in range(len(engines))]+[list(reversed(engines[i:]+engines[:i])) for i in range(len(engines))]
cases=[(c,E/'inputs'/(c+'.json'),m) for c,m in [('Aotizhongxin','known'),('Wanliu','known'),('energy','known'),('energy','infer'),('energy-date-full','known'),('late-text','infer')]]
for item in json.loads((P/'text-contracts.json').read_text()):
 path=Path(item);name=path.stem;family=name.removeprefix('all-string-')
 if family.startswith(('default-','pair-','four-','large-','none-')):cases.append((name,path,'known'))
cases += [(f'width-{width}-rows-{rows}',W/'width-inputs'/f'width-{width}-rows-{rows}.json','known') for width,rows in [(64,257),(64,32769)]]
unique=[];seen=set()
for c,p,m in cases:
 d=json.loads(p.read_text());key=(d.get('source_sha256',d.get('sha256')),tuple(d['types']),tuple(sorted(d['null_tokens'])),m)
 if key not in seen:unique.append((c,p,m));seen.add(key)
cases=unique
plan=dict(binaries={e:dict(path=str(b),sha256=h(b)) for e,b in bins.items()},sources={e:str(p) for e,p in roots.items()},orders=orders,cases=[(c,str(p),m) for c,p,m in cases],environment=environment(),controller_sha256=h(Path(__file__)),scope='Screening only. Native hash randomization; warmed input, matched native outputs and policies. Eight rotated and reversed orders. No source edits/builds/tests during samples.')
D=R/'ownership-screen';D.mkdir(exist_ok=False);(D/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');records=[]
with (D/'workers.jsonl').open('x') as out:
 for case,path,mode in cases:
  inp=json.loads(path.read_text());assert h(Path(inp['path']))==inp.get('source_sha256',inp.get('sha256'))
  for policy in ['parallel','serial']:
   for rnd,order in enumerate(orders):
    assert power_state()['source']=='AC'
    with Path(inp['path']).open('rb') as f:
     while f.read(1024*1024):pass
    for e in order:
     p=subprocess.run([str(bins[e]),str(path),mode,'fresh','1',policy],env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=120);assert p.returncode==0,(case,e,p.stderr)
     d=json.loads(p.stdout);assert d['validated'];assert [c['nulls'] for c in d['checks']['columns']]==inp['null_counts'];d.update(case=case,mode=mode,policy=policy,engine=e,round=rnd);records.append(d);out.write(json.dumps(d)+'\n');out.flush()
   print(case,mode,policy,{e:round(st.median(d['samples'][0]['total_cpu_ns'] for d in records if (d['case'],d['mode'],d['policy'],d['engine'])==(case,mode,policy,e))/1e6,3) for e in engines},flush=True)
summary=[]
for case,path,mode in cases:
 for policy in ['parallel','serial']:
  for e in engines:
   rs=[d['samples'][0] for d in records if (d['case'],d['mode'],d['policy'],d['engine'])==(case,mode,policy,e)]
   summary.append(dict(case=case,mode=mode,policy=policy,engine=e,samples=len(rs),medians={k:st.median(r[k] for r in rs) for k in ['total_cpu_ns','total_ns','process_peak_held_bytes','held_heap_bytes']}))
(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(len(records),'validated screening reads',flush=True)
