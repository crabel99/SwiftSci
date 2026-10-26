from pathlib import Path
import hashlib,json,subprocess
root=Path(__file__).resolve().parent
source=root/'source'
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
status=subprocess.check_output(['git','status','--porcelain'],cwd=source,text=True)
assert not status
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for name in ('commit','qualified-commit'):
 p=root/'verification'/f'{name}.json'
 d=json.loads(p.read_text());assert d['commit']==head
 d['source_worktree_clean']=True
 if name=='qualified-commit':
  d['swift633']['safe_xctest']=77
  bindings={}
  for mode in ('debug','release'):
   pbuild=root/f'native-{mode}/build.json';build=json.loads(pbuild.read_text())
   assert build['exit_code']==0
   for rel,digest in build['sources'].items():assert sha(source/rel)==digest,rel
   bindings[mode]={'build_receipt_sha256':sha(pbuild),'source_hashes_match_final_commit':True}
  proof=root/'verification/public-candidate/proof.json'
  probe=json.loads(proof.read_text())
  assert sha(root/'native-release/build.log')==probe['input_build_log_sha256']
  assert sha(root/'verification/public-candidate/probe')==probe['binary_sha256']
  d['candidate_binding']={'native':bindings,'public_probe_receipt_sha256':sha(proof),'public_workflow_summary_sha256':sha(root/'verification/public-workflow/summary.json'),'candidate_binary_sha256':probe['binary_sha256'],'original_object_files_may_have_been_rebuilt':True}
  d['scope']={'full_github_workflows_replicated_locally':False,'local_swift_codeql_pass_claimed':False,'new_upstream_pr_created':False,'xcode_27_remains_selected':True,'gpu_gradient_cause':'inference, not independently proven'}
 p.write_text(json.dumps(d,indent=2)+'\n')
print('Bound final clean commit and public probe to saved native build receipts:',head)
