from pathlib import Path
import hashlib,json,subprocess,statistics as st,sys,time
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state,environment,verify_uninstrumented
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
label=sys.argv[1];repetitions=int(sys.argv[2]);engines=sys.argv[3:] or ['production','control','ascii-prefix']
roots={e:R/'build'/e for e in engines}
variants=json.loads((R/'variants.json').read_text())
source_roots={e:Path(variants[e]['path']) for e in engines}
for e,d in roots.items():
 rec=json.loads((d/'build.json').read_text());assert all(h(source_roots[e]/p)==sha for p,sha in rec['sources'].items())
 for binary in ['ResourceProbe','StreamProbe']:verify_uninstrumented(d/binary)
orders=[engines[i:]+engines[:i] for i in range(len(engines))]+[list(reversed(engines[i:]+engines[:i])) for i in range(len(engines))]
orders*=repetitions
flags=json.loads((R/'crossover/review-flags.json').read_text())
selected={(f['candidate']['scope'],f['candidate']['case']) for f in flags}
contracts={Path(p).stem:Path(p) for p in json.loads((R/'crossover-contracts.json').read_text())}
cases=[(scope,case,contracts[case]) for scope,case in sorted(selected)]
P=Path('/private/tmp/swiftsci-csv-string-cost-20261022')
cases += [(scope,'energy-default',P/'inputs/energy-default.json') for scope in ['eager','stream']]
cases += [('eager','Aotizhongxin-default',P/'inputs/Aotizhongxin-default.json')]
D=R/label;D.mkdir(exist_ok=False)
plan=dict(started=time.time(),binaries={e:{b:dict(path=str(d/b),sha256=h(d/b)) for b in ['ResourceProbe','StreamProbe']} for e,d in roots.items()},sources={e:str(p) for e,p in source_roots.items()},orders=orders,cases=[(a,b,str(c)) for a,b,c in cases],environment=environment(),controller_sha256=h(Path(__file__)),argv0='same executable name per scope for every engine',scope='Native output hashes, values, types and null counts checked. Same native parallel/serial policies, native CPU scheduling and hash randomization. No builds, tests or profiling during timings.')
(D/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');records=[]
with (D/'workers.jsonl').open('x') as out:
 for scope,case,path in cases:
  inp=json.loads(path.read_text());assert h(Path(inp['path']))==inp.get('source_sha256',inp.get('sha256'))
  for policy in ['parallel','serial']:
   for rnd,order in enumerate(orders):
    assert power_state()['source']=='AC'
    with Path(inp['path']).open('rb') as f:
     while f.read(1024*1024):pass
    for e in order:
     binary='ResourceProbe' if scope=='eager' else 'StreamProbe'
     args=[str(path),*(['known','fresh','1',policy] if scope=='eager' else [str(inp['rows']) if case != 'energy-default' else '10000',policy])]
     p=subprocess.run([binary,*args],executable=str(roots[e]/binary),env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=120);assert p.returncode==0,(e,p.stderr)
     d=json.loads(p.stdout);assert d['validated']
     if scope=='eager':assert [a['nulls'] for a in d['checks']['columns']]==inp['null_counts']
     d.update(scope=scope,case=case,policy=policy,engine=e,round=rnd);records.append(d);out.write(json.dumps(d)+'\n');out.flush()
   print(scope,case,policy,{e:round(st.median(d.get('samples',[d])[0]['total_cpu_ns'] for d in records if (d['scope'],d['case'],d['policy'],d['engine'])==(scope,case,policy,e))/1e6,3) for e in engines},flush=True)
summary=[]
for scope,case,path in cases:
 for policy in ['parallel','serial']:
  for e in engines:
   rs=[d.get('samples',[d])[0] for d in records if (d['scope'],d['case'],d['policy'],d['engine'])==(scope,case,policy,e)];mem='process_peak_held_bytes' if scope=='eager' else 'peak_after_bytes'
   summary.append(dict(scope=scope,case=case,policy=policy,engine=e,samples=len(rs),medians={k:st.median(r[k] for r in rs) for k in ['total_cpu_ns','total_ns',mem]}))
(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
flags=[]
for a in summary:
 if a['engine']==engines[0]:continue
 b=next(b for b in summary if b['engine']==engines[0] and (b['scope'],b['case'],b['policy'])==(a['scope'],a['case'],a['policy']))
 if a['medians']['total_cpu_ns']>b['medians']['total_cpu_ns']*1.10:flags.append(dict(candidate=a,parent=b,reason='CPU review limit'))
 memory='process_peak_held_bytes' if a['scope']=='eager' else 'peak_after_bytes'
 if a['medians'][memory]>b['medians'][memory]*1.05+8*2**20:flags.append(dict(candidate=a,parent=b,reason='Memory review limit'))
(D/'review-flags.json').write_text(json.dumps(flags,indent=2)+'\n');print(len(records),'validated workers;',len(flags),'review flags',flush=True)
