from pathlib import Path
import hashlib,json,subprocess,statistics as st,sys
R=Path(__file__).resolve().parent;E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state,environment,verify_uninstrumented
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
forms=['short','production-name','screen-name'];engines=[x+'-'+f for x in ['parent','candidate'] for f in forms]
base={'parent':Path('/private/tmp/swiftsci-csv-number-loop-20261022/build/production'),'candidate':R/'build/production'}
roots={e:base[e.split('-')[0]] for e in engines}
sources={e:(Path('/private/tmp/swiftsci-csv-small-null-control-20261022') if e.startswith('parent-') else S) for e in engines}
argv0={'short':'StreamProbe','production-name':str(R.resolve()/'build/production/StreamProbe'),'screen-name':'/private/tmp/swiftsci-csv-stream-dispatch-20261022/build/attempt-outline/StreamProbe'}
for e,d in roots.items():
 rec=json.loads((d/'build.json').read_text());assert all(h(sources[e]/p)==sha for p,sha in rec['sources'].items())
 for label in ['ResourceProbe','StreamProbe']:verify_uninstrumented(d/label)
orders=[engines[i:]+engines[:i] for i in range(6)]+[list(reversed(engines[i:]+engines[:i])) for i in range(6)]
cases=[('stream','energy')]
D=R/'source-path-screen';D.mkdir(exist_ok=False);plan=dict(binaries={e:{f:dict(path=str(d/f),sha256=h(d/f)) for f in ['ResourceProbe','StreamProbe']} for e,d in roots.items()},sources={e:str(p) for e,p in sources.items()},orders=orders,cases=cases,environment=environment(),controller_sha256=h(Path(__file__)),scope='Diagnostic screening of three independent changes. Matched policies, native scheduling and hash randomization. No source edits, builds, tests or profiling during measurements. Complete independent native-output validation.');(D/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
records=[]
with (D/'workers.jsonl').open('x') as out:
 for scope,case in cases:
  path=E/'inputs'/(case+'.json');inp=json.loads(path.read_text());assert h(Path(inp['path']))==inp.get('source_sha256',inp.get('sha256'))
  for policy in ['parallel']:
   for rnd,order in enumerate(orders):
    assert power_state()['source']=='AC'
    with Path(inp['path']).open('rb') as f:
     while f.read(1024*1024):pass
    for e in order:
     command=[str(roots[e]/('ResourceProbe' if scope=='eager' else 'StreamProbe')),str(path),*(['known','fresh','1',policy] if scope=='eager' else ['10000',policy])]
     executable=command[0];command[0]=argv0[e.split('-',1)[1]]
     p=subprocess.run(command,executable=executable,env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=120);assert p.returncode==0,(e,p.stderr)
     d=json.loads(p.stdout);assert d['validated'];d.update(scope=scope,case=case,policy=policy,engine=e,round=rnd);records.append(d);out.write(json.dumps(d)+'\n');out.flush()
   print(scope,case,policy,{e:round(st.median(d.get('samples',[d])[0]['total_cpu_ns'] for d in records if (d['scope'],d['case'],d['policy'],d['engine'])==(scope,case,policy,e))/1e6,3) for e in engines},flush=True)
summary=[]
for scope,case in cases:
 for policy in ['parallel']:
  for e in engines:
   rs=[d.get('samples',[d])[0] for d in records if (d['scope'],d['case'],d['policy'],d['engine'])==(scope,case,policy,e)];mem='process_peak_held_bytes' if scope=='eager' else 'peak_after_bytes'
   summary.append(dict(scope=scope,case=case,policy=policy,engine=e,samples=len(rs),medians={k:st.median(r[k] for r in rs) for k in ['total_cpu_ns','total_ns',mem]}))
(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(len(records),'validated observations',flush=True)
