"""Run existing representative inference controller and the public raw workflow probe."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();r=a.root.resolve()
s=r/'source';worker=r/'ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker'
python=r/'study-env/bin/python'
# Refuse to measure during any known qualification build or workflow job.
for path in [r/'ci-main/main-result.json',r/'ci-bench/benchmarks-result.json',r/'compatibility/result.json']:
 assert json.loads(path.read_text()).get('status')=='passed',path
for tag in ['full-debug','full-release']:
 result=json.loads((r/f'native-{tag}/tests.json').read_text())
 assert result['exit_code']==0 and result['summary']['failedTests']==0 and result['summary']['skippedTests']==0
out=r/'trained-results';assert not out.exists()
cmd=[str(python),str(s/'Benchmarks/CoreMLInference/trained.py'),'--worker',str(worker),'--output',str(out),'--samples','64']
(r/'trained.command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with (r/'trained.log').open('w') as log:subprocess.run(cmd,cwd=s,stdout=log,stderr=subprocess.STDOUT,check=True)
subprocess.run([sys.executable,str(r/'summarize-trained.py'),'--source',str(s),'--results',str(out)],check=True)
probe=r/'workflow-probe/probe'
for f in [*worker.parent.glob('*.bundle'),*worker.parent.glob('*.metallib')]:
 target=probe.parent/f.name
 if not target.exists():target.symlink_to(f)
metadata={}
records=json.loads((out/'results.json').read_text())
for kind in ['wdbc','wine']:
 meta=json.loads((out/f'fixtures/{kind}-training.json').read_text());rows=len(meta['heldout_targets'])
 raw=s/meta['source_manifest']['fixture'];fixture=out/f'fixtures/{kind}-{rows}.json';destination=r/'workflow-probe'/f'{kind}.json'
 assert hashlib.sha256(raw.read_bytes()).hexdigest()==meta['source_manifest']['sha256']
 cmd=[str(probe),str(raw),str(fixture),str(destination)]
 with (r/'workflow-probe'/f'{kind}.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
 result=json.loads(destination.read_text());base=next(x for x in records if x['workload']==kind and x['rows']==rows and x['mode']=='coreml-cpu')
 assert result['modelSHA256']==base['modelSHA256'] and result['rawSHA256']==meta['source_manifest']['sha256']
 assert result['fixtureSHA256']==hashlib.sha256(fixture.read_bytes()).hexdigest()
 assert result['originalRowIndices']==meta['split_ids']['test'] and result['reservedBytesAfterPrediction']==0
 metadata[kind]=dict(command=cmd,result_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),modelSHA256=result['modelSHA256'],referenceExceedances=result['referenceExceedances'])
(r/'workflow-probe/binding.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('Representative inference and complete raw workflow probes finished.',flush=True)
