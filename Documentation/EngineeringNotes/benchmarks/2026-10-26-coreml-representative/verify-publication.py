from pathlib import Path
import gzip,hashlib,json,shutil,subprocess,sys
r=Path(__file__).resolve().parent;records=r/'records';replay=r/'event-replay';replay.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for line in (records/'FILES.sha256').read_text().splitlines():
 expected,name=line.split('  ',1);assert sha(records/name)==expected,name
compression=json.loads((records/'compression-map.json').read_text())
for name,meta in compression.items():assert hashlib.sha256(gzip.decompress((records/name).read_bytes())).hexdigest()==meta['original_sha256'],name
shutil.copy2(records/'inspect-traces.py',replay/'inspect-traces.py');(replay/'traces').mkdir()
transforms=json.loads((records/'publication-transforms.json').read_text())
for name in ['wdbc-cpu','wdbc-neural','wine-cpu','wine-neural']:
 for suffix in ['.json','.toc.xml']:shutil.copy2(records/'traces'/(name+suffix),replay/'traces'/(name+suffix))
 for suffix in ['.coreml.xml','.intervals.xml','.ane.xml']:
  original=r/'traces'/(name+suffix)
  assert sha(original)==compression['traces/'+name+suffix+'.gz']['original_sha256']
  (replay/'traces'/(name+suffix)).symlink_to(original)
with (replay/'inspection.log').open('w') as log:subprocess.run([sys.executable,str(replay/'inspect-traces.py')],stdout=log,stderr=subprocess.STDOUT,check=True)
original=json.loads((records/'traces/inspected-events.json').read_text());again=json.loads((replay/'traces/inspected-events.json').read_text())
for a,b in zip(original,again):
 for key in ['name','target_pid','modelSHA256','measurement_start_ns','measurement_end_ns','completed_requests','event_counts','dispatch_counts','models','first_dispatches','last_dispatches']:assert a[key]==b[key],(a['name'],key)
 transform=transforms['traces/'+a['name']+'.toc.xml']
 assert a['toc_sha256']==transform['original_sha256'] and b['toc_sha256']==transform['published_sha256']
receipt=dict(status='passed',compressed_files_verified=len(compression),event_replay_cases=len(again),redaction='Device identity removed from published TOCs; all target process, interval, model and dispatch results replay identically',script_sha256=sha(Path(__file__)))
(r/'publication-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
