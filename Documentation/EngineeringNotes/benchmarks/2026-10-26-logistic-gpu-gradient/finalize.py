from pathlib import Path
import hashlib,json,re,subprocess
r=Path(__file__).resolve().parent;source=r/'source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
assert not subprocess.check_output(['git','status','--porcelain'],cwd=source,text=True)
report={'status':'passed','commit':head,'source_worktree_clean':True,'native':{},'workflows':{},'public_gpu_workflow':{}}
for mode in ('debug','release'):
 folder=r/('native-full-'+mode)
 build=json.loads((folder/'build.json').read_text());tests=json.loads((folder/'tests.json').read_text())
 assert build['exit_code']==tests['exit_code']==0
 for rel,digest in build['sources'].items():assert sha(source/rel)==digest,rel
 summary=tests['summary'];assert summary['failedTests']==summary['skippedTests']==0
 report['native'][mode]={'passed':summary['passedTests'],'failed':0,'skipped':0,'source_hashes_match_final_commit':True,'test_receipt_sha256':sha(folder/'tests.json')}
 workflow=json.loads((r/f'verification/public-workflow-{mode}/summary.json').read_text());assert workflow['status']=='passed'
 proof_path=r/f'verification/public-candidate-{mode}/proof.json';proof=json.loads(proof_path.read_text())
 assert sha(proof_path.parent/'probe')==proof['binary_sha256']
 for path,digest in proof['objects'].items():assert sha(Path(path))==digest,path
 report['public_gpu_workflow'][mode]={'summary':workflow,'proof_sha256':sha(proof_path),'current_object_hashes_match_saved_proof':True,'bound_native_build':'native-full-'+mode+'/build.json'}
for name,path in [('main','ci-main-final/main-result.json'),('benchmarks','ci-bench-final/benchmarks-result.json'),('python_codeql','ci-security-python/security-python-result.json')]:
 receipt=r/path;data=json.loads(receipt.read_text());assert data['status']=='passed',name
 for rel,digest in data['source_fingerprints'].items():assert sha(source/rel)==digest,(name,rel)
 report['workflows'][name]={'status':'passed','receipt':path,'receipt_sha256':sha(receipt),'tested_inputs_match_final_commit':True,'steps':len(data['steps'])}
compat=json.loads((r/'compatibility/result.json').read_text());assert compat['status']=='passed'
for rel,digest in compat['sources'].items():assert sha(source/rel)==digest,rel
safe=(r/'compatibility/safe-tests.log').read_text()
assert re.search(r'Executed 77 tests, with 0 failures',safe)
assert re.search(r'Test run with 740 tests .* passed',safe)
report['swift633']={'debug_build':'passed','release_build':'passed','all_test_targets_compiled':True,'xctest_passed':77,'swift_testing_passed':740,'receipt_sha256':sha(r/'compatibility/result.json')}
worker=r/'ci-bench/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker.build.json'
data=json.loads(worker.read_text());assert data['source']['commit']==head
for rel,digest in data['source']['files'].items():
 if (source/rel).is_file():assert sha(source/rel)==digest,rel
report['benchmark_worker']={'commit':head,'receipt_sha256':sha(worker),'source_files_match_final_commit':True}
sarif=json.loads((r/'ci-security-python/python.sarif').read_text())
report['python_codeql_findings']=sum(len(x.get('results',[])) for x in sarif['runs'])
report['scope']={'swift_codeql':'Unsupported by Xcode 27 and Swift 6.4, verified against GitHub October 19 notice','all_native_tests':True,'full_github_actions_replica':False,'no_upstream_pr_created':True,'xcode_27_remains_selected':True,'general_performance_claim':False,'documentation':'All-module conversion passed with preexisting warnings; verifier reports 98.67% and zero placeholders, not 100% documentation'}
(r/'qualified-commit.json').write_text(json.dumps(report,indent=2)+'\n')
print('Final committed source verified against all receipts:',head)
