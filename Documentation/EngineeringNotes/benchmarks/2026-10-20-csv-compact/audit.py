from pathlib import Path
import subprocess,json,hashlib,difflib,statistics
R=Path(__file__).resolve().parent;repo='/private/tmp/swiftsci-scalar-resource-20261019';base='546510bb7df19fc87a664bded5947c738011ee1d'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
builds={};changed={}
for v in ['baseline','active','compact','inlined','packed']:
 b=json.loads((R/'build'/v/'build.json').read_text());builds[v]=b;changes=[];patch=[]
 for name,digest in b['sources'].items():
  p=Path(b['variant']['path'])/name;assert sha(p)==digest
  old=subprocess.check_output(['git','show',base+':'+name],cwd=repo)
  if old!=p.read_bytes():
   changes.append(name);patch.extend(difflib.unified_diff(old.decode().splitlines(True),p.read_text().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
 assert sha(R/'build'/v/'ResourceProbe')==b['binary_sha256'] and sha(R/'ResourceProbe.swift')==b['harness_sha256']
 assert b['dependency_objects']==builds['baseline']['dependency_objects']
 changed[v]=changes
 if patch:(R/(v+'.patch')).write_text(''.join(patch))
assert changed['baseline']==[]
for v in ['active','compact','inlined','packed']:
 assert set(changed[v])=={'Sources/SwiftDataFrame/IO/CSVRecordIndex.swift','Sources/SwiftDataFrame/IO/SystemsCSVParser.swift'}
for name,digest in json.loads(Path('/private/tmp/swiftsci-csv-blocks-20261020/build/active/build.json').read_text())['sources'].items():assert builds['active']['sources'][name]==digest
runs=[]
paths=[(p,p.with_name(p.name.replace('comparison-plan','workers')).with_suffix('.jsonl'),p.with_name(p.name.replace('comparison-plan','summary')),p.with_name(p.name.replace('comparison-plan','power-end'))) for p in sorted(R.glob('*comparison-plan.json'))]
paths.append((R/'return-layout-heldout/plan.json',R/'return-layout-heldout/workers.jsonl',R/'return-layout-heldout/summary.json',R/'return-layout-heldout/power-end.json'))
assert len(paths)==8
for pp,wp,sp,ep in paths:
 plan=json.loads(pp.read_text());old,new=list(plan['builds'])
 for path,digest in plan['fixtures'].items():assert sha(Path(path))==digest
 for v,b in plan['builds'].items():assert b==builds[v]
 assert plan['power']['source']=='AC' and json.loads(ep.read_text())['source']=='AC'
 es=[json.loads(l) for l in wp.read_text().splitlines()];assert len(es)==80
 expected={(tuple(c[:3]),ph,p,v) for c in plan['cases'] for ph,n in [('timing',5),('memory',3)] for p in range(n) for v in [old,new]}
 assert {(tuple(e['case']),e['phase'],e['pair'],e['variant']) for e in es}==expected
 for e in es:assert e['validated'] and len(e['samples'])==(5 if e['phase']=='timing' else 1)
 summary=json.loads(sp.read_text())
 for row in summary['rows']:
  groups={v:sorted([e for e in es if e['case']==row['case'] and e['variant']==v and e['phase']=='timing'],key=lambda e:e['pair']) for v in [old,new]}
  for v,g in groups.items():
   for metric in ['total_ns','total_cpu_ns']:assert statistics.median(statistics.median(s[metric] for s in e['samples']) for e in g)==row['statistics'][v][metric]
  ratios=[statistics.median(s['total_cpu_ns'] for s in groups[new][i]['samples'])/statistics.median(s['total_cpu_ns'] for s in groups[old][i]['samples']) for i in range(5)]
  assert row['cpu_paired']==dict(median_ratio=statistics.median(ratios),range=[min(ratios),max(ratios)])
 runs.append(dict(plan=str(pp.relative_to(R)),reference=old,candidate=new,workers=80))
for name in ['checks.json','inlined-checks.json','packed-checks.json']:
 checks=json.loads((R/name).read_text());assert len(checks)==9
 for c in checks:assert sha(R/(c['probe']+'.swift'))==c['source_sha256']
 assert len({c['stdout'] for c in checks if c['probe']=='ParserParity'})==1
 assert all('PASS: 7' in c['stdout'] for c in checks if c['probe']=='Semantics')
for prefix in ['', 'packed-']:
 for name in ['boundary-checks.json','range-checks.json']:
  c=json.loads((R/(prefix+name)).read_text());assert c['exit_code']==0
  for path,digest in c['source_hashes'].items():assert sha(Path(path))==digest
 for receipt in json.loads((R/(prefix+'test-receipts.json')).read_text()):
  assert receipt['exit_code']==0
  for name,digest in receipt['sources'].items():assert sha(R/'tests'/name)==digest
  log=R/'test-build'/receipt['variant']/'tests.log';assert sha(log)==receipt['output_sha256'] and '16 tests in 4 suites passed' in log.read_text()
for v,c in json.loads((R/'codegen.json').read_text()).items():assert sha(R/'build'/v/'SwiftDataFrame.o')==c['object_sha256']
assert json.loads((R/'runner-guard-check.json').read_text())['passed']
record=dict(status='passed',base_sha=base,changes=changed,runs=runs,valid_workers=640,timing_samples=2000,memory_samples=240,excluded_workers=80,exclusion='excluded-heldout/reason.json',field_parity_checks_per_layout=505836,parser_parity_cases=2022,existing_tests_per_layout=16,automatic_range_offsets='below 2 GiB, above 2 GiB and above 4 GiB')
(R/'audit.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS: 640 audited workers; 2000 timing samples; 240 memory samples; source and binary identities; paired summaries; boundary and regression evidence')
