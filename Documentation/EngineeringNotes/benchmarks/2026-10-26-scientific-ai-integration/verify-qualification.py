from pathlib import Path
import hashlib, json, subprocess
r = Path(__file__).resolve().parent
source = r / 'source'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
git = lambda *args: subprocess.check_output(['git', *args], cwd=source, text=True).strip()
head = 'c4de6cc866fff6f52100535dbcb38dd708558200'
base = 'a1e234d25677d91ce5914062603c41233fe13c09'
pca = '4f33c76f3938e070105c2a5928c712aa5e067a00'
assert git('rev-parse', 'HEAD') == head and git('status', '--porcelain') == ''
for parent in [base, pca]: subprocess.run(['git', 'merge-base', '--is-ancestor', parent, head], cwd=source, check=True)
fingerprints = {str(p.relative_to(source)): sha(p) for folder in ['Sources', 'Tests'] for p in (source / folder).rglob('*.swift')}
reports = {}
for mode in ['debug', 'release']:
    build = json.loads((r / f'native-full-{mode}/build.json').read_text())
    result = json.loads((r / f'native-full-{mode}/tests.json').read_text())
    assert build['exit_code'] == result['exit_code'] == 0 and build['sources'] == fingerprints
    summary = result['summary']
    assert summary['totalTestCount'] == summary['passedTests'] == 1696
    assert summary['failedTests'] == summary['skippedTests'] == 0 and result['strict_onnx_ci']
    reports[mode] = {k: summary[k] for k in ['totalTestCount', 'passedTests', 'failedTests', 'skippedTests']}
for name in ['ci-main/main-result.json', 'ci-bench/benchmarks-result.json', 'ci-security-python/security-python-result.json', 'compatibility/result.json']:
    report = json.loads((r / name).read_text())
    assert report['status'] == 'passed' and all(step['exit_code'] == 0 for step in report['steps'])
    if 'source_fingerprints' in report:
        assert all(sha(source / path) == digest for path, digest in report['source_fingerprints'].items())
    if 'sources' in report: assert report['sources'] == fingerprints
    for step in report['steps']:
        if 'log_sha256' in step: assert sha(Path(step['log'])) == step['log_sha256']
    reports[name] = dict(sha256=sha(r / name), steps=len(report['steps']), status=report['status'])
security = json.loads((r / 'ci-security-python/security-python-result.json').read_text())
assert security['security_findings']['python'] == 0
policy = json.loads((r / 'ci-bench/ci-acceptance/regression-policy.json').read_text())
assert policy['source']['commit'] == head and policy['status'] == 'passed'
assert policy['conformance_status'] == 'failed' and not policy['blocking'] and len(policy['known_failures']) == 4
assert all(item['engine'] == 'pandas' for item in policy['known_failures'])
comparison = json.loads((r / 'pca-parent-comparison.json').read_text())
for path, item in comparison.items():
    assert sha(source / path) == item['integrated_sha256']
    if path != 'Sources/SwiftDataFrame/Core/PreparedNumericBatch.swift':
        expected = subprocess.check_output(['git', 'show', pca + ':' + path], cwd=source)
        assert hashlib.sha256(expected).hexdigest() == item['integrated_sha256']
for folder in ['SwiftML', 'SwiftPreprocessing', 'SwiftLLM', 'SwiftAgent']:
    assert git('diff', base, head, '--', 'Sources/' + folder) == ''
checks = ['doc-check-red.log', 'doc-check-green.log', 'doc-check-source.log', 'standards-review.md', 'spec-review.md']
assert 'FAILED (failures=4)' in (r / checks[0]).read_text()
assert 'Ran 5 tests' in (r / checks[1]).read_text() and 'OK' in (r / checks[1]).read_text()
assert '98.68% (2464/2497' in (r / checks[2]).read_text()
result = dict(status='passed', source=head, baseline=base, pca_parent=pca, native=reports,
    regression_policy='passed', strict_conformance='failed: four unchanged Python Wampler cases',
    python_codeql_findings=0, local_swift_codeql='unsupported by installed CodeQL2.27.3 with retained Xcode27/Swift6.4; not rerun for this unchanged tooling limitation',
    documentation='heuristic2464/2497; five reporting regressions pass; placeholder failure retained',
    records={name:sha(r/name) for name in checks}, source_fingerprints=fingerprints,
    verifier_sha256=sha(Path(__file__)))
(r / 'qualification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['native','source_fingerprints','records']}, indent=2))
