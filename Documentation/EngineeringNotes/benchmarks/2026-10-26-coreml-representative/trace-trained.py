"""Profile existing representative public-adapter cases; keep timings observational."""
import argparse, hashlib, json, os, plistlib, shutil, signal, subprocess, sys
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--worker',type=Path,required=True)
p.add_argument('--reference',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
sys.path[:0]=[str(a.source/'Benchmarks/CoreMLInference'),str(a.source/'Benchmarks/Tools')]
from concurrency import run_case, validate
from runner import source_identity, verify_uninstrumented, metal_build_record
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
worker=a.worker.resolve(strict=True); build=json.loads(Path(str(worker)+'.build.json').read_text())
source=source_identity(a.source); assert source==build['source'] and sha(worker)==build['binary_sha256']
verify_uninstrumented(worker); assert metal_build_record(worker)==build['metal']
refs=json.loads((a.reference/'results.json').read_text())
a.output.mkdir(parents=True,exist_ok=False)
profile=a.output/'ProfileWorker';shutil.copy2(worker,profile)
ent=a.output/'entitlements.plist';ent.write_bytes(plistlib.dumps({'com.apple.security.get-task-allow':True}))
subprocess.run(['codesign','--force','--sign','-','--entitlements',str(ent),str(profile)],check=True)
for f in [*worker.parent.glob('*.bundle'),*worker.parent.glob('*.metallib')]:
 (a.output/f.name).symlink_to(f)
records=[];files={};controller=sha(Path(__file__))
for kind in ['wdbc','wine']:
 metadata=json.loads((a.reference/f'fixtures/{kind}-training.json').read_text());rows=len(metadata['heldout_targets'])
 fixture=(a.reference/f'fixtures/{kind}-{rows}.json').resolve();files[str(fixture)]=sha(fixture)
 for policy in ['cpu','neural']:
  name=f'{kind}-{policy}'
  q=dict(fixture=str(fixture),rows=rows,policy=policy,callers=1,instances=1,admissionSlots=1,seconds=2,rssLimitBytes=1_073_741_824)
  base=next(r for r in refs if r['workload']==kind and r['rows']==rows and r['mode']==f'coreml-{policy}-matrix-adapter')
  reference=run_case(worker,a.output,name+'-uninstrumented',q)
  assert reference['modelSHA256']==base['modelSHA256']
  request=a.output/(name+'.request.json');result=a.output/(name+'.json');trace=a.output/(name+'.trace')
  save(request,q)
  cmd=['xcrun','xctrace','record','--template','Time Profiler','--instrument','Core ML','--instrument','Neural Engine','--instrument','Points of Interest','--time-limit','42s','--output',str(trace),'--no-prompt','--launch','--',str(profile),'--coreml-concurrency',str(request),str(result)]
  save(a.output/(name+'.command.json'),cmd)
  print(name,flush=True)
  with (a.output/(name+'.log')).open('w') as log:
   process=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   try:code=process.wait(timeout=92)
   finally:
    try:os.killpg(process.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    process.wait()
    owned=str(profile)+' --coreml-concurrency '+str(request)+' '
    for line in subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines():
     parts=line.strip().split(None,1)
     if len(parts)==2 and parts[1].startswith(owned):
      try:os.kill(int(parts[0]),signal.SIGKILL)
      except ProcessLookupError:pass
  assert code==0, f'{name} recording failed with {code}'
  record=json.loads(result.read_text());validate(record,q)
  assert record['modelSHA256']==reference['modelSHA256'] and record['outputHashes']==reference['outputHashes']
  toc=a.output/(name+'.toc.xml')
  subprocess.run(['xcrun','xctrace','export','--input',str(trace),'--toc','--output',str(toc)],check=True,timeout=60)
  records.append(dict(name=name,uninstrumented=reference,profiled=record))
  save(a.output/'results.json',records)
assert source_identity(a.source)==source and sha(worker)==build['binary_sha256'] and sha(Path(__file__))==controller
assert all(sha(Path(path))==value for path,value in files.items())
save(a.output/'provenance.json',dict(source=source,build=build,controller_sha256=controller,profiling_worker_sha256=sha(profile),reference_results_sha256=sha(a.reference/'results.json'),fixtures=files,performance_evidence=False,scope='Legacy fixed-matrix artifact, existing synchronous public adapter, one caller; inspect events inside CoreML measurement signpost'))
print('Traces recorded; event inspection still required.',flush=True)
