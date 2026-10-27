from pathlib import Path
import hashlib, json, subprocess, zipfile
r = Path(__file__).resolve().parent
s = r / 'source'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
git = lambda *a: subprocess.check_output(['git', *a], cwd=s, text=True).strip()
head = '84aa7c59e80d8282c7daf0ce8e9dfc4871308b60'
base = 'e19db7dda4567c425b7eb002da82e234e6c7980f'
prior = 'c4de6cc866fff6f52100535dbcb38dd708558200'
files = ['.github/workflows/ci.yml', 'scripts/verify_doc_coverage.py', 'scripts/tests/test_verify_doc_coverage.py']
assert git('rev-parse', 'HEAD') == head and git('rev-parse', 'HEAD^') == base and git('status', '--porcelain') == ''
assert set(git('diff', '--name-only', base, head).splitlines()) == set(files)
for name in files:
    assert hashlib.sha256(subprocess.check_output(['git', 'show', prior + ':' + name], cwd=s)).hexdigest() == sha(s / name)
fingerprints = {str(p.relative_to(s)): sha(p) for folder in ['Sources', 'Tests'] for p in (s / folder).rglob('*.swift')}
for name, digest in fingerprints.items():
    assert hashlib.sha256(subprocess.check_output(['git', 'show', base + ':' + name], cwd=s)).hexdigest() == digest
assert git('diff', base, head, '--', 'Package.swift', 'Package.resolved', '.codecov.yml') == ''
red = json.loads((r / 'reporting-red/result.json').read_text())
green = json.loads((r / 'reporting-green/result.json').read_text())
for tag, d, failures, status, commit in [('red', red, 4, 'failed', base), ('green', green, 0, 'passed', head)]:
    assert d['head'] == commit and d['tests_run'] == 5 and d['failures'] == failures
    assert d['errors'] == d['skipped'] == 0 and d['status'] == status and d['scan_exit_code'] == 0
    assert d['runner_sha256'] == sha(r / 'run-reporting-tests.py')
    assert d['files'][files[2]] == sha(s / files[2])
    for name in files[:2]:
        expected = hashlib.sha256(subprocess.check_output(['git', 'show', base + ':' + name], cwd=s)).hexdigest() if tag == 'red' else sha(s / name)
        assert d['files'][name] == expected
    assert all(sha(r / ('reporting-' + tag) / name) == digest for name, digest in d['logs'].items())
oldscan = (r / 'reporting-red/scan.log').read_text()
newscan = (r / 'reporting-green/scan.log').read_text()
assert '98.66% (2431/2464' in oldscan and '100.00% DocC Public API Coverage Verified' in oldscan
assert '98.66% (2431/2464 matched declarations documented)' in newscan and '100.00%' not in newscan
assert 'heuristic scan is not DocC symbol-graph coverage' in newscan and 'No unresolved documentation placeholders found.' in newscan
system_meta = json.loads((r / 'system-python-compatibility.json').read_text())
system_result = json.loads((r / system_meta['receipt']).read_text())
assert system_meta['version'] == 'Python 3.9.6' and system_meta['source'] == head
assert sha(r / system_meta['receipt']) == system_meta['receipt_sha256']
assert system_result['head'] == head and system_result['status'] == 'passed' and system_result['tests_run'] == 5
assert system_result['failures'] == system_result['errors'] == system_result['skipped'] == system_result['scan_exit_code'] == 0
assert system_result['files'] == green['files'] and system_result['runner_sha256'] == sha(r / 'run-reporting-tests.py')
assert all(sha(r / 'reporting-system-python' / name) == digest for name, digest in system_result['logs'].items())
assert (r / 'reporting-system-python/scan.log').read_text() == newscan
reports = {}
for tag in ['full-debug', 'full-release']:
    b = json.loads((r / f'native-{tag}/build.json').read_text())
    t = json.loads((r / f'native-{tag}/tests.json').read_text())
    summary = t['summary']
    assert b['exit_code'] == t['exit_code'] == 0 and b['sources'] == fingerprints and t['strict_onnx_ci']
    assert summary['totalTestCount'] == summary['passedTests'] == 1656 and summary['failedTests'] == summary['skippedTests'] == 0
    reports[tag] = {k: summary[k] for k in ['totalTestCount', 'passedTests', 'failedTests', 'skippedTests']}
for name, count in [('ci-main/main-result.json', 9), ('ci-bench/benchmarks-result.json', 19), ('compatibility/result.json', 3), ('ci-security-python/security-python-result.json', 2)]:
    d = json.loads((r / name).read_text())
    assert d['status'] == 'passed' and len(d['steps']) == count and all(x['exit_code'] == 0 for x in d['steps'])
    if 'commit' in d:
        assert d['commit'] == head and d['initial_git_status'] == d['final_git_status'] == ''
        runner = 'benchmark-ci-runner.py' if name.startswith('ci-bench/') else 'full-ci-runner.py'
        assert d['runner_sha256'] == sha(r / runner)
        assert all(sha(s / '.github/workflows' / path) == digest for path, digest in d['workflows'].items())
    if 'sources' in d:
        assert d['sources'] == fingerprints
    if 'source_fingerprints' in d:
        assert all(sha(s / path) == digest for path, digest in d['source_fingerprints'].items())
        assert all(d['source_fingerprints'].get(path) == digest for path, digest in fingerprints.items())
    for step in d['steps']:
        if 'log_sha256' in step:
            assert sha(Path(step['log'])) == step['log_sha256']
    reports[name] = dict(status=d['status'], steps=count, sha256=sha(r / name))
main = json.loads((r / 'ci-main/main-result.json').read_text())
docsteps = [x for x in main['steps'] if x['name'] == 'Test documentation reporting']
assert len(docsteps) == 1 and 'Ran 5 tests' in Path(docsteps[0]['log']).read_text() and '\nOK\n' in Path(docsteps[0]['log']).read_text()
scansteps = [x for x in main['steps'] if x['name'] == 'Report API documentation and check placeholders']
assert len(scansteps) == 1 and Path(scansteps[0]['log']).read_text() == newscan
python = json.loads((r / 'ci-security-python/security-python-result.json').read_text())
assert python['security_findings']['python'] == 0
policy = json.loads((r / 'ci-bench/ci-acceptance/regression-policy.json').read_text())
assert policy['source']['commit'] == head and policy['status'] == 'passed' and not policy['blocking']
assert policy['conformance_status'] == 'failed' and len(policy['known_failures']) == 4 and all(x['engine'] == 'pandas' for x in policy['known_failures'])
security = r / 'ci-security-swift633'
d = json.loads((security / 'result.json').read_text())
assert d['status'] == 'passed' and d['source'] == head and d['source_fingerprints'] == fingerprints and d['findings'] == 1
assert len(d['steps']) == 2 and all(x['exit_code'] == 0 and sha(security / (x['name'] + '.log')) == x['log_sha256'] for x in d['steps'])
assert d['xcode_selected'] == '/Applications/Xcode.app/Contents/Developer' and '6.3.3' in d['swift'] and '6.3.3' in d['extractor']
assert sha(security / 'swift.sarif') == d['sarif_sha256'] and sha(r / 'check-swift-codeql-replay.py') == d['script_sha256']
sarif = json.loads((security / 'swift.sarif').read_text())
findings = [f for run in sarif['runs'] for f in run.get('results', [])]
assert len(findings) == 1 and findings[0]['ruleId'] == 'swift/weak-password-hashing'
loc = findings[0]['locations'][0]['physicalLocation']
assert loc['artifactLocation']['uri'] == 'Sources/SwiftDatabase/DatabaseConnection.swift' and loc['region']['startLine'] == 606
extracted = {loc['physicalLocation']['artifactLocation']['uri'] for run in sarif['runs'] for invocation in run.get('invocations', []) for note in invocation.get('toolExecutionNotifications', []) if note.get('descriptor', {}).get('id') == 'swift/diagnostics/successfully-extracted-files' for loc in note.get('locations', [])}
verified = sorted(name for name in extracted if (s / name).is_file())
# The 348 extracted repo files comprise library sources, benchmarks and manifest.
assert len(extracted) == len(verified) == 348 and 'Sources/SwiftDatabase/DatabaseConnection.swift' in verified
assert sum(name.startswith('Sources/') for name in verified) == 288
assert sum(name.startswith('Benchmarks/') for name in verified) == 59 and 'Package.swift' in verified
with zipfile.ZipFile(security / 'database/src.zip') as z:
    names = z.namelist()
    for name in verified:
        matches = [n for n in names if n.endswith('/source/' + name)]
        assert len(matches) == 1 and hashlib.sha256(z.read(matches[0])).hexdigest() == sha(s / name)
worker = r / 'ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker'
worker_receipt = Path(str(worker) + '.build.json')
build = json.loads(worker_receipt.read_text())
assert build['source']['commit'] == head and sha(worker) == build['binary_sha256']
assert all(sha(s / path) == digest for path, digest in build['source']['files'].items())
cache = json.loads((r / 'cache-preparation.json').read_text())
assert cache['status'] == 'passed'
checks = ['spec.md', 'production.patch', 'standards-review.md', 'spec-review.md', 'controller-derivation.json', 'cache-preparation.json', 'reporting-red/result.json', 'reporting-green/result.json', 'system-python-compatibility.json', 'reporting-system-python/result.json', 'qualification-verifier-failure.json', 'verify-qualification-before-extraction-fix.py']
result = dict(status='passed', source=head, base=base, reused_prior_fix=prior, changed_files=files, native=reports,
    reporting=dict(regressions=5, baseline_failures=4, corrected_failures=0, system_python='3.9.6 actual five-fixture and real-source execution passed', matched_declarations=2464, documented_declarations=2431, reported_percent=98.66, meaning='Existing heuristic declaration scan only, not DocC symbol-graph or executable-code coverage; no threshold change'),
    python_codeql_findings=0, swift_codeql_findings=1, verified_swift_archive_files=len(verified), verified_swift_library_files=288, verified_swift_benchmark_files=59,
    security='Complete fresh analyses, one unchanged unsuppressed legacy PostgreSQL MD5 finding remains',
    regression_policy='Passed unchanged policy; four strict Python Wampler failures remain failed',
    scope='Reporting/test/workflow correction only. All Swift source/tests, dependencies, numerical policies and Codecov settings unchanged from upstream.',
    worker_receipt_sha256=sha(worker_receipt), worker_binary_sha256=sha(worker), records={name: sha(r / name) for name in checks}, source_fingerprints=fingerprints, verifier_sha256=sha(Path(__file__)))
(r / 'qualification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ['native', 'records', 'source_fingerprints']}, indent=2))
