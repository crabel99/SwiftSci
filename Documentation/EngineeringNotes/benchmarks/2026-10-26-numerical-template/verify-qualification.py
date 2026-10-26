from pathlib import Path
import argparse
import hashlib
import json
import subprocess

parser = argparse.ArgumentParser(description='Verify retained numerical-template evidence without building or launching Swift.')
parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
parser.add_argument('--library-root', type=Path, default=Path('/private/tmp/swiftsci-llm-completion-20261026'))
args = parser.parse_args()
root = args.root.resolve()
source = args.library_root.resolve() / 'source'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda name: json.loads((root / name).read_text())
head = '0e1635199654ac6a20b32ea53eea0ffdfa39e747'
git = lambda *parts: subprocess.check_output(['git', *parts], cwd=source, text=True).strip()
assert git('rev-parse', 'HEAD') == head
assert git('status', '--porcelain') == '', 'Source cleanup is a qualification precondition'
provenance = read('final-run-qualified/provenance.json')
verification = read('final-run-qualified/verification.json')
attempts = read('final-run-qualified/attempts.json')
assert provenance['source'] == verification['source'] == head
assert len(attempts) == 2 and all(item['exit_code'] == 0 for item in attempts)
assert provenance['runner_sha256'] == sha(root / 'run-template.py')
build = provenance['build']
build_path = args.library_root / 'ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker.build.json'
assert sha(build_path) == provenance['worker_build_sha256']
assert json.loads(build_path.read_text()) == build and build['source']['commit'] == head
assert all(sha(source / name) == digest for name, digest in build['source']['files'].items())
log = Path(build['log']).resolve()
assert sha(log) == provenance['input_build_log_sha256']
for name, proof in provenance['proofs'].items():
    probe = root / f'final-{name}-probe'
    assert json.loads((probe / 'proof.json').read_text()) == proof
    assert sha(probe / 'probe') == proof['binary_sha256']
    assert Path(proof['input_build_log']).resolve() == log
    assert proof['input_build_log_sha256'] == sha(log)
    assert all(Path(path).resolve().is_relative_to(build_path.parent.resolve()) for path in proof['objects'])
    assert all(sha(Path(path)) == digest for path, digest in proof['objects'].items())
    assert '-package-name' not in proof['compile'] and '-enable-testing' not in proof['compile']
    consumer = 'ScientificWorkflow.swift' if name == 'prepared' else 'LegacyWorkflowProbe.swift'
    assert proof['probe_source_sha256'] == sha(root / consumer)
for name in ['prepared', 'legacy']:
    digest = sha(root / f'final-run-qualified/{name}.json')
    assert digest == provenance[f'{name}_result_sha256'] == verification[f'{name}_sha256']
assert verification['verifier_sha256'] == sha(root / 'verify-template.py')
subprocess.run(['python3', str(root / 'verify-template.py'), '--run', str(root / 'final-run-qualified')], check=True, stdout=subprocess.DEVNULL)
assert read('final-run-qualified/verification.json') == verification
assert verification['status'] == 'passed'
negative = read('mismatched-build-rejection-final.json')
assert negative['exit_code'] != 0 and 'Probe belongs to a different library build' in negative['stderr']
assert negative['runner_sha256'] == sha(root / 'run-template.py')
assert not any((root / 'rejected-mismatched-build-final').iterdir())
binding = read('package-source-binding.json')
assert binding['source'] == head
assert binding['template_source_sha256'] == sha(root / 'ScientificWorkflow.swift')
assert binding['original_manifest_sha256'] == sha(root / 'template/Package.swift')
assert binding['local_manifest_sha256'] == sha(root / 'template-local/Package.swift')
assert binding['resolved_sha256'] == sha(root / 'template-local/Package.resolved')
remote = (root / 'template/Package.swift').read_text()
local = (root / 'template-local/Package.swift').read_text()
replacement = f'.package(url: "https://github.com/crabel99/SwiftSci.git",\n                 revision: "{head}")'
assert remote.replace(replacement, f'.package(name: "SwiftSci", path: "{source}")') == local
consumer_bytes = (root / 'ScientificWorkflow.swift').read_bytes()
assert all((root / folder / 'Sources/ScientificWorkflow/ScientificWorkflow.swift').read_bytes() == consumer_bytes for folder in ['template', 'template-local'])
assert read('package-result.json') == read('final-run-qualified/prepared.json')
assert '** BUILD SUCCEEDED **' in (root / 'package-build.log').read_text()
remote = read('remote-package/receipt.json')
assert remote['status'] == 'passed' and remote['source'] == head
assert remote['controller_sha256'] == sha(root / 'check-remote-package.py')
assert remote['manifest_sha256'] == sha(root / 'template/Package.swift')
assert remote['consumer_sha256'] == sha(root / 'template/Sources/ScientificWorkflow/ScientificWorkflow.swift')
assert [step['name'] for step in remote['steps']] == ['resolve', 'build', 'run']
for step in remote['steps']:
    assert step['exit_code'] == 0
    assert step['log_sha256'] == sha(root / 'remote-package' / (step['name'] + '.log'))
assert '** BUILD SUCCEEDED **' in (root / 'remote-package/build.log').read_text()
checkout = root / 'remote-package/packages/checkouts/SwiftSci'
checkout_git = lambda *parts: subprocess.check_output(['git', *parts], cwd=checkout, text=True).strip()
assert checkout_git('rev-parse', 'HEAD') == remote['remote_checkout']['commit'] == head
assert checkout_git('status', '--porcelain') == ''
names = checkout_git('ls-files', 'Sources', 'Package.swift').splitlines()
assert set(names) == set(remote['remote_checkout']['files'])
assert all(sha(checkout / name) == digest == sha(source / name) for name, digest in remote['remote_checkout']['files'].items())
mirror = Path(checkout_git('remote', 'get-url', 'origin')).resolve()
assert mirror == Path(remote['remote_checkout']['remote']).resolve()
mirror_url = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url'], cwd=mirror, text=True).strip()
assert mirror_url == 'https://github.com/crabel99/SwiftSci.git'
pins = read('template/Package.resolved')
assert pins['originHash'] == remote['manifest_sha256']
swiftsci_pin = [pin for pin in pins['pins'] if pin['identity'] == 'swiftsci']
assert len(swiftsci_pin) == 1 and swiftsci_pin[0]['state']['revision'] == head
assert swiftsci_pin[0]['location'] == mirror_url
checkouts = {path.name.lower(): path for path in checkout.parent.iterdir() if path.is_dir()}
for pin in pins['pins']:
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkouts[pin['identity']], text=True).strip()
    assert actual == pin['state']['revision']
binary = root / 'remote-package/derived/Build/Products/Release/ScientificWorkflow'
assert remote['steps'][2]['command'] == [str(binary)]
assert remote['binary_sha256'] == sha(binary)
assert remote['result_sha256'] == sha(root / 'remote-package/result.json')
assert read('remote-package/result.json') == read('final-run-qualified/prepared.json')
assert "PreparedNumericMatrix' has no member 'rowValues'" in (root / 'public-probe/compile.log').read_text()
assert 'No Metal device available' in (root / 'final-run-bound/prepared.json').read_text()
assert 'No open findings after re-review' in (root / 'standards-review.md').read_text()
assert 'No spec findings' in (root / 'spec-review.md').read_text()
files = [
    'README.md', 'plan.md', 'standards-review.md', 'spec-review.md', 'audit.md',
    'ScientificWorkflow.swift', 'LegacyWorkflowProbe.swift', 'ScientificWorkflow-before-compile-correction.swift',
    'public-probe/compile.log', 'prepared-run.log', 'run-template-before-binding-fix.py',
    'run-template.py', 'verify-template.py', 'verify-qualification.py', 'package-records.py', 'verify-publication.py',
    'mismatched-build-rejection-final.json', 'package-source-binding.json', 'local-manifest.diff',
    'package-manifest.json', 'package-build.log', 'package-result.json', 'package-run.log',
    'template/Package.swift', 'template/README.md', 'template/Sources/ScientificWorkflow/ScientificWorkflow.swift',
    'template-local/Package.swift', 'template-local/Package.resolved',
    'check-remote-package.py', 'remote-package-review.md', 'template/Package.resolved',
    'remote-package/receipt.json', 'remote-package/resolve.log', 'remote-package/build.log',
    'remote-package/run.log', 'remote-package/result.json',
    'final-run-bound/prepared.json', 'final-run-bound/prepared.log',
] + [f'final-run-qualified/{name}' for name in ['attempts.json', 'prepared.json', 'prepared.log', 'legacy.json', 'legacy.log', 'provenance.json', 'verification.json']]
result = dict(
    status='passed', source=head, authoritative_run='final-run-qualified',
    source_cleanup_precondition='Exact HEAD, empty git status, and all recorded source file hashes verified',
    positive=dict(probe_exit_codes=[item['exit_code'] for item in attempts],
                  maximum_absolute_error=max(verification['maximum_absolute_errors'].values()),
                  tolerance=verification['tolerance'], predictions=verification['predictions']),
    negative_control='Old probes rejected before execution by selected-build binding; recorded exit 1',
    package_build='Passed with verified local dependency substitution; source bytes and output equal qualified probe',
    remote_package=dict(status='passed', checkout_commit=head, checkout_source_files=len(names),
                        upstream_url=mirror_url, controller_sha256=remote['controller_sha256'],
                        resolved_sha256=sha(root / 'template/Package.resolved'),
                        pins=pins['pins'], step_exit_codes=[step['exit_code'] for step in remote['steps']],
                        binary_sha256=remote['binary_sha256'], result_sha256=remote['result_sha256'],
                        result='Resolve, fresh native build and run passed; exact qualified JSON equality'),
    preserved_failures=dict(initial_compile='Matrix rowValues call failed; corrected by removing unnecessary conversion',
                            initial_launch='No probe executable existed after failed compilation',
                            final_run_bound='Sandbox launch emitted no-Metal-device diagnostic; no valid numerical result or passing verdict'),
    limits=['Toy integration fixture, not statistical-quality, performance or memory qualification',
            'Receipt verification reads retained artifacts and recomputes the scalar oracle; it does not build or launch Swift',
            'Original qualification requires retained local and remote checkouts/builds/probes; publication verification is standalone'],
    artifacts={name: sha(root / name) for name in files})
(root / 'qualification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: value for key, value in result.items() if key != 'artifacts'}, indent=2))
