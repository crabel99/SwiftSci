from pathlib import Path
import json,hashlib,os,sys,subprocess
repo=Path('/Users/crabel/Documents/src/SwiftSci');root=Path('/Users/crabel/Library/Caches/SwiftSci/retained-gpu-trial-20261007');out=Path('/Users/crabel/local-ai/spl/swiftsci/prediction-phases-20261007')
base='4230c29fc00cf7b89bde9d8f1ba000415aa8dd7f';branch='refs/heads/codex/retained-memory-accounting-trial'
def git(*args,input=None,env=None):return subprocess.check_output(['git','-C',str(repo),*args],input=input,env=env).decode().strip()
assert git('rev-parse',branch)==base and git('rev-parse','HEAD')=='6e10f5833961d6813cc65b0491fe622c83c55a5d'
assert not git('status','--porcelain=v1','--untracked-files=no')
t=json.loads((out/'focused-final-summary.json').read_text());assert (t['passedTests'],t['failedTests'],t['skippedTests'])==(2,0,0)
assert 'Ran 25 tests' in (out/'controller-tests.log').read_text() and '\nOK' in (out/'controller-tests.log').read_text()
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from profile_prediction_phases import validate as prediction_validate
from profile_imputed_latency import validate as latency_validate
from compare_gpu_pipeline_service import validate as pipeline_validate
worker=Path('/Users/crabel/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release/SwiftSciRetainedGPUTrial')
for directory in ['prediction','latency']:
 p=json.loads((out/directory/'provenance.json').read_text())
 assert hashlib.sha256(worker.read_bytes()).hexdigest()==p['binary_sha256']
 for path,digest in p['source_sha256'].items():assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,path
reference=None
for iteration in range(2):
 for slots in [1,2]:
  hashes=prediction_validate(json.loads((out/'prediction'/f'{iteration}-{slots}.json').read_text()),slots,1024,6)
  if reference is not None:assert hashes==reference
  reference=hashes
for slots in [1,2]:prediction_validate(json.loads((out/f'smoke-prediction-{slots}.json').read_text()),slots,64,2)
for route in ['preprocessing','direct','pipeline']:
 for slots in [1,2]:
  for iteration in range(2):
   name=f'{iteration}-{route}-{slots}.json'
   hashes=latency_validate(json.loads((out/'latency'/name).read_text()),route,slots,2048,6)
   assert hashes==latency_validate(json.loads((out.parent/'small-imputed-latency-20261007/phases'/name).read_text()),route,slots,2048,6)
  name=f'smoke-{route}-{slots}.json'
  assert latency_validate(json.loads((out/name).read_text()),route,slots,64,2)==latency_validate(json.loads((out.parent/'small-imputed-latency-20261007'/name).read_text()),route,slots,64,2)
for scaler,schedule,rows,columns in [('standard','fixed',64,3),('minmax','fixed',64,3),('imputer-minmax','fixed',64,3),('imputer-minmax','mixed',65536,65)]:
 for storage in ['copy','owned']:
  name=f'smoke-{scaler}-{schedule}-{storage}.json'
  actual=json.loads((out/name).read_text());parent=json.loads((out.parent/'imputed-regression-20261007'/name).read_text())
  assert pipeline_validate(actual,storage,schedule,rows,columns,4,scaler)==pipeline_validate(parent,storage,schedule,rows,columns,4,scaler)
  assert all(set(a)==set(b) for a,b in zip(actual['requests'],parent['requests']))
assert len(json.loads((out/'prediction/summary.json').read_text()))==48
assert len(json.loads((out/'latency/summary.json').read_text()))==144
workers=[x for x in subprocess.check_output(['ps','-axo','pid=,comm='],text=True).splitlines() if x.strip().split(maxsplit=1)[-1].endswith('/SwiftSciRetainedGPUTrial')]
assert not workers,workers
(out/'cleanup.json').write_text(json.dumps({'trial_workers_remaining':0,'checked_using':'ps -axo pid=,comm='},indent=2)+'\n')
files=['Benchmarks/RetainedGPUTrial/Benchmark.swift','Benchmarks/RetainedGPUTrial/ImputedLatencyWorkflow.swift','Benchmarks/RetainedGPUTrial/PipelineServiceWorkflow.swift','Benchmarks/RetainedGPUTrial/PredictionPhasesWorkflow.swift','Benchmarks/RetainedGPUTrial/README.md','Benchmarks/Tools/profile_imputed_latency.py','Benchmarks/Tools/profile_prediction_phases.py','Benchmarks/Tests/test_prediction_phases.py']
changed=set(subprocess.check_output(['git','-C',str(root),'diff','--name-only',base]).decode().splitlines())|set(subprocess.check_output(['git','-C',str(root),'ls-files','--others','--exclude-standard']).decode().splitlines())
assert changed==set(files),changed
env=dict(os.environ,GIT_INDEX_FILE=str(out/'commit.index'));git('read-tree',base,env=env)
for path in files:
 blob=git('hash-object','-w','--stdin',input=(root/path).read_bytes());git('update-index','--add','--cacheinfo',f'100644,{blob},{path}',env=env)
git('diff','--cached','--check',base,env=env)
msg='''test(memory): separate GPU prediction phases and hash encoding

Keep full SHA-256 validation in measured requests and defer hexadecimal
encoding until after measurement, preserving historical output hashes and
the pipeline JSON schema. Add a separate diagnostic actor using production
packing/import and matching GPU algebra, checked against the public model.

Measure actor waiting, validation, allocation, packing, import, graph
construction, completion, readback and scope cleanup. Explicit evaluation
changes lazy execution, so label these host-clock diagnostics separately
from production instrumentation and throughput qualification.

Two focused Release integration tests and 25 controller tests pass.
Sixteen smoke workers preserve historical hashes/schema and lifecycle
checks. Four phase workers and 12 latency workers complete 344,064 requests,
with exact public-output parity and zero final MLX active/cache allocation.
No production behavior or dispatch threshold changes. Evidence remains on
engineering-notes; no general performance speedup is claimed.
'''
c=git('commit-tree',git('write-tree',env=env),'-p',base,input=msg.encode());git('update-ref',branch,c,base)
(out/'commit.json').write_text(json.dumps({'base':base,'commit':c,'files':files,'file_sha256':{x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in files}},indent=2)+'\n')
subprocess.run(['git','-C',str(root),'read-tree',c],check=True);subprocess.run(['git','-C',str(root),'update-ref','HEAD',c,base],check=True)
print(c)
