from pathlib import Path
import json,subprocess,hashlib,statistics as st,sys
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-plan-profile-20261022');S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state
engines=['parent','parallel','serial','prototype'];bins={'parent':P/'build/production/ResourceProbe','parallel':R/'build/production/ResourceProbe','serial':R/'build/production/ResourceProbe','prototype':R/'build/serial/ResourceProbe'}
orders=[engines[i:]+engines[:i] for i in range(4)]+[list(reversed(engines[i:]+engines[:i])) for i in range(4)]
cases=[(Path(p).stem,Path(p),'known') for p in json.loads((R/'width-contracts.json').read_text())]
cases += [(f'nullable-{n}-{m}',P/f'nullable-{n}.json',m) for n,m in [(0,'infer'),(50,'infer'),(90,'infer'),(50,'known'),(90,'known')]]
records=[];D=R/'mode-controls';D.mkdir(exist_ok=False)
plan=dict(binaries={e:dict(path=str(b),sha256=hashlib.sha256(b.read_bytes()).hexdigest()) for e,b in bins.items()},orders=orders,cases=[(c,str(p),m) for c,p,m in cases],controller_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(D/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
with (D/'workers.jsonl').open('x') as out:
 for case,path,mode in cases:
  inp=json.loads(path.read_text());assert hashlib.sha256(Path(inp['path']).read_bytes()).hexdigest()==inp.get('source_sha256',inp.get('sha256'))
  for rnd,order in enumerate(orders):
   assert power_state()['source']=='AC'
   for e in order:
    args=[str(path),mode,'fresh','1']+(['serial'] if e=='serial' else []);p=subprocess.run([str(bins[e]),*args],env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=120);assert p.returncode==0,p.stderr
    d=json.loads(p.stdout);assert d['validated'];assert [a['nulls'] for a in d['checks']['columns']]==inp['null_counts'];d.update(case=case,engine=e,round=rnd);records.append(d);out.write(json.dumps(d)+'\n');out.flush()
  print(case,{e:round(st.median(d['samples'][0]['total_cpu_ns'] for d in records if d['case']==case and d['engine']==e)/1e6,3) for e in engines},flush=True)
summary=[dict(case=c,engine=e,medians={k:st.median(d['samples'][0][k] for d in records if d['case']==c and d['engine']==e) for k in ['total_cpu_ns','total_ns','process_peak_held_bytes']}) for c,p,m in cases for e in engines]
(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(len(records),'validated workers',flush=True)
