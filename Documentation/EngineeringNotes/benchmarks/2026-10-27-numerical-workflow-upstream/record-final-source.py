from pathlib import Path
import hashlib, json, subprocess
r = Path(__file__).resolve().parent
s = r / 'source'
git = lambda *a: subprocess.check_output(['git', *a], cwd=s, text=True).strip()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
head, base = git('rev-parse', 'HEAD'), git('rev-parse', 'HEAD^')
execution = (r / 'execution-head.txt').read_text().strip()
assert not git('status', '--porcelain')
assert git('diff', '--name-only', execution, head) == 'Examples/NumericalWorkflow/README.md'
files = git('diff', '--name-only', base, head).splitlines()
(r / 'source-head.txt').write_text(head + '\n')
(r / 'source-reconciliation.json').write_text(json.dumps(dict(head=head, base=base, files={n: sha(s / n) for n in files}), indent=2) + '\n')
(r / 'production.patch').write_bytes(subprocess.check_output(['git', 'diff', base, head], cwd=s))
receipt = dict(execution_head=execution, publication_head=head, changed_files=['Examples/NumericalWorkflow/README.md'], compiled_input_changes=[], reason='Documentation-only corrections: CSV inference contract, supported Xcode Metal build command, Conventional Commit subject. Original CI identities preserved.', prior_documentation_head='01bb6f39d5f503ef597234f0045fb86cf2ce7a0a', controller_sha256=sha(Path(__file__)))
(r / 'metadata-clarification.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(head)
