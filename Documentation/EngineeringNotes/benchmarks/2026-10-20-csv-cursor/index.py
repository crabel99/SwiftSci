from pathlib import Path
import json,subprocess,statistics,hashlib,sys
R=Path(__file__).resolve().parent
sys.path.insert(0,'/private/tmp/swiftsci-csv-sort-20261017/Benchmarks/Tools')
from runner import power_state,environment
power=power_state();assert power['source']=='AC'
builds={}
for v in ['baseline','active']:
 receipt=json.loads((R/'lookup-builds.json').read_text())[v]
 cmd=[x.replace('LookupProbe','IndexProbe') for x in receipt['command']]
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
 builds[v]=dict(command=cmd,source_hashes=receipt['source_hashes'],probe_sha256=hashlib.sha256((R/'IndexProbe.swift').read_bytes()).hexdigest(),binary_sha256=hashlib.sha256((R/'build'/v/'IndexProbe').read_bytes()).hexdigest())
paths=[R/'fixtures/1000000-2-True.csv',Path('/Users/crabel/local-ai/spl/swiftsci/pr-resource-metrics-20261018/fixtures/02-pr39-csv-quoted-1000000-4.csv'),R/'fixtures/1000000-4-False.csv']
(R/'index-plan.json').write_text(json.dumps(dict(builds=builds,power=power,environment=environment(),fixtures={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}),indent=2)+'\n')
records=[]
assert not (R/'index-workers.jsonl').exists()
with (R/'index-workers.jsonl').open('w') as f:
 for path in paths:
  for pair in range(5):
   for v in (['baseline','active'] if pair%2==0 else ['active','baseline']):
    p=subprocess.run([str(R/'build'/v/'IndexProbe'),str(path)],capture_output=True,text=True);assert p.returncode==0,p.stderr
    r=dict(variant=v,fixture=str(path),pair=pair,**json.loads(p.stdout));records.append(r);f.write(json.dumps(r)+'\n');f.flush()
  results=[r for r in records if r['fixture']==str(path)]
  assert len({r['checksum'] for r in results})==1
  print(path.name,{v:round(statistics.median(statistics.median(s['cpu_ns'] for s in r['samples']) for r in results if r['variant']==v)/1e6,3) for v in builds},flush=True)
end=power_state();assert end['source']=='AC';(R/'index-power-end.json').write_text(json.dumps(end,indent=2)+'\n')
