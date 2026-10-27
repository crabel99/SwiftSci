from pathlib import Path
import hashlib,json,subprocess,zipfile
r=Path(__file__).resolve().parent;s=r/'source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
git=lambda *a:subprocess.check_output(['git',*a],cwd=s,text=True).strip()
head='506204920a5a073b1e7bc316476875860bacfda0';base='e19db7dda4567c425b7eb002da82e234e6c7980f';prior='53063789b1893b28250ea239d5fdca4fed84c4c9'
loss='Sources/SwiftML/Losses/Losses.swift';test='Tests/SwiftMLTests/BinaryCrossEntropyTests.swift'
assert git('rev-parse','HEAD')==head and git('status','--porcelain')==''
assert set(git('diff','--name-only',base,head).splitlines())=={loss,test}
for name in [loss,test]:assert hashlib.sha256(subprocess.check_output(['git','show',prior+':'+name],cwd=s)).hexdigest()==sha(s/name)
fingerprints={str(p.relative_to(s)):sha(p) for folder in ['Sources','Tests'] for p in (s/folder).rglob('*.swift')}
red=json.loads((r/'red-source-binding.json').read_text());assert red['base']==base and red['test_sha256']==sha(s/test)
oldloss=hashlib.sha256(subprocess.check_output(['git','show',base+':'+loss],cwd=s)).hexdigest();assert red['loss_sha256']==oldloss
redbuild=json.loads((r/'native-red/build.json').read_text());redtests=json.loads((r/'native-red/tests.json').read_text())
assert redbuild['exit_code']==0 and redtests['exit_code']==65 and redtests['summary']['failedTests']==3
assert redbuild['sources']==dict(fingerprints,**{loss:oldloss})
assert red['tests_log_sha256']==sha(r/'native-red/tests.log') and red['test_receipt_sha256']==sha(r/'native-red/tests.json')
initial=json.loads((r/'ci-main/main-result.json').read_text())
assert len(initial['steps'])==8 and all(x['exit_code']==0 for x in initial['steps'][:7]) and initial['steps'][-1]['exit_code']==127
assert initial['runner_sha256']==sha(r/'full-ci-runner-before-coverage-fix.py')
reports={}
for tag,count in [('green',3),('full-debug',1659),('full-release',1659)]:
 b=json.loads((r/f'native-{tag}/build.json').read_text());t=json.loads((r/f'native-{tag}/tests.json').read_text());sums=t['summary']
 assert b['exit_code']==t['exit_code']==0 and b['sources']==fingerprints and t['strict_onnx_ci']
 assert sums['totalTestCount']==sums['passedTests']==count and sums['failedTests']==sums['skippedTests']==0
 reports[tag]={k:sums[k] for k in ['totalTestCount','passedTests','failedTests','skippedTests']}
for name,count in [('ci-main-fixed/main-result.json',8),('ci-bench/benchmarks-result.json',19),('compatibility/result.json',3),('ci-security-python/security-python-result.json',2)]:
 d=json.loads((r/name).read_text());assert d['status']=='passed' and len(d['steps'])==count and all(x['exit_code']==0 for x in d['steps'])
 if 'commit' in d:assert d['commit']==head and d['initial_git_status']==d['final_git_status']==''
 if 'sources' in d:assert d['sources']==fingerprints
 if 'source_fingerprints' in d:
  assert all(sha(s/path)==digest for path,digest in d['source_fingerprints'].items())
  assert all(d['source_fingerprints'].get(path)==digest for path,digest in fingerprints.items())
 for step in d['steps']:
  if 'log_sha256' in step:assert sha(Path(step['log']))==step['log_sha256']
 reports[name]=dict(status=d['status'],steps=count,sha256=sha(r/name))
p=json.loads((r/'ci-security-python/security-python-result.json').read_text());assert p['security_findings']['python']==0
policy=json.loads((r/'ci-bench/ci-acceptance/regression-policy.json').read_text());assert policy['source']['commit']==head and policy['status']=='passed' and not policy['blocking'] and policy['conformance_status']=='failed' and len(policy['known_failures'])==4
assert all(x['engine']=='pandas' for x in policy['known_failures'])
security=r/'ci-security-swift633';d=json.loads((security/'result.json').read_text())
assert d['status']=='passed' and d['source']==head and d['source_fingerprints']==fingerprints and d['findings']==1
assert len(d['steps'])==2 and all(x['exit_code']==0 and sha(security/(x['name']+'.log'))==x['log_sha256'] for x in d['steps'])
assert d['xcode_selected']=='/Applications/Xcode.app/Contents/Developer' and '6.3.3' in d['swift'] and '6.3.3' in d['extractor']
assert sha(security/'swift.sarif')==d['sarif_sha256'] and sha(r/'check-swift-codeql-replay.py')==d['script_sha256']
sarif=json.loads((security/'swift.sarif').read_text());findings=[f for run in sarif['runs'] for f in run.get('results',[])]
assert len(findings)==1 and findings[0]['ruleId']=='swift/weak-password-hashing'
db='Sources/SwiftDatabase/DatabaseConnection.swift';loc=findings[0]['locations'][0]['physicalLocation'];assert loc['artifactLocation']['uri']==db and loc['region']['startLine']==606
assert git('diff',base,head,'--',db)==''
extracted={loc['physicalLocation']['artifactLocation']['uri'] for run in sarif['runs'] for invocation in run.get('invocations',[]) for note in invocation.get('toolExecutionNotifications',[]) if note.get('descriptor',{}).get('id')=='swift/diagnostics/successfully-extracted-files' for loc in note.get('locations',[])}
assert loss in extracted
with zipfile.ZipFile(security/'database/src.zip') as z:
 matches=[n for n in z.namelist() if n.endswith('/source/'+loss)];assert len(matches)==1
 assert hashlib.sha256(z.read(matches[0])).hexdigest()==sha(s/loss)
worker=r/'ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker'
worker_receipt=Path(str(worker)+'.build.json');build=json.loads(worker_receipt.read_text())
assert build['source']['commit']==head and sha(worker)==build['binary_sha256']
assert all(sha(s/path)==digest for path,digest in build['source']['files'].items())
checks=['spec.md','production.patch','standards-review.md','spec-review.md','red-source-binding.json','controller-derivation.json','controller-launch-failure.json']
result=dict(status='passed',source=head,base=base,reused_prior_fix=prior,changed_files=[loss,test],native=reports,
 python_codeql_findings=0,swift_codeql_findings=1,swift_security='Completed matching6.3.3 analysis, actual loss extraction/archive bytes verified; one unchanged unsuppressed legacy PostgreSQL MD5 finding, not clean security',
 regression_policy='Passed unchanged policy; four strict Python Wampler failures remain failed',
 scope='Independent shared GPU loss correction and analytical regressions; public signatures, CPU fitting, dependencies and routing unchanged. No performance, convergence or general quality claim.',
 worker_receipt_sha256=sha(worker_receipt),worker_binary_sha256=sha(worker),records={name:sha(r/name) for name in checks},source_fingerprints=fingerprints,verifier_sha256=sha(Path(__file__)))
(r/'qualification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['native','records','source_fingerprints']},indent=2))
