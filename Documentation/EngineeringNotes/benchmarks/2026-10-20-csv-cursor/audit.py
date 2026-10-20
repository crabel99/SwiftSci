from pathlib import Path
import subprocess,json,hashlib,difflib,statistics
R=Path(__file__).resolve().parent
repo='/private/tmp/swiftsci-scalar-resource-20261019';base='546510bb7df19fc87a664bded5947c738011ee1d'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
builds={};changed={}
for v in ['baseline','active','cursor','specialized']:
 b=json.loads((R/'build'/v/'build.json').read_text());builds[v]=b
 changes=[];patch=[]
 for name,digest in b['sources'].items():
  p=Path(b['variant']['path'])/name;assert sha(p)==digest
  old=subprocess.check_output(['git','show',base+':'+name],cwd=repo)
  if old!=p.read_bytes():
   changes.append(name);patch.extend(difflib.unified_diff(old.decode().splitlines(True),p.read_text().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
 assert sha(R/'build'/v/'ResourceProbe')==b['binary_sha256']
 assert sha(R/'ResourceProbe.swift')==b['harness_sha256']
 assert b['dependency_objects']==builds['baseline']['dependency_objects']
 changed[v]=changes
 if patch:(R/(v+'.patch')).write_text(''.join(patch))
assert changed['baseline']==[]
assert set(changed['active'])=={'Sources/SwiftDataFrame/IO/CSVRecordIndex.swift','Sources/SwiftDataFrame/IO/SystemsCSVParser.swift'}
for v in ['cursor','specialized']:
 assert set(changed[v])==set(changed['active'])|{'Sources/SwiftDataFrame/IO/CSVReader.swift'}
 assert (R/v/'Sources/SwiftDataFrame/IO/SystemsCSVParser.swift').read_bytes()==(R/'active/Sources/SwiftDataFrame/IO/SystemsCSVParser.swift').read_bytes()
for name,digest in json.loads(Path('/private/tmp/swiftsci-csv-blocks-20261020/build/active/build.json').read_text())['sources'].items():assert builds['active']['sources'][name]==digest
runs=[]
for prefix,old,new in [('', 'active','cursor'),('heldout-','active','cursor'),('specialized-','active','specialized'),('heldout-specialized-','active','specialized'),('production-','baseline','cursor'),('heldout-production-','baseline','cursor')]:
 plan=json.loads((R/(prefix+'comparison-plan.json')).read_text())
 for path,digest in plan['fixtures'].items():assert sha(Path(path))==digest
 assert plan['power']['source']=='AC' and json.loads((R/(prefix+'power-end.json')).read_text())['source']=='AC'
 for v,b in plan['builds'].items():assert b==builds[v]
 es=[json.loads(l) for l in (R/(prefix+'workers.jsonl')).read_text().splitlines()]
 assert len(es)==80
 expected={(tuple(c[:3]),ph,p,v) for c in plan['cases'] for ph,n in [('timing',5),('memory',3)] for p in range(n) for v in [old,new]}
 assert {(tuple(e['case']),e['phase'],e['pair'],e['variant']) for e in es}==expected
 for e in es:assert e['validated'] and len(e['samples'])==(5 if e['phase']=='timing' else 1)
 summary=json.loads((R/(prefix+'summary.json')).read_text())
 for row in summary['rows']:
  groups={v:sorted([e for e in es if e['case']==row['case'] and e['variant']==v and e['phase']=='timing'],key=lambda e:e['pair']) for v in [old,new]}
  for v,g in groups.items():
   for metric in ['total_ns','total_cpu_ns']:
    assert statistics.median(statistics.median(s[metric] for s in e['samples']) for e in g)==row['statistics'][v][metric]
  ratios=[statistics.median(s['total_cpu_ns'] for s in groups[new][i]['samples'])/statistics.median(s['total_cpu_ns'] for s in groups[old][i]['samples']) for i in range(5)]
  assert row['cpu_paired']==dict(median_ratio=statistics.median(ratios),range=[min(ratios),max(ratios)])
 runs.append(dict(prefix=prefix,reference=old,candidate=new,workers=80))
for name in ['checks.json','specialized-checks.json']:
 checks=json.loads((R/name).read_text());assert len(checks)==9
 for c in checks:assert sha(R/(c['probe']+'.swift'))==c['source_sha256']
 assert len({c['stdout'] for c in checks if c['probe']=='ParserParity'})==1
 assert all('PASS: 7' in c['stdout'] for c in checks if c['probe']=='Semantics')
lookup=json.loads((R/'lookup-builds.json').read_text())
for v,b in lookup.items():
 for name,digest in b['source_hashes'].items():assert sha(Path(name))==digest
 assert sha(R/'LookupProbe.swift')==b['probe_sha256'] and sha(R/'build'/v/'LookupProbe')==b['binary_sha256']
assert '2800581' in lookup['cursor']['correctness']['stdout']
assert lookup['cursor']['correctness']['source_sha256']==sha(R/'CursorChecks.swift')
index=json.loads((R/'index-plan.json').read_text())
for v,b in index['builds'].items():
 for name,digest in b['source_hashes'].items():assert sha(Path(name))==digest
 assert sha(R/'IndexProbe.swift')==b['probe_sha256'] and sha(R/'build'/v/'IndexProbe')==b['binary_sha256']
assert index['power']['source']=='AC' and json.loads((R/'index-power-end.json').read_text())['source']=='AC'
for name,number,reps in [('lookup-workers.jsonl',45,10),('index-workers.jsonl',30,5)]:
 es=[json.loads(l) for l in (R/name).read_text().splitlines()];assert len(es)==number
 assert len({(e['fixture'],e['pair'],e['variant']) for e in es})==number
 assert all(len(e['samples'])==reps for e in es)
 for fixture in {e['fixture'] for e in es}:assert len({e['checksum'] for e in es if e['fixture']==fixture})==1
for receipt in json.loads((R/'test-receipts.json').read_text()):
 assert receipt['exit_code']==0
 for name,digest in receipt['sources'].items():assert sha(R/'tests'/name)==digest
 log=R/'test-build'/receipt['variant']/'tests.log'
 assert sha(log)==receipt['output_sha256'] and '16 tests in 4 suites passed' in log.read_text()
record=dict(status='passed',base_sha=base,changes=changed,runs=runs,full_api_workers=480,timing_samples=1500,memory_samples=180,diagnostic_workers=75,diagnostic_samples=600,cursor_offsets_checked=2800581,parser_parity_cases=2022,existing_csv_tests_per_candidate=16)
(R/'audit.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
