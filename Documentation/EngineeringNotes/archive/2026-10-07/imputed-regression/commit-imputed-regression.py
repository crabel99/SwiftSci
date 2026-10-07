from pathlib import Path
import hashlib,json,os,subprocess,sys
repo=Path('/Users/crabel/Documents/src/SwiftSci');root=Path('/Users/crabel/Library/Caches/SwiftSci/retained-gpu-trial-20261007')
out=Path('/Users/crabel/local-ai/spl/swiftsci/imputed-regression-20261007');run=out/'comparison-sustained'
base='8386d2476f32a1f685314134cd0be1b5f291e79d';branch='refs/heads/codex/retained-memory-accounting-trial'
def git(*args,input=None,env=None):return subprocess.check_output(['git','-C',str(repo),*args],input=input,env=env).decode().strip()
assert git('rev-parse',branch)==base
assert git('rev-parse','HEAD')=='6e10f5833961d6813cc65b0491fe622c83c55a5d'
assert not git('status','--porcelain=v1','--untracked-files=no')
t=json.loads((out/'final-release-summary.json').read_text());assert (t['passedTests'],t['failedTests'],t['skippedTests'])==(874,0,2)
assert 'Ran 16 tests' in (out/'controller-tests-final.log').read_text() and '\nOK' in (out/'controller-tests-final.log').read_text()
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from compare_gpu_pipeline_service import validate,IMPUTER_CASES
p=json.loads((run/'provenance.json').read_text())
for path,digest in p['source_sha256'].items():assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,path
worker=Path('/Users/crabel/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release/SwiftSciRetainedGPUTrial')
assert hashlib.sha256(worker.read_bytes()).hexdigest()==p['binary_sha256']
s=json.loads((run/'summary.json').read_text())
assert len(s)==24 and {(r['round'],r['case'],r['storage']) for r in s}=={(i,c,m) for i in range(3) for c in IMPUTER_CASES for m in ['copy','owned']}
reference={};parameters={};requests=0
for item in s:
 case=item['case'];mode=item['storage'];schedule,rows,cols,count=IMPUTER_CASES[case]
 record=json.loads((run/f"{item['round']}-{case}-{mode}.json").read_text())
 digest=validate(record,mode,schedule,rows,cols,count,'imputer-minmax')
 if case in reference:assert digest==reference[case] and record['parameters_sha256']==parameters[case]
 reference[case]=digest;parameters[case]=record['parameters_sha256'];requests+=count
 assert item['elapsed_ms']==record['elapsed_ms'] and item['requests_per_second']==record['requests_per_second']
 assert item['measured_rss_mib']==record['measured']['rss_bytes']/1024**2
assert requests==149760
source=json.loads((out/'source-verification/validation.json').read_text())
assert source['complete'] and source['binary_sha256']==p['binary_sha256'] and len(source['results'])==8
checks=0
for case,(schedule,rows,cols,_) in IMPUTER_CASES.items():
 a=None
 for mode in ['copy','owned']:
  record=json.loads((out/'source-verification'/f'{case}-{mode}.json').read_text())
  digest=validate(record,mode,schedule,rows,cols,8,'imputer-minmax',verify_source=True)
  if a is not None:assert digest==a
  a=digest;checks+=record['source_checks']
assert checks==32
assert json.loads((out/'cleanup.json').read_text())['trial_workers_remaining']==0
files=['Benchmarks/RetainedGPUTrial/PipelineServiceWorkflow.swift','Benchmarks/RetainedGPUTrial/ImputedRegressionPreparation.swift','Benchmarks/RetainedGPUTrial/README.md','Benchmarks/Tools/compare_gpu_pipeline_service.py','Benchmarks/Tests/test_gpu_pipeline_service.py','Tests/SwiftMLTests/ImputedRegressionWorkflowTests.swift']
changed=set(subprocess.check_output(['git','-C',str(root),'diff','--name-only',base]).decode().splitlines())|set(subprocess.check_output(['git','-C',str(root),'ls-files','--others','--exclude-standard']).decode().splitlines())
assert changed==set(files),changed
assert not any(p.startswith('Sources/') for p in changed)
env=dict(os.environ,GIT_INDEX_FILE=str(out/'commit.index'));git('read-tree',base,env=env)
for path in files:
 blob=git('hash-object','-w','--stdin',input=(root/path).read_bytes());git('update-index','--add','--cacheinfo',f'100644,{blob},{path}',env=env)
git('diff','--cached','--check',base,env=env)
assert set(git('diff','--cached','--name-only',base,env=env).splitlines())==set(files)
message='''test(memory): qualify imputation through held-out GPU regression

Fit imputation and scaling on training data, fit CPU regression, then run
shifted held-out observations with missing flags and NaNs through public
GPU prediction APIs. Preserve the existing finite-input policy.

Compare retained and consumed inputs using complete output hashes,
independent analytic predictions, fitted parameter fingerprints and
consumed column addresses. Verify retained source values and validity in
separate child processes so source hashing does not distort timing.

Check four request windows per worker without intermediate cache clears;
require request reservations and MLX owners to return to baseline, then
release the model and cached allocations. Keep old continuous modes.

Validation: 874 selected Release tests passed, two optional skips; 16
controller tests passed. Eight integrity workers and 24 sustained workers
passed, covering 64 integrity and 149,760 timed requests. Production
sources unchanged. Performance and memory evidence is in engineering-notes.
'''
c=git('commit-tree',git('write-tree',env=env),'-p',base,input=message.encode());git('update-ref',branch,c,base)
(out/'commit.json').write_text(json.dumps({'base':base,'commit':c,'files':files,'file_sha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in files}},indent=2)+'\n')
subprocess.run(['git','-C',str(root),'read-tree',c],check=True);subprocess.run(['git','-C',str(root),'update-ref','HEAD',c,base],check=True)
print(c)
