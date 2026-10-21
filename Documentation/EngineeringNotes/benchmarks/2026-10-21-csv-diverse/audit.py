from pathlib import Path
import json,hashlib,subprocess,difflib,statistics
r=Path(__file__).resolve().parent
sha='546510bb7df19fc87a664bded5947c738011ee1d';repo=Path('/private/tmp/swiftsci-scalar-resource-20261019')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
builds={v:json.loads((r/'build'/v/'build.json').read_text()) for v in ['baseline','packed','direct']}
for v,b in builds.items():
 assert b['harness_sha256']==h(r/'ResourceProbe.swift')
 assert b['binary_sha256']==h(r/'build'/v/'ResourceProbe')
 for name,digest in b['sources'].items():assert digest==h(r/v/name)
 assert b['dependency_objects']==builds['baseline']['dependency_objects']
for name in builds['baseline']['sources']:
 assert (r/'baseline'/name).read_bytes()==subprocess.check_output(['git','show',sha+':'+name],cwd=repo)
for v in ['packed','direct']:
 patch=[];changed=[]
 for name in builds[v]['sources']:
  a=(r/'baseline'/name).read_text();b=(r/v/name).read_text()
  if a!=b:
   changed.append(name);patch.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
 assert set(changed)=={'Sources/SwiftDataFrame/IO/CSVRecordIndex.swift','Sources/SwiftDataFrame/IO/SystemsCSVParser.swift'}
 (r/(v+'.patch')).write_text(''.join(patch))
# The established packed candidate is unchanged from the previous experiment.
for name in builds['packed']['sources']:
 assert (r/'packed'/name).read_bytes()==(Path('/private/tmp/swiftsci-csv-compact-20261020/packed')/name).read_bytes()
sets={};workers=timings=memories=0
for name in ['direct-primary','layout-primary','packed-diverse','packed-primary']:
 d=r/name;p=json.loads((d/'plan.json').read_text());es=[json.loads(l) for l in (d/'workers.jsonl').read_text().splitlines()]
 assert p['power']['source']==json.loads((d/'power-end.json').read_text())['source']=='AC'
 for path,digest in p['fixtures'].items():assert h(Path(path))==digest
 for v,b in p['builds'].items():assert b==builds[v]
 expected={(tuple(c[:3]),phase,pair,v) for c in p['cases'] for phase,n in [('timing',5),('memory',3)] for pair in range(n) for v in p['builds']}
 actual={(tuple(e['case']),e['phase'],e['pair'],e['variant']) for e in es}
 assert actual==expected and len(es)==len(expected)
 for e in es:
  assert e['validated'] and len(e['samples'])==(5 if e['phase']=='timing' else 1)
  for s in e['samples']:
   assert s['call_cpu_ns']+s['release_cpu_ns']==s['total_cpu_ns']
   assert s['call_ns']+s['release_ns']==s['total_ns']
   if e['phase']=='timing':timings+=1
   else:memories+=1
 summary=json.loads((d/'summary.json').read_text());assert summary['records_sha256']==h(d/'workers.jsonl')
 for row in summary['rows']:
  groups={v:sorted([e for e in es if e['case']==row['case'] and e['variant']==v and e['phase']=='timing'],key=lambda e:e['pair']) for v in p['builds']}
  ratios=[statistics.median(s['total_cpu_ns'] for s in groups[p['candidate']][i]['samples'])/statistics.median(s['total_cpu_ns'] for s in groups[p['reference']][i]['samples']) for i in range(5)]
  assert row['cpu_paired']==dict(median_ratio=statistics.median(ratios),range=[min(ratios),max(ratios)])
 workers+=len(es);sets[name]=dict(workers=len(es),records_sha256=h(d/'workers.jsonl'),plan_sha256=h(d/'plan.json'))
smoke=json.loads((r/'smoke.json').read_text());assert len(smoke)==24 and all(e['exit_code']==0 and json.loads(e['stdout'])['validated'] for e in smoke)
checks=json.loads((r/'checks.json').read_text());assert len(checks)==9
assert len(set(e['stdout'] for e in checks if e['probe']=='ParserParity'))==1
for e in checks:assert e['source_sha256']==h(r/(e['probe']+'.swift'))
stream=json.loads((r/'stream-checks.json').read_text());assert len(stream)==3
for e in stream:assert e['exit_code']==0 and e['source_sha256']==h(r/'StreamChecks.swift') and '4176384 exact field comparisons' in e['stdout']
for name in ['packed-boundary-checks.json','packed-range-checks.json']:
 e=json.loads((r/name).read_text());assert e['exit_code']==0
 for path,digest in e['source_hashes'].items():assert h(Path(path))==digest
for e in json.loads((r/'test-receipts.json').read_text()):
 assert e['exit_code']==0 and e['output_sha256']==h(r/'test-build'/e['variant']/'tests.log')
 for name,digest in e['sources'].items():assert h(r/'tests'/name)==digest
record=dict(base_sha=sha,sets=sets,workers=workers,timing_samples=timings,memory_samples=memories,smoke_workers=24,streaming_fields_per_variant=4176384,production_files_changed=0)
(r/'audit.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
