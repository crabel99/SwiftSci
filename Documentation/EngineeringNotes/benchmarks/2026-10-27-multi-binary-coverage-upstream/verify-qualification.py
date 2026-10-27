from pathlib import Path
import hashlib
import json
import re
import subprocess
import zipfile

r = Path(__file__).resolve().parent
s = r / 'source'
head = '08486058190836df0a3b1916aa2cb633450a35fc'
base = '200d3935cc43396658a315bf4d5f745b6c7b496c'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda n: json.loads((r / n).read_text())
git = lambda *a: subprocess.check_output(['git', *a], cwd=s, text=True).strip()
assert git('rev-parse', 'HEAD') == head and git('rev-parse', 'HEAD^') == base
assert git('status', '--porcelain') == ''
changed = {'.github/workflows/ci.yml', 'scripts/export_coverage.py', 'scripts/tests/test_export_coverage.py'}
assert set(git('diff', '--name-only', base, head).splitlines()) == changed
assert git('diff', base, head, '--', 'Sources', 'Tests', 'Package.swift', 'Package.resolved', '.codecov.yml', 'Benchmarks') == ''
reconciliation = load('source-reconciliation.json')
assert reconciliation['head'] == head and reconciliation['base'] == base
assert set(reconciliation['files']) == changed
assert all(sha(s / n) == v for n, v in reconciliation['files'].items())
assert (r / 'production.patch').read_bytes() == subprocess.check_output(['git', 'diff', base, head], cwd=s)
fingerprints = {str(p.relative_to(s)): sha(p) for folder in ['Sources', 'Tests'] for p in (s / folder).rglob('*.swift')}
reports = {}

red = (r / 'regression-red-final-fixtures.log').read_text()
assert 'Ran 8 tests' in red and 'FAILED (failures=8)' in red
for name in ['regression-green-2.log', 'regression-python39.log']:
    text = (r / name).read_text()
    assert 'Ran 13 tests' in text and text.rstrip().endswith('OK') and 'skipped' not in text
predecessor = load('red-reproducible/result.json')
assert predecessor['source'] == head and predecessor['predecessor'] == base and predecessor['exit_code'] == 1 and predecessor['tests'] == predecessor['failures'] == 8
assert predecessor['test_sha256'] == sha(s / 'scripts/tests/test_export_coverage.py') and predecessor['controller_sha256'] == sha(r / 'reproduce-predecessor.py')
assert predecessor['log_sha256'] == sha(r / 'red-reproducible/tests.log')
assert predecessor['predecessor_workflow_sha256'] == hashlib.sha256(subprocess.check_output(['git', 'show', base + ':.github/workflows/ci.yml'], cwd=s)).hexdigest()
reports['regressions'] = dict(before_failures=8, after_passes=13, python39_passes=13, predecessor_receipt_sha256=sha(r / 'red-reproducible/result.json'))
old = load('baseline-original-order/result.json')
assert old['exit_code'] == 0 and not old['source_modules_present']['SwiftAgent']
assert old['source_modules_present']['SwiftDataFrame'] and len(old['command']) == 20
assert load('baseline-reproduction-known-path/result.json')['source_modules_present']['SwiftAgent']

def walk(x):
    if isinstance(x, dict):
        yield x
        for value in x.values():
            yield from walk(value)
    elif isinstance(x, list):
        for value in x:
            yield from walk(value)

for tag in ['full-debug', 'full-release']:
    folder = r / ('native-' + tag)
    b, t = load('native-' + tag + '/build.json'), load('native-' + tag + '/tests.json')
    assert b['exit_code'] == t['exit_code'] == 0 and b['sources'] == fingerprints and t['strict_onnx_ci']
    actual = json.loads(subprocess.check_output(['xcrun', 'xcresulttool', 'get', 'test-results', 'summary', '--path', str(folder / 'tests.xcresult'), '--format', 'json'], text=True))
    assert all(actual[k] == t['summary'][k] for k in ['totalTestCount', 'passedTests', 'failedTests', 'skippedTests'])
    assert actual['totalTestCount'] == actual['passedTests'] == 1713 and actual['failedTests'] == actual['skippedTests'] == 0
    tree = json.loads(subprocess.check_output(['xcrun', 'xcresulttool', 'get', 'test-results', 'tests', '--path', str(folder / 'tests.xcresult'), '--format', 'json'], text=True))
    (folder / 'actual-test-tree.json').write_text(json.dumps(tree, indent=2) + '\n')
    for module, count in [('SwiftAgentTests', 62), ('SwiftNLPTests', 161)]:
        cases = [n for n in walk(tree) if n.get('nodeType') == 'Test Case' and '/' + module + '/' in n.get('nodeIdentifierURL', '')]
        assert len(cases) == count and all(n['result'] == 'Passed' for n in cases)
    reports[tag] = dict(tests=actual['totalTestCount'], failed=0, skipped=0, receipt_sha256=sha(folder / 'tests.json'), tree_sha256=sha(folder / 'actual-test-tree.json'))
assert reports['full-debug']['tests'] == reports['full-release']['tests']

for name, count in [('ci-main/main-result.json', 9), ('ci-bench/benchmarks-result.json', 19), ('compatibility/result.json', 3), ('ci-security-python/security-python-result.json', 2)]:
    d = load(name)
    assert d['status'] == 'passed' and len(d['steps']) == count and all(x['exit_code'] == 0 for x in d['steps'])
    if 'commit' in d:
        assert d['commit'] == head and d['initial_git_status'] == d['final_git_status'] == ''
        controller = 'benchmark-ci-runner.py' if name.startswith('ci-bench') else 'full-ci-runner.py'
        assert d['runner_sha256'] == sha(r / controller)
        assert all(sha(s / '.github/workflows' / n) == v for n, v in d['workflows'].items())
    if 'sources' in d:
        assert d['sources'] == fingerprints
    if 'source_fingerprints' in d:
        assert all(sha(s / n) == v for n, v in d['source_fingerprints'].items())
        assert all(d['source_fingerprints'].get(n) == v for n, v in fingerprints.items())
    for step in d['steps']:
        if 'log_sha256' in step:
            assert sha(Path(step['log'])) == step['log_sha256']
    reports[name] = dict(steps=count, sha256=sha(r / name))
assert 'Swift version 6.3.3' in load('compatibility/result.json')['swift']
assert 'Ran 13 tests' in (r / 'ci-main/main-07-test-documentation-reporting.log').read_text()
assert load('ci-security-python/security-python-result.json')['security_findings']['python'] == 0

coverage = r / 'ci-main/coverage.lcov'
modules = {'SwiftAgent', 'SwiftDataFrame', 'SwiftNLP'}
records, hits = {m: 0 for m in modules}, {m: 0 for m in modules}
current = None
for line in coverage.read_text().splitlines():
    if line.startswith('SF:'):
        current = next((m for m in modules if '/Sources/' + m + '/' in line), None)
        if current:
            records[current] += 1
    elif line.startswith('DA:') and current and int(line.split(',')[1]) > 0:
        hits[current] += 1
    elif line == 'end_of_record':
        current = None
assert all(records[m] > 0 and hits[m] > 0 for m in modules)
build = (s / '.build/debug').resolve()
binaries = sorted(p / 'Contents/MacOS' / p.stem for p in build.glob('*.xctest'))
assert len(binaries) == 15 and all(p.is_file() for p in binaries)
reports['coverage'] = dict(sha256=sha(coverage), records=records, executed_lines=hits, profile_sha256=sha(s / '.build/debug/codecov/default.profdata'), objects={str(p): sha(p) for p in binaries}, scope='Actual final-head safe-test workflow export; no supplemental export is used as a substitute')

policy = load('ci-bench/ci-acceptance/regression-policy.json')
acceptance = load('ci-bench/ci-acceptance/acceptance.json')
assert policy['source']['commit'] == head and policy['status'] == 'passed' and not policy['blocking']
assert acceptance['coverage_complete'] and sum(p['engine_cases'] for p in acceptance['profiles']) == 404
assert sum(p['passed'] for p in acceptance['profiles']) == 400 and sum(len(p['failures']) for p in acceptance['profiles']) == 4
assert sha(r / 'ci-bench/ci-acceptance/acceptance.json') == policy['acceptance_sha256']
assert policy['conformance_status'] == 'failed' and len(policy['known_failures']) == 4 and all(f['engine'] == 'pandas' for f in policy['known_failures'])
worker = r / 'ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker'
build = json.loads(Path(str(worker) + '.build.json').read_text())
assert build['source']['commit'] == head and sha(worker) == build['binary_sha256'] and all(sha(s / n) == v for n, v in build['source']['files'].items())
reports['benchmarks'] = dict(engine_cases=404, strict_pass=400, known_strict_failures=4, worker_source_files=len(build['source']['files']), worker_sha256=sha(worker))

security = r / 'ci-security-swift633'
d = load('ci-security-swift633/result.json')
assert d['status'] == 'passed' and d['source'] == head and d['source_fingerprints'] == fingerprints and d['findings'] == 1 and len(d['steps']) == 2
assert all(step['exit_code'] == 0 and sha(security / (step['name'] + '.log')) == step['log_sha256'] for step in d['steps'])
assert d['xcode_selected'] == '/Applications/Xcode.app/Contents/Developer' and '6.3.3' in d['swift'] and '6.3.3' in d['extractor']
assert sha(security / 'swift.sarif') == d['sarif_sha256'] and sha(r / 'check-swift-codeql-replay.py') == d['script_sha256']
assert re.search(r'Number of unresolved AST nodes\s*\|\s*0\s*\|', (security / 'analysis.log').read_text())
sarif = load('ci-security-swift633/swift.sarif')
findings = [f for run in sarif['runs'] for f in run.get('results', [])]
assert len(findings) == 1 and findings[0]['ruleId'] == 'swift/weak-password-hashing' and not findings[0].get('suppressions')
location = findings[0]['locations'][0]['physicalLocation']
assert location['artifactLocation']['uri'] == 'Sources/SwiftDatabase/DatabaseConnection.swift' and location['region']['startLine'] == 606
assert all(inv.get('executionSuccessful') for run in sarif['runs'] for inv in run.get('invocations', []))
extracted = {loc['physicalLocation']['artifactLocation']['uri'] for run in sarif['runs'] for inv in run.get('invocations', []) for note in inv.get('toolExecutionNotifications', []) if note.get('descriptor', {}).get('id') == 'swift/diagnostics/successfully-extracted-files' for loc in note.get('locations', [])}
assert len(extracted) == 350 and sum(n.startswith('Sources/') for n in extracted) == 290 and sum(n.startswith('Benchmarks/') for n in extracted) == 59 and 'Package.swift' in extracted
with zipfile.ZipFile(security / 'database/src.zip') as archive:
    for name in sorted(extracted):
        members = [n for n in archive.namelist() if n.endswith('/source/' + name)]
        assert len(members) == 1 and hashlib.sha256(archive.read(members[0])).hexdigest() == sha(s / name)
(r / 'security-extraction.json').write_text(json.dumps(dict(source=head, files={n: sha(s / n) for n in sorted(extracted)}, sarif_sha256=sha(security / 'swift.sarif')), indent=2) + '\n')
reports['swift-security'] = dict(extracted=350, findings=1, sha256=sha(security / 'result.json'))
assert load('cache-preparation.json')['status'] == 'passed'
assert git('status', '--porcelain') == '' and subprocess.check_output(['xcode-select', '-p'], text=True).strip() == '/Applications/Xcode.app/Contents/Developer'
result = dict(status='passed', source=head, base=base, files=3, commits=1, reports=reports, verifier_sha256=sha(Path(__file__)), limits=['This establishes local workflow coverage export, not hosted Codecov acceptance or full branch coverage.', 'Four known pandas Wampler strict failures and one unchanged unsuppressed legacy MD5 finding remain.', 'Known concurrent MLX cold-start hazard remains open; stored old local embeddings still require regeneration.'])
(r / 'qualification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
