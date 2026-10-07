from pathlib import Path
import json,hashlib,os,sys,subprocess
repo=Path('/Users/crabel/Documents/src/SwiftSci');root=Path('/Users/crabel/Library/Caches/SwiftSci/retained-gpu-trial-20261007');out=Path('/Users/crabel/local-ai/spl/swiftsci/device-production-20261007')
base='98f9a9268aa2fa82beada688b00b7ddb74171e00';branch='refs/heads/codex/retained-memory-accounting-trial'
def git(*args,input=None,env=None):return subprocess.check_output(['git','-C',str(repo),*args],input=input,env=env).decode().strip()
assert git('rev-parse',branch)==base and git('rev-parse','HEAD')=='6e10f5833961d6813cc65b0491fe622c83c55a5d'
assert not git('status','--porcelain=v1','--untracked-files=no')
t=json.loads((out/'full-release-summary.json').read_text());assert (t['passedTests'],t['failedTests'],t['skippedTests'])==(874,0,2)
assert 'Ran 32 tests' in (out/'controller-tests.log').read_text() and '\nOK' in (out/'controller-tests.log').read_text()
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from compare_gpu_device_reuse import compare_records
from compare_gpu_pipeline_service import validate,IMPUTER_CASES
p=json.loads((out/'comparison/provenance.json').read_text())
worker=Path('/Users/crabel/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release/SwiftSciRetainedGPUTrial')
assert hashlib.sha256(worker.read_bytes()).hexdigest()==p['candidate_binary_sha256']
assert hashlib.sha256(Path(p['baseline']['binary_path']).read_bytes()).hexdigest()==p['baseline']['binary_sha256']
for path,digest in p['candidate_source_sha256'].items():
 data=(out/'controller-used.py').read_bytes() if path=='Benchmarks/Tools/compare_gpu_device_reuse.py' else (root/path).read_bytes()
 assert hashlib.sha256(data).hexdigest()==digest,path
changed_sources={x for x,d in p['baseline']['source_sha256'].items() if x.startswith('Sources/') and p['candidate_source_sha256'].get(x)!=d}
assert changed_sources=={'Sources/SwiftPreprocessing/Core/ScopedGPURead.swift','Sources/SwiftPreprocessing/Core/RetainedGPUInputTrial.swift'}
for path in ['Package.swift','Package.resolved']:
 assert p['baseline']['source_sha256'][path]==p['candidate_source_sha256'][path]
for path,digest in p['baseline']['source_sha256'].items():
 if path.startswith('Benchmarks/RetainedGPUTrial/'):
  assert p['candidate_source_sha256'][path]==digest,path
references={};count=0
for iteration in range(3):
 for case,(schedule,rows,columns,requests) in IMPUTER_CASES.items():
  for storage in ['copy','owned']:
   records={}
   for name in ['baseline','candidate']:
    record=json.loads((out/'comparison'/f'{iteration}-{case}-{storage}-{name}.json').read_text())
    hashes=validate(record,storage,schedule,rows,columns,requests,'imputer-minmax')
    if case in references:assert hashes==references[case]
    references[case]=hashes;records[name]=record;count+=requests
   # Compare each stored summary against the final controller, including its positive denominator guard.
   expected=next(x for x in json.loads((out/'comparison/paired.json').read_text()) if x['round']==iteration and x['case']==case and x['storage']==storage)
   assert all(expected[k]==v for k,v in compare_records(records['baseline'],records['candidate'],storage,case).items())
assert count==299520
assert len(json.loads((out/'comparison/summary.json').read_text()))==48
assert len(json.loads((out/'comparison/paired.json').read_text()))==24
source=json.loads((out/'source-verification/validation.json').read_text())
assert source['complete'] and len(source['results'])==8 and sum(x['source_checks'] for x in source['results'])==32
assert source['binary_sha256']==p['candidate_binary_sha256']
for case,(schedule,rows,columns,_) in IMPUTER_CASES.items():
 for storage in ['copy','owned']:
  validate(json.loads((out/'source-verification'/f'{case}-{storage}.json').read_text()),storage,schedule,rows,columns,8,'imputer-minmax',verify_source=True)
for scaler,schedule,rows,columns in [('standard','fixed',64,3),('minmax','fixed',64,3),('imputer-minmax','fixed',64,3),('imputer-minmax','mixed',65536,65)]:
 for storage in ['copy','owned']:
  name=f'smoke-{scaler}-{schedule}-{storage}.json'
  actual=json.loads((out/name).read_text());parent=json.loads((out.parent/'imputed-regression-20261007'/name).read_text())
  assert validate(actual,storage,schedule,rows,columns,4,scaler)==validate(parent,storage,schedule,rows,columns,4,scaler)
workers=[x for x in subprocess.check_output(['ps','-axo','pid=,comm='],text=True).splitlines() if '/SwiftSciRetainedGPUTrial' in x]
assert not workers,workers
(out/'cleanup.json').write_text(json.dumps({'trial_workers_remaining':0,'checked_using':'ps -axo pid=,comm='},indent=2)+'\n')
files=['Sources/SwiftPreprocessing/Core/MetalDeviceOwner.swift','Sources/SwiftPreprocessing/Core/ScopedGPURead.swift','Sources/SwiftPreprocessing/Core/RetainedGPUInputTrial.swift','Benchmarks/RetainedGPUTrial/README.md','Benchmarks/Tools/compare_gpu_device_reuse.py','Benchmarks/Tests/test_gpu_device_reuse.py']
changed=set(subprocess.check_output(['git','-C',str(root),'diff','--name-only',base]).decode().splitlines())|set(subprocess.check_output(['git','-C',str(root),'ls-files','--others','--exclude-standard']).decode().splitlines())
assert changed==set(files),changed
env=dict(os.environ,GIT_INDEX_FILE=str(out/'commit.index'));git('read-tree',base,env=env)
for path in files:
 blob=git('hash-object','-w','--stdin',input=(root/path).read_bytes());git('update-index','--add','--cacheinfo',f'100644,{blob},{path}',env=env)
git('diff','--cached','--check',base,env=env)
msg='''perf(memory): reuse the default Metal device for shared allocations

Retain the initial default Metal device in one internal owner used by
scoped and retained shared-buffer allocation. Retry lookups after an
initial unavailable-device result. Keep fresh buffers, extent validation,
allocation errors, reservation ownership and GPU synchronization intact.

Add a baseline/candidate controller for the unchanged public pipeline
worker, comparing three rounds, four sizes and both ownership modes.
Require complete output and fitted-parameter equality plus lifecycle checks.

Validation: 874 selected Release tests pass with two optional skips;
32 controller tests pass. All 48 paired-production workers pass 299,520
requests. Eight source-integrity workers preserve retained inputs and
eight smoke workers preserve historical hashes. No request GPU owners or
reservations remain. Detailed timing and limitations stay on engineering-notes.
'''
c=git('commit-tree',git('write-tree',env=env),'-p',base,input=msg.encode());git('update-ref',branch,c,base)
(out/'commit.json').write_text(json.dumps({'base':base,'commit':c,'files':files,'file_sha256':{x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in files}},indent=2)+'\n')
subprocess.run(['git','-C',str(root),'read-tree',c],check=True);subprocess.run(['git','-C',str(root),'update-ref','HEAD',c,base],check=True)
print(c)
