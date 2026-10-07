from pathlib import Path
import json,hashlib,os,sys,subprocess
repo=Path('/Users/crabel/Documents/src/SwiftSci');root=Path('/Users/crabel/Library/Caches/SwiftSci/retained-gpu-trial-20261007');out=Path('/Users/crabel/local-ai/spl/swiftsci/device-reuse-20261007')
base='5e1603eea4a0a66635727e01e6f76e20e883bb06';branch='refs/heads/codex/retained-memory-accounting-trial'
def git(*args,input=None,env=None):return subprocess.check_output(['git','-C',str(repo),*args],input=input,env=env).decode().strip()
assert git('rev-parse',branch)==base and git('rev-parse','HEAD')=='6e10f5833961d6813cc65b0491fe622c83c55a5d'
assert not git('status','--porcelain=v1','--untracked-files=no')
t=json.loads((out/'focused-build-summary.json').read_text());assert (t['passedTests'],t['failedTests'],t['skippedTests'])==(2,0,0)
assert 'Ran 27 tests' in (out/'controller-tests.log').read_text() and '\nOK' in (out/'controller-tests.log').read_text()
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from profile_prediction_phases import validate
worker=Path('/Users/crabel/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release/SwiftSciRetainedGPUTrial')
p=json.loads((out/'comparison/provenance.json').read_text())
assert hashlib.sha256(worker.read_bytes()).hexdigest()==p['binary_sha256']
for path,digest in p['source_sha256'].items():assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,path
reference=None
for iteration in range(2):
 for slots in [1,2]:
  name=f'{iteration}-{slots}.json';hashes=validate(json.loads((out/'comparison'/name).read_text()),slots,1024,6)
  if reference is not None:assert hashes==reference
  reference=hashes
  previous=json.loads((out.parent/'prediction-phases-20261007/prediction'/name).read_text())
  assert hashes=={b['pair']:b['output_sha256'] for b in previous['blocks']}
for slots in [1,2]:
 hashes=validate(json.loads((out/f'smoke-{slots}.json').read_text()),slots,64,2)
 previous=json.loads((out.parent/'prediction-phases-20261007'/f'smoke-prediction-{slots}.json').read_text())
 assert hashes=={b['pair']:b['output_sha256'] for b in previous['blocks']}
assert len(json.loads((out/'comparison/summary.json').read_text()))==72
workers=[x for x in subprocess.check_output(['ps','-axo','pid=,comm='],text=True).splitlines() if x.strip().split(maxsplit=1)[-1].endswith('/SwiftSciRetainedGPUTrial')]
assert not workers,workers
(out/'cleanup.json').write_text(json.dumps({'trial_workers_remaining':0,'checked_using':'ps -axo pid=,comm='},indent=2)+'\n')
files=['Benchmarks/RetainedGPUTrial/PredictionPhasesWorkflow.swift','Benchmarks/RetainedGPUTrial/README.md','Benchmarks/Tools/profile_prediction_phases.py','Benchmarks/Tests/test_prediction_phases.py']
changed=set(subprocess.check_output(['git','-C',str(root),'diff','--name-only',base]).decode().splitlines())|set(subprocess.check_output(['git','-C',str(root),'ls-files','--others','--exclude-standard']).decode().splitlines())
assert changed==set(files),changed
env=dict(os.environ,GIT_INDEX_FILE=str(out/'commit.index'));git('read-tree',base,env=env)
for path in files:
 blob=git('hash-object','-w','--stdin',input=(root/path).read_bytes());git('update-index','--add','--cacheinfo',f'100644,{blob},{path}',env=env)
git('diff','--cached','--check',base,env=env)
msg='''test(memory): compare retained Metal device with per-request lookup

Split device lookup from buffer allocation in the diagnostic actor. Run
public prediction, per-request lookup and retained-handle routes over all
six route-order permutations. The same actor owns the same state in both
diagnostic controls; each request still allocates a fresh Metal buffer.

Version the output schema and reject missing routes, wrong ordering,
output mismatches and invalid phase totals. Preserve aggregate hashes for
identical request IDs. Production source and dispatch remain unchanged.

Two focused Release tests and 27 controller tests pass. Two smoke workers
and four comparison workers preserve historical output hashes and complete
cleanup. The comparison covers 73,728 requests and supports a narrow device
reuse candidate; it is not a production-throughput qualification. Results
and limitations are archived separately on engineering-notes.
'''
c=git('commit-tree',git('write-tree',env=env),'-p',base,input=msg.encode());git('update-ref',branch,c,base)
(out/'commit.json').write_text(json.dumps({'base':base,'commit':c,'files':files,'file_sha256':{x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in files}},indent=2)+'\n')
subprocess.run(['git','-C',str(root),'read-tree',c],check=True);subprocess.run(['git','-C',str(root),'update-ref','HEAD',c,base],check=True)
print(c)
