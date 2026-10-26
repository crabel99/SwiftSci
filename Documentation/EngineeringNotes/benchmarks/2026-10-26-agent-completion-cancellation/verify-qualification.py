from pathlib import Path
import hashlib, json, subprocess, zipfile
r=Path(__file__).resolve().parent; source=r/'source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
git=lambda *a:subprocess.check_output(['git',*a],cwd=source,text=True).strip()
head='0e1635199654ac6a20b32ea53eea0ffdfa39e747'
base='c4de6cc866fff6f52100535dbcb38dd708558200'
assert git('rev-parse','HEAD')==head and git('status','--porcelain')==''
subprocess.run(['git','merge-base','--is-ancestor',base,head],cwd=source,check=True)
fingerprints={str(p.relative_to(source)):sha(p) for folder in ['Sources','Tests'] for p in (source/folder).rglob('*.swift')}
reports={}
for mode in ['debug','release']:
 b=json.loads((r/f'native-full-{mode}/build.json').read_text());t=json.loads((r/f'native-full-{mode}/tests.json').read_text())
 assert b['exit_code']==t['exit_code']==0 and b['sources']==fingerprints
 s=t['summary'];assert s['totalTestCount']==s['passedTests']==1712 and s['failedTests']==s['skippedTests']==0 and t['strict_onnx_ci']
 reports[mode]={k:s[k] for k in ['totalTestCount','passedTests','failedTests','skippedTests']}
for name,count in [('ci-main/main-result.json',9),('ci-bench/benchmarks-result.json',19),('compatibility/result.json',3),('ci-security-python/security-python-result.json',2)]:
 d=json.loads((r/name).read_text());assert d['status']=='passed' and len(d['steps'])==count and all(i['exit_code']==0 for i in d['steps'])
 if 'source_fingerprints' in d:
  assert all(sha(source/path)==digest for path,digest in d['source_fingerprints'].items())
  assert all(d['source_fingerprints'].get(path)==digest for path,digest in fingerprints.items())
 if 'sources' in d: assert d['sources']==fingerprints
 if 'commit' in d: assert d['commit']==head
 for step in d['steps']:
  if 'log_sha256' in step: assert sha(Path(step['log']))==step['log_sha256']
 reports[name]=dict(sha256=sha(r/name),steps=count,status=d['status'])
python=json.loads((r/'ci-security-python/security-python-result.json').read_text());assert python['security_findings']['python']==0
policy=json.loads((r/'ci-bench/ci-acceptance/regression-policy.json').read_text())
assert policy['source']['commit']==head and policy['status']=='passed' and policy['conformance_status']=='failed' and not policy['blocking'] and len(policy['known_failures'])==4
assert all(i['engine']=='pandas' for i in policy['known_failures'])
for folder in ['SwiftDataFrame','SwiftPreprocessing','SwiftCluster','SwiftML']:
 assert git('diff',base,head,'--','Sources/'+folder)==''
for binding,log,test in [('red-binding.json','truncated-action-red.log','red-test.swift'),('cancellation-red-binding.json','cancellation-red.log','cancellation-red-test.swift')]:
 d=json.loads((r/binding).read_text());assert d['observed_exit_code']==1 and d['log_sha256']==sha(r/log) and d['test_source_sha256']==sha(r/test)
assert 'Test run with 42 tests in 5 suites passed' in (r/'agent-suite-final.log').read_text()
assert 'Test run with 7 tests' in (r/'cancellation-green.log').read_text()
assert 'Test run with 9 tests' in (r/'completion-green.log').read_text()
security=r/'ci-security-swift633-unsandboxed';s=json.loads((security/'result.json').read_text())
assert s['status']=='passed' and s['findings']==1 and s['source']==head and s['source_fingerprints']==fingerprints
assert len(s['steps'])==2 and all(i['exit_code']==0 and sha(security/(i['name']+'.log'))==i['log_sha256'] for i in s['steps'])
assert sha(security/'swift.sarif')==s['sarif_sha256']
sarif=json.loads((security/'swift.sarif').read_text())
extracted_uris={location['physicalLocation']['artifactLocation']['uri']
 for run in sarif['runs'] for invocation in run.get('invocations',[])
 for notification in invocation.get('toolExecutionNotifications',[])
 if notification.get('descriptor',{}).get('id')=='swift/diagnostics/successfully-extracted-files'
 for location in notification.get('locations',[])}
findings=[item for run in sarif['runs'] for item in run.get('results',[])]
assert len(findings)==1 and findings[0]['ruleId']=='swift/weak-password-hashing'
database_path='Sources/SwiftDatabase/DatabaseConnection.swift'
location=findings[0]['locations'][0]['physicalLocation']
assert location['artifactLocation']['uri']==database_path and location['region']['startLine']==606
assert git('diff',base,head,'--',database_path)==''
assert s['xcode_selected']=='/Applications/Xcode.app/Contents/Developer' and '6.3.3' in s['swift'] and '6.3.3' in s['extractor']
archive=security/'database/src.zip'
with zipfile.ZipFile(archive) as z:
 names=z.namelist();extracted={}
 for relative in ['Sources/SwiftAgent/ReActAgent.swift','Sources/SwiftLLM/Core/LLMModel.swift','Sources/SwiftLLM/Core/Generation.swift','Sources/SwiftLLM/Core/TransformerDecoder.swift']:
  assert relative in extracted_uris, relative
  matches=[n for n in names if n.endswith('/source/'+relative)]
  assert len(matches)==1,(relative,matches)
  assert hashlib.sha256(z.read(matches[0])).hexdigest()==sha(source/relative)
  extracted[relative]=sha(source/relative)
assert 'Unsupported' not in s.get('status','')
records=['production.patch','standards-review.md','spec-review.md','red-binding.json','cancellation-red-binding.json','completion-green.log','cancellation-green.log','agent-suite-final.log','cancellation-build-failure.log','agent-build-failure.log','check-swift-codeql.py','security-triage-review.md']
result=dict(status='passed',source=head,baseline=base,native=reports,python_codeql_findings=0,swift_codeql_findings=1,
 swift_security_result='Analysis completed; one retained pre-existing weak-password-hashing finding in PostgreSQL legacy MD5 authentication. Not a clean security result. Database policy follow-up remains open.',
 swift_security_scope='CodeQL2.27.3 Swift code-scanning suite with installed Swift6.3.3 compatibility compiler and disabled SwiftPM manifest sandbox; Xcode27 remains selected. Production source archive hashes verified.',
 swift_extracted_sources=extracted,swift_database_source_archive_sha256=sha(archive),swift_security_receipt_sha256=sha(security/'result.json'),
 swift_successfully_extracted_file_count=len(extracted_uris),
 regression_policy='passed; 400 strict passes and four unchanged Python Wampler failures among 404 executions',
 completion_scope='Optional rich-model refinement; exactly one final stop and normal stream end before parsing. Legacy text-only completion status remains unknown.',
 cancellation_scope='Consumer requests producer cancellation; cooperative model/tool work, no forceful interruption, rollback or guaranteed drain before cancelled run returns.',
 records={n:sha(r/n) for n in records},source_fingerprints=fingerprints,verifier_sha256=sha(Path(__file__)))
(r/'qualification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['native','source_fingerprints','records']},indent=2))
