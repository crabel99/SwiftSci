from pathlib import Path
import hashlib, json, re, subprocess, zipfile
r = Path(__file__).resolve().parent
s = r / 'source'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
git = lambda *args: subprocess.check_output(['git', *args], cwd=s, text=True).strip()
load = lambda name: json.loads((r / name).read_text())
head = '3fd462155a10fa78a1cf6b98b56ea926d43ef112'
base = 'e19db7dda4567c425b7eb002da82e234e6c7980f'
gpu = '506204920a5a073b1e7bc316476875860bacfda0'
assert git('rev-parse', 'HEAD') == head and git('rev-parse', 'HEAD^') == gpu
assert git('rev-parse', gpu + '^') == base and git('status', '--porcelain') == ''
reconciliation = load('source-reconciliation.json')
assert reconciliation['head'] == head
feature_files = {row['path'] for row in reconciliation['reused_files']}
assert len(feature_files) == 11 and set(git('diff', '--name-only', gpu, head).splitlines()) == feature_files
assert set(git('diff', '--name-only', base, head).splitlines()) == feature_files | {'Sources/SwiftML/Losses/Losses.swift', 'Tests/SwiftMLTests/BinaryCrossEntropyTests.swift'}
for row in reconciliation['reused_files']:
    assert sha(s / row['path']) == row['sha256']
    assert hashlib.sha256(subprocess.check_output(['git', 'show', row['prior'] + ':' + row['path']], cwd=s)).hexdigest() == row['sha256']
assert git('diff', base, head, '--', 'Package.swift', 'Package.resolved', '.codecov.yml', '.github/workflows', 'Benchmarks', 'scripts') == ''
assert (r / 'production.patch').read_bytes() == subprocess.check_output(['git', 'diff', base, head], cwd=s)
assert (r / 'classification.patch').read_bytes() == subprocess.check_output(['git', 'diff', gpu, head], cwd=s)
fingerprints = {str(p.relative_to(s)): sha(p) for folder in ['Sources', 'Tests'] for p in (s / folder).rglob('*.swift')}
reports = {}
def native(root, tag, expected=None):
    b = json.loads((root / ('native-' + tag) / 'build.json').read_text())
    t = json.loads((root / ('native-' + tag) / 'tests.json').read_text())
    assert b['exit_code'] == t['exit_code'] == 0 and t['strict_onnx_ci']
    actual = json.loads(subprocess.check_output(['xcrun', 'xcresulttool', 'get', 'test-results', 'summary', '--path', str(root / ('native-' + tag) / 'tests.xcresult'), '--format', 'json'], text=True))
    fields = ['totalTestCount', 'passedTests', 'failedTests', 'skippedTests']
    assert all(actual[k] == t['summary'][k] for k in fields)
    assert actual['totalTestCount'] == actual['passedTests'] and actual['failedTests'] == actual['skippedTests'] == 0
    if expected is not None:
        assert actual['totalTestCount'] == expected
    return b, {k: actual[k] for k in fields}
for tag in ['full-debug', 'full-release']:
    b, summary = native(r, tag, 1683)
    assert b['sources'] == fingerprints
    reports[tag] = summary
for path, count in [('ci-main/main-result.json', 8), ('ci-bench/benchmarks-result.json', 19), ('compatibility/result.json', 4), ('ci-security-python/security-python-result.json', 2)]:
    d = load(path)
    assert d['status'] == 'passed' and len(d['steps']) == count and all(step['exit_code'] == 0 for step in d['steps'])
    if 'commit' in d:
        assert d['commit'] == head and d['initial_git_status'] == d['final_git_status'] == ''
        controller = 'benchmark-ci-runner.py' if path.startswith('ci-bench/') else 'full-ci-runner.py'
        assert d['runner_sha256'] == sha(r / controller)
        assert all(sha(s / '.github/workflows' / name) == digest for name, digest in d['workflows'].items())
    if 'sources' in d:
        assert d['sources'] == fingerprints
    if 'source_fingerprints' in d:
        assert all(sha(s / name) == digest for name, digest in d['source_fingerprints'].items())
        assert all(d['source_fingerprints'].get(name) == digest for name, digest in fingerprints.items())
    for step in d['steps']:
        if 'log_sha256' in step:
            assert sha(Path(step['log'])) == step['log_sha256']
    reports[path] = dict(status=d['status'], steps=count, sha256=sha(r / path))
compat = load('compatibility/result.json')
assert 'Swift version 6.3.3' in compat['swift']
focused = (r / 'compatibility/focused-prepared-tests.log').read_text()
assert re.search(r'Test run with [1-9][0-9]* tests in 5 suites passed', focused)
assert 'Prepared logistic regression' in focused and 'Binary cross entropy gradients' in focused
assert 'Prepared classification integration' in focused and 'Classification pipeline synchronized lifecycle' in focused and 'Prepared row mapping metadata' in focused
assert load('ci-security-python/security-python-result.json')['security_findings']['python'] == 0
policy = load('ci-bench/ci-acceptance/regression-policy.json')
assert policy['source']['commit'] == head and policy['status'] == 'passed' and not policy['blocking']
assert policy['conformance_status'] == 'failed' and len(policy['known_failures']) == 4 and all(f['engine'] == 'pandas' for f in policy['known_failures'])
security = r / 'ci-security-swift633'
d = load('ci-security-swift633/result.json')
assert d['status'] == 'passed' and d['source'] == head and d['source_fingerprints'] == fingerprints and d['findings'] == 1
assert len(d['steps']) == 2 and all(step['exit_code'] == 0 and sha(security / (step['name'] + '.log')) == step['log_sha256'] for step in d['steps'])
assert d['xcode_selected'] == '/Applications/Xcode.app/Contents/Developer' and '6.3.3' in d['swift'] and '6.3.3' in d['extractor']
assert sha(security / 'swift.sarif') == d['sarif_sha256'] and sha(r / 'check-swift-codeql-replay.py') == d['script_sha256']
sarif = load('ci-security-swift633/swift.sarif')
findings = [finding for run in sarif['runs'] for finding in run.get('results', [])]
assert len(findings) == 1 and findings[0]['ruleId'] == 'swift/weak-password-hashing'
location = findings[0]['locations'][0]['physicalLocation']
assert location['artifactLocation']['uri'] == 'Sources/SwiftDatabase/DatabaseConnection.swift' and location['region']['startLine'] == 606
extracted = {loc['physicalLocation']['artifactLocation']['uri'] for run in sarif['runs'] for invocation in run.get('invocations', []) for note in invocation.get('toolExecutionNotifications', []) if note.get('descriptor', {}).get('id') == 'swift/diagnostics/successfully-extracted-files' for loc in note.get('locations', [])}
assert len(extracted) == 348 and all((s / name).is_file() for name in extracted)
assert sum(name.startswith('Sources/') for name in extracted) == 288 and sum(name.startswith('Benchmarks/') for name in extracted) == 59 and 'Package.swift' in extracted
with zipfile.ZipFile(security / 'database/src.zip') as archive:
    names = archive.namelist()
    for name in sorted(extracted):
        matches = [member for member in names if member.endswith('/source/' + name)]
        assert len(matches) == 1 and hashlib.sha256(archive.read(matches[0])).hexdigest() == sha(s / name)
worker = r / 'ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker'
receipt = Path(str(worker) + '.build.json')
build = json.loads(receipt.read_text())
assert build['source']['commit'] == head and sha(worker) == build['binary_sha256']
assert all(sha(s / name) == digest for name, digest in build['source']['files'].items())
public = load('verification/public-workflow/summary.json')
assert public['status'] == 'passed' and public['source_head'] == head and public['baseline_source'] == gpu
assert public['verifier_sha256'] == sha(r / 'verification/verify-public-workflow.py')
assert public['baseline_provenance_sha256'] == sha(r / 'verification/baseline-provenance.json')
assert public['candidate_proof_sha256'] == sha(r / 'verification/public-candidate/proof.json')
for case in public['cases']:
    assert case['rows'] == 569 and case['features'] == 30 and case['splits'] == [328, 115, 126] and case['executions'] == 3
    assert case['device'] == 'CPU' and case['precision'] == 'Double' and case['max_old_new_abs'] == 0 and case['labels_and_row_positions_exact']
    fixture = s / f"Benchmarks/Fixtures/supervised/inputs/wdbc-supervised-logistic-cpu-epochs{case['epochs']}.json"
    assert sha(fixture) == case['fixture_sha256']
    for name, digest in case['fresh_output_files'].items():
        assert sha(r / f"verification/public-workflow/epochs{case['epochs']}-{name}.json") == digest
assert [case['epochs'] for case in public['cases']] == [0, 1, 32]
for name in ['baseline', 'candidate']:
    proof = load('verification/public-' + name + '/proof.json')
    assert sha(r / ('verification/public-' + name + '/probe')) == proof['binary_sha256']
    assert all(sha(Path(path)) == digest for path, digest in proof['objects'].items())
    assert sha(Path(proof['input_build_log'])) == proof['input_build_log_sha256']
pca = load('pca-integration/result.json')
assert pca['status'] == 'passed' and pca['exit_code'] == 0 and pca['classification'] == head and pca['pca'] == reconciliation['pca_head'] and pca['tree'] == reconciliation['clean_integration_tree']
assert pca['controller_sha256'] == sha(r / 'check-pca-integration.py')
integration_source = r / 'pca-integration/source'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=integration_source, text=True).strip() == pca['integration_commit']
assert subprocess.check_output(['git', 'status', '--porcelain'], cwd=integration_source, text=True) == ''
b, pca_summary = native(r / 'pca-integration', 'pca-classification')
assert b['sources'] == {str(p.relative_to(integration_source)): sha(p) for folder in ['Sources', 'Tests'] for p in (integration_source / folder).rglob('*.swift')}
assert set(arg.removeprefix('-only-testing:') for arg in b['command'] if arg.startswith('-only-testing:')) == set(pca['selected'])
assert pca_summary['totalTestCount'] == 33
pca_tree = json.loads(subprocess.check_output(['xcrun','xcresulttool','get','test-results','tests','--path',str(r/'pca-integration/native-pca-classification/tests.xcresult'),'--format','json'],text=True))
pca_suites = {}
def collect_suites(node):
    if isinstance(node, dict):
        if node.get('nodeType') == 'Test Suite':
            identifier = node['nodeIdentifierURL'].split('/SwiftSci/')[-1]
            pca_suites[identifier] = node['result']
        for child in node.values(): collect_suites(child)
    elif isinstance(node, list):
        for child in node: collect_suites(child)
collect_suites(pca_tree)
assert set(pca_suites) == set(pca['selected']) and set(pca_suites.values()) == {'Passed'}
assert load('pca-integration-initial-failure.json')['failed_git_checkout_exit_code'] == 128
assert load('object-reference-repair.json')['referenced_stores'] >= 1
assert load('cache-preparation.json')['status'] == 'passed'
assert subprocess.check_output(['xcode-select', '-p'], text=True).strip() == '/Applications/Xcode.app/Contents/Developer'
assert load('compatibility-initial-failure.json')['exit_code'] == 1
metal = compat['metal_runtime_resource']
assert sha(Path(metal['source'])) == sha(Path(metal['destination'])) == metal['sha256']
for checkout in [r/'native-packages/checkouts/mlx-swift',r/'swift633/checkouts/mlx-swift']:
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=checkout,text=True).strip() == metal['mlx_revision']
    assert subprocess.check_output(['git','status','--porcelain'],cwd=checkout,text=True) == ''
assert load('compatibility-serial-probe/result.json')['exit_code'] == 0
assert '--no-parallel' in next(step['command'] for step in compat['steps'] if step['name'] == 'focused-prepared-tests')
checks = ['compatibility-cold-start-failure.json','compatibility-serial-probe/result.json','compatibility-initial-failure.json', 'spec.md', 'production.patch', 'classification.patch', 'source-reconciliation.json', 'standards-review.md', 'spec-review.md', 'controller-derivation.json', 'cache-preparation.json', 'pca-integration-initial-failure.json', 'object-reference-repair.json', 'pca-integration/result.json', 'verification/baseline-provenance.json', 'verification/public-workflow/summary.json']
result = dict(status='passed', source=head, base=base, gpu_prerequisite=gpu, changed_files=sorted(feature_files), full_pr_files=13, native=reports,
    public_workflow=dict(processes=9, numerical_fields=sum(case['numerical_fields_checked'] for case in public['cases']), max_baseline_difference=0, max_numpy_difference=max(case['max_numpy_abs'] for case in public['cases']), device='CPU', precision='Double', baseline='Fresh probe using retained qualified GPU prerequisite library objects; baseline library build is historical'),
    pca_integration=dict(source=pca['integration_commit'], tree=pca['tree'], summary=pca_summary, scope='Qualification-only clean merge with current PR89; no upstream merge or delivery of PCA in this PR'),
    compatibility_scope='All test targets compiled; safe suite plus all new prepared logistic numerical/GPU, pipeline, concurrency, row-mapping and BCE suites executed. Explicit --no-parallel avoids the preserved pinned-MLX concurrent cold-start lock cycle; concurrency tests retain their internal tasks. Swift6.3.3+SDK26.5 host code uses the pinned MLX Metal resource compiled by Xcode27 on this Mac.',
    python_codeql_findings=0, swift_codeql_findings=1, verified_swift_archive_files=348, regression_policy='Passed unchanged policy; four strict Python Wampler failures remain failed',
    security='One unchanged unsuppressed legacy PostgreSQL MD5 finding remains', worker_receipt_sha256=sha(receipt), worker_binary_sha256=sha(worker), worker_source_files=len(build['source']['files']),
    records={name:sha(r / name) for name in checks}, source_fingerprints=fingerprints, verifier_sha256=sha(Path(__file__)))
(r / 'qualification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({name:value for name,value in result.items() if name not in ['native','records','source_fingerprints']},indent=2))
