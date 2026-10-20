from pathlib import Path
import hashlib,json,subprocess,statistics
R=Path(__file__).resolve().parent
repo='/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=json.loads((R/'plan.json').read_text())
for label,b in plan['builds'].items():
 root=Path(b['variant']['path'])
 for name,digest in b['sources'].items():
  assert sha(root/name)==digest
  data=subprocess.check_output(['git','show',b['variant']['sha']+':'+name],cwd=repo)
  assert hashlib.sha256(data).hexdigest()==digest
 assert sha(R/'ResourceProbe.swift')==b['harness_sha256']
 assert sha(R/'build'/label/'ResourceProbe')==b['binary_sha256']
 assert not any(x in ' '.join(b['commands'][0]) for x in ['-sanitize','-profile-generate','-profile-coverage-mapping'])
assert plan['builds']['baseline']['dependency_objects']==plan['builds']['candidate']['dependency_objects']
events=[json.loads(l) for l in (R/'processes.jsonl').read_text().splitlines()]
assert len(events)==192
keys={(tuple(e['case']),e['phase'],e['pair'],e['variant']) for e in events};assert len(keys)==192
for case in plan['cases']:
 for phase,rounds in [('timing',5),('memory',3)]:
  for i in range(rounds):
   pair=[e for e in events if e['case']==case and e['phase']==phase and e['pair']==i]
   assert len(pair)==2 and {e['variant'] for e in pair}=={'baseline','candidate'}
   assert pair[0]['index_sha']==pair[1]['index_sha']
for e in events:
 assert e['validated'] and len(e['samples'])==(5 if e['phase']=='timing' else 1)
 for s in e['samples']:
  assert s['total_cpu_ns']>=0 and s['total_ns']>0
  assert s['held_heap_delta_bytes']>=0
  assert s['process_peak_held_bytes']>=s['process_peak_before_bytes']
# A fresh independent aggregation checks the published medians.
summary=json.loads((R/'summary.json').read_text())
for row in summary['rows']:
 for v,s in row['statistics'].items():
  measured=[e for e in events if e['case']==row['case'] and e['variant']==v and e['phase']=='timing']
  for metric in ['total_ns','total_cpu_ns']:
   assert statistics.median(statistics.median(x[metric] for x in e['samples']) for e in measured)==s[metric]
record={'status':'passed','source_blobs_verified':sum(len(b['sources']) for b in plan['builds'].values()),'workers':len(events),'timed_samples':sum(len(e['samples']) for e in events if e['phase']=='timing'),'memory_samples':sum(len(e['samples']) for e in events if e['phase']=='memory'),'files':{p.name:sha(p) for p in [R/'ResourceProbe.swift',R/'plan.json',R/'processes.jsonl',R/'summary.json',R/'RESULTS.md']}}
(R/'audit.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
