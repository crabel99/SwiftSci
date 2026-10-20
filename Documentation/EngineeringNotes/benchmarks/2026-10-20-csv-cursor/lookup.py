from pathlib import Path
import subprocess,json,hashlib,statistics,sys
R=Path(__file__).resolve().parent
sys.path.insert(0,'/private/tmp/swiftsci-csv-sort-20261017/Benchmarks/Tools')
from runner import power_state
assert power_state()['source']=='AC'
receipts={}
for v in ['baseline','active','cursor']:
 sources=[R/v/'Sources/SwiftDataFrame/IO'/n for n in ['CSVRecordIndex.swift','SystemsCSVParser.swift']]
 cmd=['xcrun','swiftc','-O','-whole-module-optimization','-swift-version','6','-target','arm64-apple-macos14.0','-parse-as-library',*[str(p) for p in sources],str(R/'LookupProbe.swift'),'-o',str(R/'build'/v/'LookupProbe')]
 if v=='cursor':cmd += ['-D','CURSOR']
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
 receipts[v]=dict(command=cmd,source_hashes={str(s):hashlib.sha256(s.read_bytes()).hexdigest() for s in sources},probe_sha256=hashlib.sha256((R/'LookupProbe.swift').read_bytes()).hexdigest(),binary_sha256=hashlib.sha256((R/'build'/v/'LookupProbe').read_bytes()).hexdigest())
 if v=='cursor':
  cmd=cmd[:];cmd[cmd.index(str(R/'LookupProbe.swift'))]=str(R/'CursorChecks.swift');cmd[cmd.index('-o')+1]=str(R/'build'/v/'CursorChecks')
  p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
  p=subprocess.run([str(R/'build'/v/'CursorChecks')],capture_output=True,text=True);assert p.returncode==0,p.stderr
  receipts[v]['correctness']=dict(command=cmd,stdout=p.stdout,source_sha256=hashlib.sha256((R/'CursorChecks.swift').read_bytes()).hexdigest())
  print(p.stdout,flush=True)
(R/'lookup-builds.json').write_text(json.dumps(receipts,indent=2)+'\n')
assert not (R/'lookup-workers.jsonl').exists()
paths=[R/'fixtures/1000000-2-True.csv',Path('/Users/crabel/local-ai/spl/swiftsci/pr-resource-metrics-20261018/fixtures/02-pr39-csv-quoted-1000000-4.csv'),R/'fixtures/1000000-4-False.csv']
records=[]
with (R/'lookup-workers.jsonl').open('w') as f:
 for path in paths:
  for pair in range(5):
   for v in (['baseline','active','cursor'] if pair%2==0 else ['cursor','active','baseline']):
    p=subprocess.run([str(R/'build'/v/'LookupProbe'),str(path)],capture_output=True,text=True);assert p.returncode==0,p.stderr
    r=dict(variant=v,fixture=str(path),fixture_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),pair=pair,**json.loads(p.stdout));records.append(r);f.write(json.dumps(r)+'\n');f.flush()
  results=[r for r in records if r['fixture']==str(path)]
  assert len({r['checksum'] for r in results})==1
  print(path.name,{v:round(statistics.median(statistics.median(s['cpu_ns'] for s in r['samples']) for r in results if r['variant']==v)/1e6,3) for v in receipts},flush=True)
assert power_state()['source']=='AC'
