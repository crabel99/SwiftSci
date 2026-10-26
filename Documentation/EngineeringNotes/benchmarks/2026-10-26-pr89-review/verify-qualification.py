from pathlib import Path
import argparse, hashlib, json, subprocess

p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
a = p.parse_args()
r = a.root.resolve()
source = r / 'source'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads((r / path).read_text())
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
assert commit == '4f33c76f3938e070105c2a5928c712aa5e067a00'
changed = subprocess.check_output(['git', 'diff', '--name-only', '09607a7e9caa2b7166651dcaaa167178f6097b55', 'HEAD'], cwd=source, text=True).splitlines()
fingerprints = {name: sha(source / name) for name in changed}
result = {'commit': commit, 'changed_sources': fingerprints, 'native': {}, 'workflows': {}}

for mode in ['debug', 'release']:
    folder = f'native-full-{mode}-final'
    build, tests = read(f'{folder}/build.json'), read(f'{folder}/tests.json')
    assert build['exit_code'] == tests['exit_code'] == 0
    assert all(build['sources'][name] == digest for name, digest in fingerprints.items())
    summary = tests['summary']
    assert summary['failedTests'] == summary['skippedTests'] == 0
    assert summary['passedTests'] == summary['totalTestCount']
    result['native'][mode] = {key: summary[key] for key in ['totalTestCount', 'passedTests', 'failedTests', 'skippedTests']}

for scope, folder in [('main', 'ci-main-final'), ('benchmarks', 'ci-bench-final'), ('security-python', 'ci-security-python')]:
    receipt = read(f'{folder}/{scope}-result.json')
    assert receipt['commit'] == commit and receipt['status'] == 'passed'
    assert all(receipt['source_fingerprints'][name] == digest for name, digest in fingerprints.items())
    for step in receipt['steps']:
        assert step['exit_code'] == 0
        assert sha(Path(step['log'])) == step['log_sha256']
    result['workflows'][scope] = {'steps': [step['name'] for step in receipt['steps']], 'security_findings': receipt.get('security_findings')}

worker_path = r / 'ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker'
worker = read(str(worker_path.relative_to(r)) + '.build.json')
assert worker['source']['commit'] == commit
assert worker['binary_sha256'] == sha(worker_path)
assert all(worker['source']['files'][name] == digest for name, digest in fingerprints.items() if name.startswith('Sources/'))
acceptance = read('ci-bench-final/ci-acceptance/acceptance.json')
assert acceptance['status'] == 'failed' and acceptance['coverage_complete']
assert acceptance['source'] == worker['source']
policy = read('ci-bench-final/ci-acceptance/regression-policy.json')
assert policy['status'] == 'passed' and not policy['blocking']
assert policy['acceptance_sha256'] == sha(r / 'ci-bench-final/ci-acceptance/acceptance.json')
assert policy['source'] == worker['source'] and len(policy['known_failures']) == 4
assert all(failure['engine'] == 'pandas' and failure['classification'] == 'comparator-accuracy' for failure in policy['known_failures'])
assert sum(len(profile['failures']) for profile in acceptance['profiles']) == 4
assert all(not profile['infrastructure_errors'] for profile in acceptance['profiles'])
result['acceptance'] = {key: acceptance[key] for key in ['status', 'coverage_complete', 'profiles']}
result['regression_policy'] = {key: policy[key] for key in ['status', 'blocking', 'known_failures']}

compatibility = read('compatibility/result.json')
assert compatibility['status'] == 'passed'
assert all(step['exit_code'] == 0 for step in compatibility['steps'])
assert all(compatibility['sources'][name] == digest for name, digest in fingerprints.items())
result['compatibility'] = compatibility['swift']
regressions = read('compatibility-regressions/result.json')
assert regressions['exit_code'] == 0
assert all(regressions['sources'][name] == digest for name, digest in fingerprints.items())
assert 'Test run with 4 tests in 2 suites passed' in (r / 'compatibility-regressions/tests.log').read_text()
covered_errors = [int(line.split('|')[1]) for line in (r / 'compatibility-regressions/layout-coverage.txt').read_text().splitlines() if 'throw ClusterError' in line]
assert len(covered_errors) == 2 and all(count > 0 for count in covered_errors)
result['checked_layout_error_executions'] = covered_errors
assert read('layout-final/result.json')['exit_code'] == 0
result['limits'] = [
    'Swift CodeQL is unsupported with the retained Xcode 27 / Swift 6.4 toolchain.',
    'Native xccov output is not a library source coverage percentage.',
    'Large layout tests validate metadata without allocating the corresponding matrices.',
    'Four known Python Wampler reference failures remain under the unchanged acceptance policy.',
]
(r / 'qualification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
