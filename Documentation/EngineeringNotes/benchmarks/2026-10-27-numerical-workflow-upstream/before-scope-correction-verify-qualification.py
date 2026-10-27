from pathlib import Path
import hashlib
import json
import re
import subprocess
import zipfile

r = Path(__file__).resolve().parent
s = r / 'source'
head = (r / 'source-head.txt').read_text().strip()
execution_head = 'c676a0acfca0274fe05e2dc72bf7a0b45ab9f5c9'
base = '200d3935cc43396658a315bf4d5f745b6c7b496c'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda n: json.loads((r / n).read_text())
git = lambda *a: subprocess.check_output(['git', *a], cwd=s, text=True).strip()
assert git('rev-parse', 'HEAD') == head and git('rev-parse', 'HEAD^') == base
assert git('status', '--porcelain') == ''
changed = {'Package.swift', 'README.md', 'Examples/NumericalWorkflow/Data/sample.csv', 'Examples/NumericalWorkflow/README.md', 'Examples/NumericalWorkflow/ScientificWorkflow.swift', 'Examples/NumericalWorkflow/verify.py'}
assert set(git('diff', '--name-only', base, head).splitlines()) == changed
assert git('diff', base, head, '--', 'Sources', 'Tests', 'Package.resolved', '.codecov.yml', 'Benchmarks', '.github', 'scripts') == ''
reconciliation = load('source-reconciliation.json')
assert reconciliation['head'] == head and reconciliation['base'] == base
assert set(reconciliation['files']) == changed
assert all(sha(s / n) == v for n, v in reconciliation['files'].items())
assert (r / 'production.patch').read_bytes() == subprocess.check_output(['git', 'diff', base, head], cwd=s)
fingerprints = {str(p.relative_to(s)): sha(p) for folder in ['Sources', 'Tests', 'Examples'] for p in (s / folder).rglob('*.swift')}
reports = {}
assert (r / 'execution-head.txt').read_text().strip() == execution_head
execution = load('execution-reconciliation.json')
assert execution['head'] == execution_head and execution['base'] == base
assert set(execution['files']) == changed
assert all(hashlib.sha256(subprocess.check_output(['git', 'show', execution_head + ':' + n], cwd=s)).hexdigest() == v for n, v in execution['files'].items())
assert (r / 'execution.patch').read_bytes() == subprocess.check_output(['git', 'diff', base, execution_head], cwd=s)
clarification = load('metadata-clarification.json')
assert clarification['execution_head'] == execution_head and clarification['publication_head'] == head
assert clarification['changed_files'] == ['Examples/NumericalWorkflow/README.md']
assert clarification['compiled_input_changes'] == []
assert clarification['controller_sha256'] == sha(r / 'record-final-source.py')

# Retain original execution identity after a documentation-only clarification.
assert git('diff', '--name-only', execution_head, head) == 'Examples/NumericalWorkflow/README.md'
assert git('diff', execution_head, head, '--', 'Package.swift', 'Package.resolved', 'Sources', 'Tests', 'Benchmarks', 'scripts', '.github', '.codecov.yml', 'Examples/NumericalWorkflow/ScientificWorkflow.swift', 'Examples/NumericalWorkflow/verify.py', 'Examples/NumericalWorkflow/Data/sample.csv') == ''
def recorded_match(name, digest):
    original = subprocess.check_output(['git', 'show', execution_head + ':' + name], cwd=s)
    assert hashlib.sha256(original).hexdigest() == digest, name
    return name == 'Examples/NumericalWorkflow/README.md' or sha(s / name) == digest


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
    assert len(d['steps']) == count
    if name.startswith('ci-main'):
        assert all(x['exit_code'] == 0 for x in d['steps'][:8]) and d['steps'][8]['exit_code'] != 0
        assert d['steps'][8]['name'] == 'Validate coverage export'
    else:
        assert d['status'] == 'passed' and all(x['exit_code'] == 0 for x in d['steps'])
    if 'commit' in d:
        assert d['commit'] == execution_head and d['initial_git_status'] == ''
        if not name.startswith('ci-main'):
            assert d['final_git_status'] == ''
        controller = 'benchmark-ci-runner.py' if name.startswith('ci-bench') else 'full-ci-runner.py'
        assert d['runner_sha256'] == sha(r / controller)
        assert all(sha(s / '.github/workflows' / n) == v for n, v in d['workflows'].items())
    if 'sources' in d:
        assert d['sources'] == fingerprints
    if 'source_fingerprints' in d:
        assert all(recorded_match(n, v) for n, v in d['source_fingerprints'].items())
        assert all(d['source_fingerprints'].get(n) == v for n, v in fingerprints.items())
    for step in d['steps']:
        if 'log_sha256' in step:
            assert sha(Path(step['log'])) == step['log_sha256']
    reports[name] = dict(steps=count, sha256=sha(r / name))
assert 'Swift version 6.3.3' in load('compatibility/result.json')['swift']
assert 'Ran 5 tests' in (r / 'ci-main/main-07-test-documentation-reporting.log').read_text()
assert load('ci-security-python/security-python-result.json')['security_findings']['python'] == 0

coverage = r / 'coverage-supplement/coverage.lcov'
original_coverage = (r / 'ci-main/coverage.lcov').read_text()
assert not any(line.startswith('SF:') and '/Sources/SwiftAgent/' in line for line in original_coverage.splitlines())
supplement = load('coverage-supplement/result.json')
assert supplement['source'] == '01bb6f39d5f503ef597234f0045fb86cf2ce7a0a' and supplement['exit_code'] == 0
assert supplement['coverage_sha256'] == sha(coverage)
assert supplement['controller_sha256'] == sha(r / 'export-agent-coverage.py')
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
assert supplement['objects'] == {str(p): sha(p) for p in binaries}
assert supplement['profile_sha256'] == sha(s / '.build/debug/codecov/default.profdata')
assert supplement['main_receipt_sha256'] == sha(r / 'ci-main/main-result.json')
assert supplement['log_sha256'] == sha(r / 'coverage-supplement/export.log')
reports['coverage'] = dict(sha256=sha(coverage), records=records, executed_lines=hits, profile_sha256=sha(s / '.build/debug/codecov/default.profdata'), objects={str(p): sha(p) for p in binaries}, scope='Supplemental explicit-object local export. Original unchanged workflow omits Agent; PR97 separately fixes the hosted exporter.')

policy = load('ci-bench/ci-acceptance/regression-policy.json')
acceptance = load('ci-bench/ci-acceptance/acceptance.json')
assert policy['source']['commit'] == execution_head and policy['status'] == 'passed' and not policy['blocking']
assert acceptance['coverage_complete'] and sum(p['engine_cases'] for p in acceptance['profiles']) == 404
assert sum(p['passed'] for p in acceptance['profiles']) == 400 and sum(len(p['failures']) for p in acceptance['profiles']) == 4
assert sha(r / 'ci-bench/ci-acceptance/acceptance.json') == policy['acceptance_sha256']
assert policy['conformance_status'] == 'failed' and len(policy['known_failures']) == 4 and all(f['engine'] == 'pandas' for f in policy['known_failures'])
worker = r / 'ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker'
build = json.loads(Path(str(worker) + '.build.json').read_text())
assert build['source']['commit'] == execution_head and sha(worker) == build['binary_sha256'] and all(sha(s / n) == v for n, v in build['source']['files'].items())
reports['benchmarks'] = dict(engine_cases=404, strict_pass=400, known_strict_failures=4, worker_source_files=len(build['source']['files']), worker_sha256=sha(worker))

security = r / 'ci-security-swift633'
d = load('ci-security-swift633/result.json')
assert d['status'] == 'passed' and d['source'] == execution_head and d['source_fingerprints'] == fingerprints and d['findings'] == 1 and len(d['steps']) == 2
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
assert len(extracted) == 351 and sum(n.startswith('Sources/') for n in extracted) == 290 and sum(n.startswith('Benchmarks/') for n in extracted) == 59 and 'Package.swift' in extracted and 'Examples/NumericalWorkflow/ScientificWorkflow.swift' in extracted
with zipfile.ZipFile(security / 'database/src.zip') as archive:
    for name in sorted(extracted):
        members = [n for n in archive.namelist() if n.endswith('/source/' + name)]
        assert len(members) == 1 and hashlib.sha256(archive.read(members[0])).hexdigest() == sha(s / name)
(r / 'security-extraction.json').write_text(json.dumps(dict(source=head, execution_source=execution_head, scope='Archived source bytes from execution_source verified against publication source; only example README and commit subject changed', files={n: sha(s / n) for n in sorted(extracted)}, sarif_sha256=sha(security / 'swift.sarif')), indent=2) + '\n')
reports['swift-security'] = dict(extracted=351, findings=1, sha256=sha(security / 'result.json'))
# Execute and verify the actual documented command and each retained compiler/configuration binary.
doc = load('documented-example/result.json')
assert doc['status'] == 'passed' and doc['source'] == head and doc['initial_git_status'] == ''
assert doc['source_tree'] == git('rev-parse', 'HEAD^{tree}')
assert doc['controller_sha256'] == sha(r / 'run-documented-example.py')
assert all(sha(s / n) == v for n, v in doc['source_sha256'].items())
assert all(step['exit_code'] == 0 and step['log_sha256'] == sha(r / 'documented-example' / (step['name'] + '.log')) for step in doc['steps'])
assert sha(Path(doc['binary'])) == doc['binary_sha256']
assert all(sha(r / 'documented-example/results' / n) == v for n, v in doc['outputs'].items())
controls = {}
expected_binaries = {
    'native-debug': r / 'derived/Build/Products/Debug/ScientificWorkflow',
    'native-release': r / 'derived/Build/Products/Release/ScientificWorkflow',
    'swift633-debug': r / 'swift633/debug/ScientificWorkflow',
    'swift633-release': r / 'swift633/release/ScientificWorkflow',
    'documented-release': r / 'derived/Build/Products/Release/ScientificWorkflow'
}

for label in ['native-debug', 'native-release']:
    folder = r / ('example-' + label)
    d = load('example-' + label + '/result.json')
    assert d['status'] == 'passed' and d['source'] == head and d['initial_git_status'] == ''
    assert Path(d['binary']) == expected_binaries[label].resolve()
    assert len(d['steps']) == d['steps_count'] == 23 and all(step['status'] == 'passed' for step in d['steps'])
    assert d['controller_sha256'] == sha(r / 'exercise-example.py')
    assert all(sha(s / n) == v for n, v in d['source_sha256'].items())
    assert sha(Path(d['binary'])) == d['binary_sha256'] and sha(Path(d['resource'])) == d['resource_sha256']
    assert d['resource_sha256'] == sha(s / 'Examples/NumericalWorkflow/Data/sample.csv')
    for step in d['steps']:
        assert step['log_sha256'] == sha(folder / (step['name'] + '.log'))
        assert (step['exit_code'] == 0) == (step['expected'] == 'success')
    for name, hashes in d['outputs'].items():
        assert all(sha(folder / name / n) == v for n, v in hashes.items())
    for name, digest in d['profile_files'].items():
        assert sha(folder / name) == digest
    verification = json.loads((folder / 'verify-fixture-0.log').read_text())
    assert verification['status'] == 'passed' and verification['verifier_sha256'] == sha(s / 'Examples/NumericalWorkflow/verify.py')
    controls[label] = dict(steps=23, receipt_sha256=sha(folder / 'result.json'), maximum_absolute_error=max(verification['maximum_absolute_errors'].values()), outputs=d['outputs']['bundled-first'])
for label in ['debug', 'release']:
    folder = r / ('example-swift633-' + label + '-before-xcode-guide')
    failed = json.loads((folder / 'result.json').read_text())
    assert failed['steps'][0]['exit_code'] == 255
    assert 'Failed to load the default metallib' in (folder / 'bundled-first.log').read_text()
    assert failed['steps'][0]['log_sha256'] == sha(folder / 'bundled-first.log')
reports['compatibility-runtime-limit'] = 'Plain SwiftPM omits MLX Metal resources; builds and safe tests pass, runtime controls fail as retained. Supported numerical run uses Xcode, per dependency documentation.'
empty = load('empty-column-control/result.json')
assert empty['status'] == 'passed' and empty['source'] == head
assert empty['binary_sha256'] == load('example-native-debug/result.json')['binary_sha256']
assert empty['controller_sha256'] == sha(r / 'check-empty-column.py')
assert [x['name'] for x in empty['cases']] == ['all-missing-feature', 'first-numeric-after-1000', 'invalid-feature-text']
for case in empty['cases']:
    assert case['exit_code'] != 0
    assert case['log_sha256'] == sha(r / 'empty-column-control' / (case['name'] + '.log'))
    assert case['input_sha256'] == sha(r / 'empty-column-control' / (case['name'] + '.csv'))
cli_coverage = load('example-coverage/result.json')
assert cli_coverage['status'] == 'passed' and cli_coverage['source'] == head
assert cli_coverage['source_sha256'] == sha(s / 'Examples/NumericalWorkflow/ScientificWorkflow.swift')
assert cli_coverage['binary_sha256'] == load('example-native-debug/result.json')['binary_sha256']
assert cli_coverage['controls_sha256'] == sha(r / 'example-native-debug/result.json')
assert cli_coverage['controller_sha256'] == sha(r / 'export-example-coverage.py')
assert cli_coverage['profile_sha256'] == sha(r / 'example-coverage/example.profdata')
expected_profiles = {str((r / 'example-native-debug' / n).resolve()): digest for n, digest in load('example-native-debug/result.json')['profile_files'].items()}
assert cli_coverage['profiles'] == expected_profiles
assert all(sha(Path(n)) == digest for n, digest in expected_profiles.items())
assert set(expected_profiles) == {str(p.resolve()) for p in (r / 'example-native-debug/profiles').glob('*.profraw')}
coverage_lines = (r / 'example-coverage/example.lcov').read_text().splitlines()
assert cli_coverage['selected_record_sha256'] == sha(r / 'example-coverage/example.lcov')
assert sum(n.startswith('SF:') for n in coverage_lines) == 1
assert any(n.startswith('SF:') and n.endswith('Examples/NumericalWorkflow/ScientificWorkflow.swift') for n in coverage_lines)
assert cli_coverage['executable_lines'] == sum(int(n[3:]) for n in coverage_lines if n.startswith('LF:'))
assert cli_coverage['executed_lines'] == sum(int(n[3:]) for n in coverage_lines if n.startswith('LH:'))
assert cli_coverage['line_percent'] == 100 * cli_coverage['executed_lines'] / cli_coverage['executable_lines']
assert cli_coverage['executed_lines'] > 0 and cli_coverage['executable_lines'] >= cli_coverage['executed_lines']
for step in cli_coverage['steps']:
    assert step['exit_code'] == 0
    output = 'coverage.lcov' if step['name'] == 'export' else 'merge.stdout'
    assert step['stdout_sha256'] == sha(r / 'example-coverage' / output)
    assert step['stderr_sha256'] == sha(r / 'example-coverage' / (step['name'] + '.log'))
reports['example'] = dict(documented_command_sha256=sha(r / 'documented-example/result.json'), configurations=controls, empty_column_rejected=True)
assert load('cache-preparation.json')['status'] == 'passed'
assert git('status', '--porcelain') == '' and subprocess.check_output(['xcode-select', '-p'], text=True).strip() == '/Applications/Xcode.app/Contents/Developer'
result = dict(status='passed', source=head, base=base, files=6, changed_files=sorted(changed), commits=1, execution_source=execution_head, reports=reports, verifier_sha256=sha(Path(__file__)), limits=['Local CI execution precedes a documentation-only clarification and Conventional Commit subject correction. Compiled and executable inputs are byte-identical; final-head actual example checks are separate.', 'The inherited positional coverage export omits Agent; extra local guard fails. PR97 is separate; supplemental export does not repair hosted CI.', 'Swift6.3.3 compatibility runs safe suites and the actual example, not every GPU suite; CodeQL uses its matching6.3.3 compiler/extractor. Local action-step replay does not prove hosted uploads.', 'Four known pandas Wampler strict failures and one unchanged unsuppressed legacy MD5 finding remain.'])
(r / 'qualification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
