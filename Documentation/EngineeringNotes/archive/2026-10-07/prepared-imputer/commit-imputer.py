from pathlib import Path
import hashlib,json,os,subprocess,sys
repo=Path('/Users/crabel/Documents/src/SwiftSci')
root=Path('/Users/crabel/Library/Caches/SwiftSci/retained-gpu-trial-20261007')
out=Path('/Users/crabel/local-ai/spl/swiftsci/prepared-imputer-20261007')
base='a075d7f52ef8fb75ba8b623e1ca21235f89764ab'
branch='refs/heads/codex/retained-memory-accounting-trial'
def git(*args,input=None,env=None):
 return subprocess.check_output(['git','-C',str(repo),*args],input=input,env=env).decode().strip()
assert git('rev-parse',branch)==base
assert git('rev-parse','HEAD')=='6e10f5833961d6813cc65b0491fe622c83c55a5d'
assert not git('status','--porcelain=v1','--untracked-files=no')
t=json.loads((out/'verified-release-summary.json').read_text())
assert (t['passedTests'],t['failedTests'],t['skippedTests'])==(872,0,2)
assert (out/'red.log').read_text().count('recorded an issue')==3
assert 'Ran 12 tests' in (out/'controller-tests.log').read_text() and '\nOK' in (out/'controller-tests.log').read_text()
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from compare_imputer_pipeline import validate,CASES
p=json.loads((out/'comparison/provenance.json').read_text())
for path,digest in p['source_sha256'].items():
 assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,path
worker=Path('/Users/crabel/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release/SwiftSciRetainedGPUTrial')
assert hashlib.sha256(worker.read_bytes()).hexdigest()==p['binary_sha256']
s=json.loads((out/'comparison/summary.json').read_text())
assert {(r['round'],r['case'],r['path']) for r in s}=={(i,c,m) for i in range(3) for c in CASES for m in ['rows','copy','owned']}
assert len(s)==27
reference={};requests=0
for item in s:
 case=item['case'];mode=item['path'];rows,cols,count=CASES[case]
 record=json.loads((out/'comparison'/f"{item['round']}-{case}-{mode}.json").read_text())
 digest=validate(record,mode,rows,cols,count)
 if case in reference:assert digest==reference[case]
 reference[case]=digest;requests+=count
 assert item['elapsed_ms']==record['elapsed_ms']
 assert item['requests_per_second']==record['requests_per_second']
 assert item['rss_mib']==record['measured']['rss_bytes']/1024**2
assert requests==304416
assert json.loads((out/'cleanup.json').read_text())['trial_workers_remaining']==0
files=['Sources/SwiftPreprocessing/Core/Imputer.swift','Sources/SwiftML/SwiftML.docc/PreparedRegression.md','Tests/SwiftPreprocessingTests/PreparedImputerTests.swift','Benchmarks/RetainedGPUTrial/Benchmark.swift','Benchmarks/RetainedGPUTrial/ImputerPipelineWorkflow.swift','Benchmarks/RetainedGPUTrial/README.md','Benchmarks/Tools/compare_imputer_pipeline.py','Benchmarks/Tests/test_imputer_pipeline.py']
changed=set(subprocess.check_output(['git','-C',str(root),'diff','--name-only',base]).decode().splitlines())
changed|=set(subprocess.check_output(['git','-C',str(root),'ls-files','--others','--exclude-standard']).decode().splitlines())
assert changed==set(files),changed
subprocess.run(['git','-C',str(root),'diff','--check'],check=True)
env=dict(os.environ,GIT_INDEX_FILE=str(out/'commit.index'))
git('read-tree',base,env=env)
for path in files:
 blob=git('hash-object','-w','--stdin',input=(root/path).read_bytes())
 git('update-index','--add','--cacheinfo',f'100644,{blob},{path}',env=env)
git('diff','--cached','--check',base,env=env)
assert set(git('diff','--cached','--name-only',base,env=env).splitlines())==set(files)
message='''feat(preprocessing): keep imputation in prepared column storage

Add native prepared fitting and consuming transforms to Imputer. Share
existing statistic formulas with the row API and preserve missing-value,
empty-input, error, metadata and copy-on-write behavior. Reuse unique
buffers; detach shared columns only when values need replacement.

Cover ownership, nested pipelines, aliases, strategy edges, failed refits
and concurrent readers. Document that missing values must be filled before
the existing prepared regression finite-input boundary.

Add a CPU imputer/scaler comparison for row, copied and consumed paths.
Three ownership assertions fail before the change. Afterward 872 selected
Release tests pass with two optional skips; 12 controller tests pass.
All 27 comparison workers complete 304,416 measured requests with matching
complete output hashes. Timing evidence remains on engineering-notes.
'''
c=git('commit-tree',git('write-tree',env=env),'-p',base,input=message.encode())
git('update-ref',branch,c,base)
(out/'commit.json').write_text(json.dumps({'base':base,'commit':c,'files':files,'file_sha256':{path:hashlib.sha256((root/path).read_bytes()).hexdigest() for path in files}},indent=2)+'\n')
subprocess.run(['git','-C',str(root),'read-tree',c],check=True)
subprocess.run(['git','-C',str(root),'update-ref','HEAD',c,base],check=True)
print(c)
