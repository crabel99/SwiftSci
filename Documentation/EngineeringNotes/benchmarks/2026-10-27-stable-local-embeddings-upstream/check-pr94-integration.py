from pathlib import Path
import hashlib,json,subprocess
r=Path(__file__).resolve().parent;s=r/'source';git=lambda *a:subprocess.check_output(['git',*a],cwd=s,text=True).strip()
head=git('rev-parse','HEAD');dependency='a9732e04f5c5ca16fc6aadf39d0707fe85721246';tree=git('merge-tree','--write-tree',dependency,head);assert len(tree)==40
expected={'Benchmarks/Python/requirements-gguf.txt','Benchmarks/Python/requirements-llm.txt'}
assert set(git('diff','--name-only',head,tree).splitlines())==expected
assert git('diff',head,tree,'--','Sources','Tests','.github/workflows','Package.swift','Package.resolved','.codecov.yml','Benchmarks/Python/requirements-comparison.txt')==''
for name in expected:assert git('rev-parse',tree+':'+name)==git('rev-parse',dependency+':'+name)
report=dict(status='clean_merge_verified',source=head,dependency_head=dependency,combined_tree=tree,only_differences_from_qualified_source=sorted(expected),source_and_test_and_workflow_bytes_identical=True,controller_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Actual Git three-way merge tree preserves PR94 requirements and exact candidate Swift/tests/workflows. This is source integration proof, not a separate full runtime or GGUF/LLM-model qualification of the combined tree.')
(r/'pr94-integration.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
