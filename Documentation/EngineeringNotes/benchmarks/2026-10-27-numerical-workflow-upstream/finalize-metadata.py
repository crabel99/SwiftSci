from pathlib import Path
import hashlib, json, shutil, subprocess

r = Path(__file__).resolve().parent
s = r / 'source'
git = lambda *a: subprocess.check_output(['git', *a], cwd=s, text=True).strip()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
execution = 'c676a0acfca0274fe05e2dc72bf7a0b45ab9f5c9'
assert git('rev-parse', 'HEAD') == execution and git('status', '--porcelain') == ''
# Wait for every controller that fingerprints the README. The remaining Swift
# security import checks only unchanged Swift inputs from its completed build.
for name in ['compatibility/result.json', 'ci-bench/benchmarks-result.json', 'ci-security-python/security-python-result.json']:
    assert json.loads((r / name).read_text())['status'] == 'passed', name
assert 'Running TRAP import for CodeQL database' in (r / 'ci-security-swift633/database.log').read_text()
for tag in ['full-debug', 'full-release']:
    assert json.loads((r / ('native-' + tag) / 'tests.json').read_text())['exit_code'] == 0
main = json.loads((r / 'ci-main/main-result.json').read_text())
assert len(main['steps']) == 9 and all(x['exit_code'] == 0 for x in main['steps'][:8]) and main['steps'][8]['exit_code'] != 0
for source, target in [('source-head.txt', 'execution-head.txt'), ('source-reconciliation.json', 'execution-reconciliation.json'), ('production.patch', 'execution.patch')]:
    assert not (r / target).exists()
    shutil.copyfile(r / source, r / target)
doc = s / 'Examples/NumericalWorkflow/README.md'
text = doc.read_text()
needle = 'Missing or NaN features are imputed; infinite features and invalid labels need\ncorrection in the input.'
replacement = '''Each feature must have a numeric value within the CSV reader's first 1,000 data
rows so type inference can establish its numeric type. Entirely missing feature
columns, or columns whose first numeric value appears after that sample, are
rejected before imputation. Missing or NaN cells in numeric columns are imputed;
infinite features, invalid text and invalid labels need correction in the input.'''
assert text.count(needle) == 1
doc.write_text(text.replace(needle, replacement))
git('add', 'Examples/NumericalWorkflow/README.md')
git('commit', '--amend', '-m', 'feat: add a complete numerical workflow example')
head, base = git('rev-parse', 'HEAD'), git('rev-parse', 'HEAD^')
assert git('diff', '--name-only', execution, head) == 'Examples/NumericalWorkflow/README.md'
assert git('status', '--porcelain') == ''
files = git('diff', '--name-only', base, head).splitlines()
(r / 'source-head.txt').write_text(head + '\n')
(r / 'source-reconciliation.json').write_text(json.dumps(dict(head=head, base=base, files={n: sha(s / n) for n in files}), indent=2) + '\n')
(r / 'production.patch').write_bytes(subprocess.check_output(['git', 'diff', base, head], cwd=s))
receipt = dict(execution_head=execution, publication_head=head, changed_files=git('diff', '--name-only', execution, head).splitlines(), compiled_input_changes=[], reason='Clarify existing CSV inference contract and correct Conventional Commit subject; preserve original CI identities and recheck final documented command', controller_sha256=sha(Path(__file__)))
(r / 'metadata-clarification.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
