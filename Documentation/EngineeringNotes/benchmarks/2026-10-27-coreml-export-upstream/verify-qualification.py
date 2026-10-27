from pathlib import Path
import hashlib, json, subprocess, zipfile
r = Path(__file__).resolve().parent
s = r / 'source'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
git = lambda *a: subprocess.check_output(['git', *a], cwd=s, text=True).strip()
head = (r / 'source-head.txt').read_text().strip()
base = 'e19db7dda4567c425b7eb002da82e234e6c7980f'
prior = 'a1e234d25677d91ce5914062603c41233fe13c09'
production = ['Sources/SwiftML/Serialization/' + n + '.swift' for n in ['CoreMLExportable', 'CoreMLExporter', 'CoreMLProtobuf']]
test = 'Tests/SwiftMLTests/CoreMLMulticlassExportTests.swift'
assert git('rev-parse', 'HEAD') == head and git('rev-parse', 'HEAD^') == base
assert git('status', '--porcelain') == ''
assert set(git('diff', '--name-only', base, head).splitlines()) == set(production + [test])
for name in production + [test]:
    assert hashlib.sha256(subprocess.check_output(['git', 'show', prior + ':' + name], cwd=s)).hexdigest() == sha(s / name)
fingerprints = {str(p.relative_to(s)): sha(p) for folder in ['Sources', 'Tests'] for p in (s / folder).rglob('*.swift')}
old = {name: hashlib.sha256(subprocess.check_output(['git', 'show', base + ':' + name], cwd=s)).hexdigest() for name in production}
red = json.loads((r / 'red-source-binding.json').read_text())
assert red['base'] == base and red['test_sha256'] == sha(s / test) and red['production_sha256'] == old
redbuild = json.loads((r / 'native-red/build.json').read_text())
redtests = json.loads((r / 'native-red/tests.json').read_text())
assert redbuild['exit_code'] == 0 and redtests['exit_code'] == 65
assert redtests['summary']['totalTestCount'] == redtests['summary']['failedTests'] == 2
assert redtests['summary']['passedTests'] == redtests['summary']['skippedTests'] == 0
assert redbuild['sources'] == dict(fingerprints, **old)
assert red['tests_log_sha256'] == sha(r / 'native-red/tests.log') and red['test_receipt_sha256'] == sha(r / 'native-red/tests.json')
failed = json.loads((r / 'compatibility-cache-path-failure/result.json').read_text())
assert failed['sources'] == fingerprints and len(failed['steps']) == 1
assert failed['steps'][0]['name'] == 'debug-build' and failed['steps'][0]['exit_code'] == 1
failure_log = (r / 'compatibility-cache-path-failure/debug-build.log').read_text()
assert 'was compiled with module cache path' in failure_log
assert '/swiftsci-upstream-gpu-gradient-20261027/swift633/' in failure_log
assert '/swiftsci-upstream-coreml-export-20261027/swift633/' in failure_log
recovery = json.loads((r / 'cache-recovery.json').read_text())
assert recovery['original_receipt_sha256'] == sha(r / 'compatibility-cache-path-failure/result.json')
reports = {}
for tag, count in [('green', 2), ('full-debug', 1658), ('full-release', 1658)]:
    b = json.loads((r / f'native-{tag}/build.json').read_text())
    t = json.loads((r / f'native-{tag}/tests.json').read_text())
    sums = t['summary']
    assert b['exit_code'] == t['exit_code'] == 0 and b['sources'] == fingerprints and t['strict_onnx_ci']
    assert sums['totalTestCount'] == sums['passedTests'] == count and sums['failedTests'] == sums['skippedTests'] == 0
    reports[tag] = {k: sums[k] for k in ['totalTestCount', 'passedTests', 'failedTests', 'skippedTests']}
for name, count in [('ci-main/main-result.json', 8), ('ci-bench/benchmarks-result.json', 19), ('compatibility/result.json', 4), ('ci-security-python/security-python-result.json', 2)]:
    d = json.loads((r / name).read_text())
    assert d['status'] == 'passed' and len(d['steps']) == count and all(x['exit_code'] == 0 for x in d['steps'])
    if 'commit' in d:
        assert d['commit'] == head and d['initial_git_status'] == d['final_git_status'] == ''
    if 'sources' in d:
        assert d['sources'] == fingerprints
    if 'source_fingerprints' in d:
        assert all(sha(s / path) == digest for path, digest in d['source_fingerprints'].items())
        assert all(d['source_fingerprints'].get(path) == digest for path, digest in fingerprints.items())
    for step in d['steps']:
        if 'log_sha256' in step:
            assert sha(Path(step['log'])) == step['log_sha256']
    reports[name] = dict(status=d['status'], steps=count, sha256=sha(r / name))
python = json.loads((r / 'ci-security-python/security-python-result.json').read_text())
assert python['security_findings']['python'] == 0
focused_compat = (r / 'compatibility/focused-coreml-tests.log').read_text()
assert 'Testing Library Version: 6.3.3' in focused_compat
assert 'Test run with 2 tests in 1 suite passed' in focused_compat
assert 'Exported multiclass probabilities match independent stable softmax' in focused_compat
assert 'Fitted public multiclass classifier survives export and prepared inference' in focused_compat
policy = json.loads((r / 'ci-bench/ci-acceptance/regression-policy.json').read_text())
assert policy['source']['commit'] == head and policy['status'] == 'passed' and not policy['blocking']
assert policy['conformance_status'] == 'failed' and len(policy['known_failures']) == 4
assert all(x['engine'] == 'pandas' for x in policy['known_failures'])
security = r / 'ci-security-swift633'
d = json.loads((security / 'result.json').read_text())
assert d['status'] == 'passed' and d['source'] == head and d['source_fingerprints'] == fingerprints and d['findings'] == 1
assert len(d['steps']) == 2 and all(x['exit_code'] == 0 and sha(security / (x['name'] + '.log')) == x['log_sha256'] for x in d['steps'])
assert d['xcode_selected'] == '/Applications/Xcode.app/Contents/Developer' and '6.3.3' in d['swift'] and '6.3.3' in d['extractor']
assert sha(security / 'swift.sarif') == d['sarif_sha256'] and sha(r / 'check-swift-codeql-replay.py') == d['script_sha256']
sarif = json.loads((security / 'swift.sarif').read_text())
findings = [f for run in sarif['runs'] for f in run.get('results', [])]
assert len(findings) == 1 and findings[0]['ruleId'] == 'swift/weak-password-hashing'
db = 'Sources/SwiftDatabase/DatabaseConnection.swift'
loc = findings[0]['locations'][0]['physicalLocation']
assert loc['artifactLocation']['uri'] == db and loc['region']['startLine'] == 606 and git('diff', base, head, '--', db) == ''
extracted = {loc['physicalLocation']['artifactLocation']['uri'] for run in sarif['runs'] for invocation in run.get('invocations', []) for note in invocation.get('toolExecutionNotifications', []) if note.get('descriptor', {}).get('id') == 'swift/diagnostics/successfully-extracted-files' for loc in note.get('locations', [])}
assert set(production).issubset(extracted)
with zipfile.ZipFile(security / 'database/src.zip') as z:
    for name in production:
        matches = [n for n in z.namelist() if n.endswith('/source/' + name)]
        assert len(matches) == 1 and hashlib.sha256(z.read(matches[0])).hexdigest() == sha(s / name)
worker = r / 'ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker'
worker_receipt = Path(str(worker) + '.build.json')
build = json.loads(worker_receipt.read_text())
assert build['source']['commit'] == head and sha(worker) == build['binary_sha256']
assert all(sha(s / path) == digest for path, digest in build['source']['files'].items())
checks = ['spec.md', 'production.patch', 'standards-review.md', 'spec-review.md', 'red-source-binding.json', 'controller-derivation.json', 'schema-reference.md', 'cache-recovery.json', 'compatibility/focused-coreml-tests.log']
result = dict(status='passed', source=head, base=base, reused_prior_fix=prior, changed_files=production + [test], native=reports,
    python_codeql_findings=0, swift_codeql_findings=1,
    swift_security='Completed matching6.3.3 analysis; actual serialization extraction and archive bytes verified. One unchanged unsuppressed legacy PostgreSQL MD5 finding remains.',
    regression_policy='Passed unchanged policy; four strict Python Wampler failures remain failed',
    scope='Independent multiclass Core ML softmax serialization correction. Public signatures, probability shapes, binary sigmoid, regression and device policy unchanged. No performance, placement or quality claim.',
    worker_receipt_sha256=sha(worker_receipt), worker_binary_sha256=sha(worker), records={name: sha(r / name) for name in checks}, source_fingerprints=fingerprints, verifier_sha256=sha(Path(__file__)))
(r / 'qualification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ['native', 'records', 'source_fingerprints']}, indent=2))
