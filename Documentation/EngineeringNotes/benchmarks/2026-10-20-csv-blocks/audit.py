from pathlib import Path
import hashlib,json,subprocess,difflib,statistics
R=Path(__file__).resolve().parent
repo='/private/tmp/swiftsci-scalar-resource-20261019'
base='546510bb7df19fc87a664bded5947c738011ee1d'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()==base
builds={};changed={}
for v in ['baseline','blocked','active','flattened']:
 b=json.loads((R/'build'/v/'build.json').read_text());builds[v]=b
 changes=[];patch=[]
 for name,digest in b['sources'].items():
  p=Path(b['variant']['path'])/name
  assert hashlib.sha256(p.read_bytes()).hexdigest()==digest
  old=subprocess.check_output(['git','show',base+':'+name],cwd=repo)
  if old!=p.read_bytes():
   changes.append(name)
   patch.extend(difflib.unified_diff(old.decode().splitlines(True),p.read_text().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
 assert hashlib.sha256((R/'build'/v/'ResourceProbe').read_bytes()).hexdigest()==b['binary_sha256']
 assert b['harness_sha256']==hashlib.sha256((R/'ResourceProbe.swift').read_bytes()).hexdigest()
 assert b['dependency_objects']==builds['baseline']['dependency_objects']
 changed[v]=changes
 if patch:(R/(v+'.patch')).write_text(''.join(patch))
 assert all('[DEBUG-csvcap]' not in p.read_text() for p in (R/v/'Sources').rglob('*.swift'))
assert changed['baseline']==[]
for v in ['blocked','active','flattened']:
 assert set(changed[v])=={'Sources/SwiftDataFrame/IO/SystemsCSVParser.swift','Sources/SwiftDataFrame/IO/CSVRecordIndex.swift'}
runs=[]
for prefix,v in [('', 'blocked'),('active-','active'),('heldout-','active'),('flattened-','flattened')]:
 plan=json.loads((R/(prefix+'comparison-plan.json')).read_text())
 for fixture,digest in plan['fixtures'].items():
  assert hashlib.sha256(Path(fixture).read_bytes()).hexdigest()==digest
 assert plan['power']['source']=='AC'
 assert json.loads((R/(prefix+'power-end.json')).read_text())['source']=='AC'
 for label,b in plan['builds'].items(): assert b==builds[label]
 es=[json.loads(l) for l in (R/(prefix+'workers.jsonl')).read_text().splitlines()]
 assert len(es)==80
 assert len({(tuple(e['case']),e['phase'],e['pair'],e['variant']) for e in es})==80
 expected={(tuple(c[:3]),ph,p,label) for c in plan['cases'] for ph,n in [('timing',5),('memory',3)] for p in range(n) for label in ['baseline',v]}
 assert {(tuple(e['case']),e['phase'],e['pair'],e['variant']) for e in es}==expected
 for e in es: assert e['validated'] and len(e['samples'])==(5 if e['phase']=='timing' else 1)
 summary=json.loads((R/(prefix+'summary.json')).read_text())
 for row in summary['rows']:
  for label in ['baseline',v]:
   g=[e for e in es if e['case']==row['case'] and e['variant']==label and e['phase']=='timing']
   for metric in ['total_ns','total_cpu_ns']:
    assert statistics.median(statistics.median(s[metric] for s in e['samples']) for e in g)==row['statistics'][label][metric]
  g={label:sorted([e for e in es if e['case']==row['case'] and e['variant']==label and e['phase']=='timing'],key=lambda e:e['pair']) for label in ['baseline',v]}
  ratios=[statistics.median(s['total_cpu_ns'] for s in g[v][i]['samples'])/statistics.median(s['total_cpu_ns'] for s in g['baseline'][i]['samples']) for i in range(5)]
  assert row['cpu_paired']==dict(median_ratio=statistics.median(ratios),range=[min(ratios),max(ratios)])
 runs.append(dict(prefix=prefix,variant=v,workers=80,timing_samples=250,memory_samples=30))
checks=[]
for prefix in ['', 'active-','flattened-']:
 records=json.loads((R/(prefix+'checks.json')).read_text())
 assert len(records)==6
 for r in records:
  assert r['source_sha256']==hashlib.sha256((R/(r['probe']+'.swift')).read_bytes()).hexdigest()
 parity=[r['stdout'] for r in records if r['probe']=='ParserParity']
 assert parity[0]==parity[1] and 'cases=2022' in parity[0]
 assert all('PASS: 7' in r['stdout'] for r in records if r['probe']=='Semantics')
 checks.append(dict(prefix=prefix,parity=parity[0].strip(),explicit_fixtures_per_variant=7))
record=dict(status='passed',baseline_sha=base,changes=changed,runs=runs,checks=checks,total_workers=320,total_timing_samples=1000,total_memory_samples=120)
(R/'audit.json').write_text(json.dumps(record,indent=2)+'\n')
print('PASS: source, binary, harness and fixture hashes; 320 workers; 1000 timing samples; 120 memory samples; semantic checks; recomputed paired CPU summaries')
