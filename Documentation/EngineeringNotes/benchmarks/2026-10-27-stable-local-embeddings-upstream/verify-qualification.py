from pathlib import Path
import hashlib,json,re,subprocess,zipfile
r=Path(__file__).resolve().parent;s=r/'source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda n:json.loads((r/n).read_text())
git=lambda *a:subprocess.check_output(['git',*a],cwd=s,text=True).strip()
head='3012a6e52d70306a9437fb8cd8af4343a41560dd';base='01d48cbcd940c886546b2bb8d6b177d9b7a0e277'
assert git('rev-parse','HEAD')==head and git('rev-parse','HEAD^')==base and git('status','--porcelain')==''
rec=load('source-reconciliation.json');files={row['path'] for row in rec['files']};assert len(files)==3 and set(git('diff','--name-only',base,head).splitlines())==files
for row in rec['files']:assert sha(s/row['path'])==row['sha256']
assert (r/'production.patch').read_bytes()==subprocess.check_output(['git','diff',base,head],cwd=s)
assert git('diff',base,head,'--','Package.swift','Package.resolved','.codecov.yml','.github/workflows','Benchmarks','scripts')==''
fingerprints={str(p.relative_to(s)):sha(p) for folder in ['Sources','Tests'] for p in (s/folder).rglob('*.swift')};reports={}
engine='Sources/SwiftNLP/Core/LocalEmbeddingEngine.swift';old_engine=hashlib.sha256(subprocess.check_output(['git','show',base+':'+engine],cwd=s)).hexdigest()
assert subprocess.check_output(['git','show','a9732e04f5c5ca16fc6aadf39d0707fe85721246:'+engine],cwd=s)==subprocess.check_output(['git','show',base+':'+engine],cwd=s)
old=load('baseline-repro/result.json');fresh=load('fixed-final-processes/result.json');failure=load('classification-failure.json')
assert old['source']==base and old['runs']==old['unique_vectors']==40 and old['source_sha256'][engine]==old_engine
assert fresh['source']==head and fresh['runs']==fresh['golden_passes']==100 and fresh['unique_vectors']==1 and fresh['predictions']=={'technology':100,'food':0}
assert fresh['controller_sha256']==sha(r/'reproduce.py') and fresh['probe_sha256']==sha(r/'probe.swift') and fresh['binary_sha256']==sha(r/'fixed-final-processes/probe')
assert all(sha(s/name)==v for name,v in fresh['source_sha256'].items())
outputs=load('fixed-final-processes/outputs.json');assert len(outputs)==100 and len({json.dumps(d['vector']) for d in outputs})==1 and all(d['prediction']=='technology' and d['golden'][5]==-1 and sum(abs(x) for x in d['golden'])==1 for d in outputs)
assert failure['status']=='reproduced' and failure['runs']==55 and failure['first_failure']['output']['prediction']=='food' and failure['binary_sha256']==old['binary_sha256']==sha(r/'baseline-repro/probe') and failure['controller_sha256']==sha(r/'reproduce-failure.py')
for tag,expected_exit,digest in [('red-coordinates-xctest',1,old_engine),('green-coordinates-xctest',0,sha(s/engine))]:
 d=load(tag+'/result.json');assert d['exit_code']==expected_exit and d['production_sha256']==digest and d['test_sha256']==sha(s/'Tests/SwiftNLPTests/LocalEmbeddingEngineTests.swift') and d['log_sha256']==sha(r/tag/'tests.log') and d['controller_sha256']==sha(r/'test-stable-coordinates.py')
 log=(r/tag/'tests.log').read_text();assert ('Executed 5 tests, with '+('7' if expected_exit else '0')+' failures') in log
 if expected_exit:assert 'testEmbeddingsUseStableHashCoordinates' in log and 'XCTAssertEqual failed' in log
 reports[tag]=dict(exit_code=expected_exit,tests=5,failures=7 if expected_exit else 0,sha256=sha(r/tag/'result.json'))
integration=load('pr94-integration.json');assert integration['source']==head and integration['controller_sha256']==sha(r/'check-pr94-integration.py') and integration['source_and_test_and_workflow_bytes_identical']
assert git('merge-tree','--write-tree',integration['dependency_head'],head)==integration['combined_tree']
assert set(git('diff','--name-only',head,integration['combined_tree']).splitlines())==set(integration['only_differences_from_qualified_source'])=={'Benchmarks/Python/requirements-gguf.txt','Benchmarks/Python/requirements-llm.txt'}
for name,digest in load('setup-failures.json')['files'].items():assert sha(r/name)==digest
# Re-read actual native result bundles, retain exported trees for package inspection.
for tag in ['full-debug','full-release']:
 folder=r/('native-'+tag);b=load('native-'+tag+'/build.json');t=load('native-'+tag+'/tests.json')
 assert b['exit_code']==t['exit_code']==0 and b['sources']==fingerprints and t['strict_onnx_ci']
 actual=json.loads(subprocess.check_output(['xcrun','xcresulttool','get','test-results','summary','--path',str(folder/'tests.xcresult'),'--format','json'],text=True))
 assert all(actual[k]==t['summary'][k] for k in ['totalTestCount','passedTests','failedTests','skippedTests'])
 assert actual['totalTestCount']==actual['passedTests']==1673 and actual['failedTests']==actual['skippedTests']==0
 tree=json.loads(subprocess.check_output(['xcrun','xcresulttool','get','test-results','tests','--path',str(folder/'tests.xcresult'),'--format','json'],text=True));(folder/'actual-test-tree.json').write_text(json.dumps(tree,indent=2)+'\n')
 def walk(x):
  if isinstance(x,dict):
   yield x
   for v in x.values():yield from walk(v)
  elif isinstance(x,list):
   for v in x:yield from walk(v)
 nlp=[n for n in walk(tree) if n.get('nodeType')=='Test Case' and '/SwiftNLPTests/' in n.get('nodeIdentifierURL','')]
 assert len(nlp)==161 and all(n['result']=='Passed' for n in nlp)
 for method in ['LocalEmbeddingEngineTests/testEmbeddingsUseStableHashCoordinates','ZeroShotTextClassifierTests/testZeroShotWithLocalEmbeddingEngine']:
  assert any(method in n.get('nodeIdentifierURL','') for n in nlp),method
 reports[tag]=dict(tests=1673,nlp_tests=len(nlp),failed=0,skipped=0,receipt_sha256=sha(folder/'tests.json'),tree_sha256=sha(folder/'actual-test-tree.json'))
for name,count in [('ci-main/main-result.json',9),('ci-bench/benchmarks-result.json',19),('compatibility/result.json',4),('ci-security-python/security-python-result.json',2)]:
 d=load(name);assert len(d['steps'])==count
 if name.startswith('ci-main'):
  assert all(x['exit_code']==0 for x in d['steps'][:8]) and d['steps'][8]['exit_code']==1
 else:assert d['status']=='passed' and all(x['exit_code']==0 for x in d['steps'])
 if 'commit' in d:
  assert d['commit']==head and d['initial_git_status']==''
  if 'final_git_status' in d:assert d['final_git_status']==''
  controller='benchmark-ci-runner.py' if name.startswith('ci-bench') else 'full-ci-runner.py'
  assert d['runner_sha256']==sha(r/controller)
  assert all(sha(s/'.github/workflows'/n)==v for n,v in d['workflows'].items())
 if 'sources' in d:assert d['sources']==fingerprints
 if 'source_fingerprints' in d:
  assert all(sha(s/n)==v for n,v in d['source_fingerprints'].items()) and all(d['source_fingerprints'].get(n)==v for n,v in fingerprints.items())
 for step in d['steps']:
  if 'log_sha256' in step:assert sha(Path(step['log']))==step['log_sha256']
 reports[name]=dict(steps=count,workflow_steps_passed=8 if name.startswith('ci-main') else count,sha256=sha(r/name))
compat=load('compatibility/result.json');assert 'Swift version 6.3.3' in compat['swift']
focused=(r/'compatibility/focused-nlp-tests.log').read_text();assert 'LocalEmbeddingEngineTests' in focused and 'testEmbeddingsUseStableHashCoordinates' in focused and 'ZeroShotTextClassifierTests' in focused and 'testZeroShotWithLocalEmbeddingEngine' in focused and 'Executed 12 tests, with 0 failures' in focused and 'Test run with 149 tests in 24 suites passed' in focused
safe=(r/'ci-main/main-03-run-safe-unit-tests.log').read_text();assert 'testEmbeddingsUseStableHashCoordinates' in safe and 'testZeroShotWithLocalEmbeddingEngine' in safe
cov=load('nlp-coverage.json');supp=load('coverage-supplement/result.json')
assert cov['source']==supp['source']==head and cov['source_sha256']==sha(s/cov['path'])
assert cov['controller_sha256']==sha(r/'verify-nlp-coverage.py') and supp['controller_sha256']==sha(r/'export-agent-coverage.py')
assert supp['exit_code']==0 and supp['main_receipt_sha256']==sha(r/'ci-main/main-result.json') and supp['safe_test_log_sha256']==sha(r/'ci-main/main-03-run-safe-unit-tests.log')
assert supp['coverage_sha256']==cov['coverage_sha256']==sha(r/'coverage-supplement/coverage.lcov') and supp['log_sha256']==sha(r/'coverage-supplement/export.log')
assert all(sha(Path(n))==v for n,v in supp['objects'].items()) and sha(s/'.build/debug/codecov/default.profdata')==supp['profile_sha256']
assert cov['added_executable_lines']==cov['covered_added_executable_lines']>0 and cov['executed_embedding_functions']>0
reports['coverage']=dict(added_executable_lines=cov['added_executable_lines'],covered=cov['covered_added_executable_lines'],original_workflow_export_omits_agent=True,supplement_sha256=sha(r/'coverage-supplement/result.json'))
assert load('ci-security-python/security-python-result.json')['security_findings']['python']==0
policy=load('ci-bench/ci-acceptance/regression-policy.json');assert policy['source']['commit']==head and policy['status']=='passed' and not policy['blocking']
acceptance=load('ci-bench/ci-acceptance/acceptance.json');assert acceptance['coverage_complete'] and sum(p['engine_cases'] for p in acceptance['profiles'])==404 and sum(p['passed'] for p in acceptance['profiles'])==400 and sum(len(p['failures']) for p in acceptance['profiles'])==4
assert sha(r/'ci-bench/ci-acceptance/acceptance.json')==policy['acceptance_sha256']
assert policy['conformance_status']=='failed' and len(policy['known_failures'])==4 and all(f['engine']=='pandas' for f in policy['known_failures'])
security=r/'ci-security-swift633';d=load('ci-security-swift633/result.json')
assert d['status']=='passed' and d['source']==head and d['source_fingerprints']==fingerprints and d['findings']==1 and len(d['steps'])==2
assert all(step['exit_code']==0 and sha(security/(step['name']+'.log'))==step['log_sha256'] for step in d['steps'])
assert d['xcode_selected']=='/Applications/Xcode.app/Contents/Developer' and '6.3.3' in d['swift'] and '6.3.3' in d['extractor']
assert sha(security/'swift.sarif')==d['sarif_sha256'] and sha(r/'check-swift-codeql-replay.py')==d['script_sha256']
assert re.search(r'Number of unresolved AST nodes\s*\|\s*0\s*\|',(security/'analysis.log').read_text())
sarif=load('ci-security-swift633/swift.sarif');findings=[f for run in sarif['runs'] for f in run.get('results',[])]
assert len(findings)==1 and findings[0]['ruleId']=='swift/weak-password-hashing' and not findings[0].get('suppressions')
loc=findings[0]['locations'][0]['physicalLocation'];assert loc['artifactLocation']['uri']=='Sources/SwiftDatabase/DatabaseConnection.swift' and loc['region']['startLine']==606
assert all(inv.get('executionSuccessful') for run in sarif['runs'] for inv in run.get('invocations',[]))
extracted={loc['physicalLocation']['artifactLocation']['uri'] for run in sarif['runs'] for inv in run.get('invocations',[]) for note in inv.get('toolExecutionNotifications',[]) if note.get('descriptor',{}).get('id')=='swift/diagnostics/successfully-extracted-files' for loc in note.get('locations',[])}
assert len(extracted)==350 and sum(n.startswith('Sources/') for n in extracted)==290 and sum(n.startswith('Benchmarks/') for n in extracted)==59 and 'Package.swift' in extracted
with zipfile.ZipFile(security/'database/src.zip') as archive:
 for name in sorted(extracted):
  members=[n for n in archive.namelist() if n.endswith('/source/'+name)];assert len(members)==1 and hashlib.sha256(archive.read(members[0])).hexdigest()==sha(s/name)
(r/'security-extraction.json').write_text(json.dumps(dict(source=head,files={n:sha(s/n) for n in sorted(extracted)},sarif_sha256=sha(security/'swift.sarif')),indent=2)+'\n')
reports['swift-security']=dict(extracted=350,sources=290,benchmarks=59,manifest=1,findings=1,sha256=sha(security/'result.json'))
worker=r/'ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker';build=json.loads(Path(str(worker)+'.build.json').read_text());assert build['source']['commit']==head and sha(worker)==build['binary_sha256'] and all(sha(s/n)==v for n,v in build['source']['files'].items())
reports['benchmarks']=dict(engine_cases=404,strict_pass=400,known_strict_failures=4,worker_source_files=len(build['source']['files']),worker_sha256=sha(worker))
assert load('cache-preparation.json')['status']=='passed'
assert git('status','--porcelain')=='' and subprocess.check_output(['xcode-select','-p'],text=True).strip()=='/Applications/Xcode.app/Contents/Developer'
result=dict(status='passed',source=head,base=base,files=3,commits=1,reports=reports,verifier_sha256=sha(Path(__file__)),limits=['Original 8 main workflow steps passed; ninth local guard still exposes the existing agent coverage omission. A separate explicit-object export measures local NLP coverage, not a hosted workflow repair.','Stored LocalEmbeddingEngine vectors/indexes from the old randomized mapping must be regenerated; this is not a trained semantic model.','Four known pandas Wampler strict failures and one unchanged unsuppressed legacy MD5 finding remain.','Known concurrent MLX cold-start hazard remains open.'])
(r/'qualification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
