from pathlib import Path
import json,hashlib,os,sys,subprocess
repo=Path('/Users/crabel/Documents/src/SwiftSci');root=Path('/Users/crabel/Library/Caches/SwiftSci/retained-gpu-trial-20261007');out=Path('/Users/crabel/local-ai/spl/swiftsci/small-imputed-latency-20261007')
base='f0261a2212d08b74f0444d9f76e510e93cb606d8';branch='refs/heads/codex/retained-memory-accounting-trial'
def git(*args,input=None,env=None):return subprocess.check_output(['git','-C',str(repo),*args],input=input,env=env).decode().strip()
assert git('rev-parse',branch)==base and git('rev-parse','HEAD')=='6e10f5833961d6813cc65b0491fe622c83c55a5d'
assert not git('status','--porcelain=v1','--untracked-files=no')
t=json.loads((out/'focused-build-summary.json').read_text());assert (t['passedTests'],t['failedTests'],t['skippedTests'])==(2,0,0)
assert 'Ran 20 tests' in (out/'controller-tests.log').read_text() and '\nOK' in (out/'controller-tests.log').read_text()
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from profile_imputed_latency import validate
p=json.loads((out/'phases/provenance.json').read_text())
for path,digest in p['source_sha256'].items():
 data=(out/'controller-used.py').read_bytes() if path=='Benchmarks/Tools/profile_imputed_latency.py' else (root/path).read_bytes()
 assert hashlib.sha256(data).hexdigest()==digest,path
supplement=json.loads((out/'provenance-supplement.json').read_text())
assert hashlib.sha256((root/'Benchmarks/Tools/profile_imputed_latency.py').read_bytes()).hexdigest()==supplement['final_controller_sha256']
for path,digest in supplement['dependency_sha256'].items():assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest
worker=Path('/Users/crabel/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release/SwiftSciRetainedGPUTrial')
assert hashlib.sha256(worker.read_bytes()).hexdigest()==p['binary_sha256']
reference={};count=0
for iteration in range(2):
 for route in ['preprocessing','direct','pipeline']:
  for slots in [1,2]:
   r=json.loads((out/'phases'/f'{iteration}-{route}-{slots}.json').read_text())
   hashes=validate(r,route,slots,2048,6);key='cpu' if route=='preprocessing' else 'gpu'
   if key in reference:assert hashes==reference[key]
   reference[key]=hashes;count+=2048*12
assert count==294912
assert len(json.loads((out/'phases/summary.json').read_text()))==144
for route in ['preprocessing','direct','pipeline']:
 for slots in [1,2]:validate(json.loads((out/f'smoke-{route}-{slots}.json').read_text()),route,slots,64,2)
workers=[x for x in subprocess.check_output(['ps','-axo','pid=,comm='],text=True).splitlines() if x.strip().split(maxsplit=1)[-1].endswith('/SwiftSciRetainedGPUTrial')]
assert not workers,workers
(out/'cleanup.json').write_text(json.dumps({'trial_workers_remaining':0,'checked_using':'ps -axo pid=,comm='},indent=2)+'\n')
files=['Benchmarks/RetainedGPUTrial/Benchmark.swift','Benchmarks/RetainedGPUTrial/ImputedLatencyWorkflow.swift','Benchmarks/RetainedGPUTrial/README.md','Benchmarks/Tools/profile_imputed_latency.py','Benchmarks/Tests/test_imputed_latency.py']
changed=set(subprocess.check_output(['git','-C',str(root),'diff','--name-only',base]).decode().splitlines())|set(subprocess.check_output(['git','-C',str(root),'ls-files','--others','--exclude-standard']).decode().splitlines())
assert changed==set(files),changed
env=dict(os.environ,GIT_INDEX_FILE=str(out/'commit.index'));git('read-tree',base,env=env)
for path in files:
 blob=git('hash-object','-w','--stdin',input=(root/path).read_bytes());git('update-index','--add','--cacheinfo',f'100644,{blob},{path}',env=env)
git('diff','--cached','--check',base,env=env)
msg='''test(memory): isolate small-request preprocessing and inference latency

Add an opt-in phase diagnostic with same-process alternating ownership,
direct-model and regression-pipeline controls, and one or two request
slots. Keep the original throughput worker and all production code intact.

Check complete predictions, independent analytic error, admission balances
and GPU model cleanup. Label preprocessing as including ownership checks,
and prediction as the complete awaited API call rather than kernel time.

Release build and two focused integration tests pass; 20 controller tests
pass. Six smoke workers and 12 diagnostic workers complete, with 294,912
diagnostic requests and matching outputs. The unchanged throughput rerun
and phase evidence remain on engineering-notes. No dispatch threshold or
production fix is justified by the variable ownership timing observed.
'''
c=git('commit-tree',git('write-tree',env=env),'-p',base,input=msg.encode());git('update-ref',branch,c,base)
(out/'commit.json').write_text(json.dumps({'base':base,'commit':c,'files':files,'file_sha256':{x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in files}},indent=2)+'\n')
subprocess.run(['git','-C',str(root),'read-tree',c],check=True);subprocess.run(['git','-C',str(root),'update-ref','HEAD',c,base],check=True)
print(c)
