from pathlib import Path
import argparse, hashlib, json, os, plistlib, shutil, signal, subprocess, sys

p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--resume', action='store_true')
a = p.parse_args()
r = a.root.resolve()
source = r / 'source'
sys.path[:0] = [str(source / 'Benchmarks/CoreMLInference'), str(source / 'Benchmarks/Tools')]
from concurrency import validate
from runner import source_identity, verify_uninstrumented, metal_build_record

sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
save = lambda path, value: path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
worker = Path('/private/tmp/swiftsci-coreml-representative-20261026/ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker')
build = json.loads(Path(str(worker) + '.build.json').read_text())
identity = source_identity(source)
assert identity == build['source'] and sha(worker) == build['binary_sha256']
verify_uninstrumented(worker)
assert metal_build_record(worker) == build['metal']
assert json.loads((r / 'concurrency/completed.json').read_text())['integration'] == 'verified'
comparisons = json.loads((r / 'concurrency/summary.json').read_text())
models = json.loads((r / 'models/provenance.json').read_text())
assert all(sha(Path(path)) == digest for path, digest in models['files'].items())
a.output.mkdir(parents=True, exist_ok=a.resume)
profile = a.output / 'ProfileWorker'
entitlements = a.output / 'entitlements.plist'
if profile.exists():
    assert a.resume
    subprocess.run(['codesign', '--verify', '--strict', str(profile)], check=True)
else:
    shutil.copy2(worker, profile)
    assert sha(profile) == build['binary_sha256']
    entitlements.write_bytes(plistlib.dumps({'com.apple.security.get-task-allow': True}))
    subprocess.run(['codesign', '--force', '--sign', '-', '--entitlements', str(entitlements), str(profile)], check=True)
for file in [*worker.parent.glob('*.bundle'), *worker.parent.glob('*.metallib')]:
    target = a.output / file.name
    if target.exists():
        assert a.resume and target.resolve() == file.resolve()
    else:
        target.symlink_to(file)
bound = {str(path): sha(path) for path in [Path(__file__).resolve(), r / 'models/provenance.json',
    r / 'concurrency/summary.json', r / 'concurrency/completed.json']}
for version in ['trace-programs-before.py', 'trace-programs-resume-capture.py']:
    if (r / version).exists():
        bound[str(r / version)] = sha(r / version)
records = []
prior = json.loads((a.output / 'recordings.json').read_text()) if (a.output / 'recordings.json').exists() else []
prior = {item['name']: item for item in prior}
for kind in ['wdbc', 'wine']:
    folder = r / 'models' / kind
    metadata = json.loads((folder / 'training.json').read_text())
    for bits in [16, 32]:
        for policy in ['cpu', 'neural']:
            name = f'{kind}-program{bits}-{policy}'
            baseline = next(item for item in comparisons if item['dataset'] == kind and item['bits'] == bits
                and item['policy'] == policy and item['mode'] == 'persistent' and item['slots'] == 1)
            request = dict(modelPackage=str(folder / f'models/program{bits}.mlpackage'),
                execution='persistent', retainedBytes=33_554_432, fixture=str(folder / 'fixture.json'),
                rows=len(metadata['heldout_targets']), policy=policy, callers=1, instances=1,
                admissionSlots=1, seconds=2, rssLimitBytes=1_073_741_824)
            request_path = a.output / (name + '.request.json')
            result_path = a.output / (name + '.json')
            trace = a.output / (name + '.trace')
            if request_path.exists():
                assert a.resume and json.loads(request_path.read_text()) == request
            else:
                save(request_path, request)
            command = ['xcrun', 'xctrace', 'record', '--template', 'Time Profiler',
                '--instrument', 'Core ML', '--instrument', 'Neural Engine', '--instrument', 'Points of Interest',
                '--time-limit', '42s', '--output', str(trace), '--no-prompt', '--launch', '--',
                str(profile), '--coreml-concurrency', str(request_path), str(result_path)]
            if trace.exists():
                assert a.resume and result_path.exists(), 'Preserve incomplete recording and investigate before retrying'
                driver_status = prior.get(name, {}).get('recording_driver_status',
                    'completed_before_resume' if name in prior else 'recovered_saved_trace_after_driver_timeout')
                capture_controller = prior.get(name, {}).get('capture_controller_sha256')
                if capture_controller is None:
                    version = 'trace-programs-resume-capture.py' if driver_status == 'exited_zero' else 'trace-programs-before.py'
                    capture_controller = sha(r / version)
                print('Validate saved ' + name, flush=True)
            else:
                save(a.output / (name + '.command.json'), command)
                print(name, flush=True)
                with (a.output / (name + '.log')).open('w') as log:
                    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                    try:
                        code = process.wait(timeout=92)
                    except subprocess.TimeoutExpired:
                        process.send_signal(signal.SIGINT)
                        try:
                            code = process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            code = process.wait(timeout=5)
                    finally:
                        if process.poll() is None:
                            process.kill()
                            process.wait(timeout=5)
                        owned = str(profile) + ' --coreml-concurrency ' + str(request_path) + ' '
                        for line in subprocess.check_output(['ps', '-axo', 'pid=,command='], text=True).splitlines():
                            parts = line.strip().split(None, 1)
                            if len(parts) == 2 and parts[1].startswith(owned):
                                try:
                                    os.kill(int(parts[0]), signal.SIGKILL)
                                except ProcessLookupError:
                                    pass
                driver_status = 'exited_zero' if code == 0 else f'nonzero_driver_{code}_saved_trace_requires_validation'
                capture_controller = sha(Path(__file__).resolve())
                assert trace.exists() and result_path.exists(), name
            record = json.loads(result_path.read_text())
            validate(record, request)
            assert record['modelSHA256'] == baseline['model_sha256']
            assert record['outputHashes'] == baseline['output_hashes']
            assert record['preflightReferenceMismatches'] == baseline['reference_mismatches']
            toc = a.output / (name + '.toc.xml')
            if not toc.exists():
                subprocess.run(['xcrun', 'xctrace', 'export', '--input', str(trace), '--toc', '--output', str(toc)], check=True, timeout=60)
            import xml.etree.ElementTree as E
            target = E.parse(toc).find('./run/info/target/process')
            assert target.get('name') == 'ProfileWorker' and target.get('return-exit-status') == '0'
            if name in prior:
                assert sha(toc) == prior[name]['toc_sha256'] and sha(result_path) == prior[name]['result_sha256']
            records.append(dict(name=name, dataset=kind, bits=bits, policy=policy,
                recording_driver_status=driver_status,
                capture_controller_sha256=capture_controller,
                model_sha256=record['modelSHA256'], result_sha256=sha(result_path), toc_sha256=sha(toc),
                completed_requests=sum(caller['latency']['count'] for caller in record['callers'])))
            save(a.output / 'recordings.json', records)
assert source_identity(source) == identity and sha(worker) == build['binary_sha256']
assert all(sha(Path(path)) == digest for path, digest in models['files'].items())
assert all(sha(Path(path)) == digest for path, digest in bound.items())
save(a.output / 'provenance.json', dict(source=identity, build=build, files=bound,
    prior_capture_controller_sha256=sha(r / 'trace-programs-before.py') if (r / 'trace-programs-before.py').exists() else None,
    profiling_worker_sha256=sha(profile), performance_evidence=False,
    scope='Existing public persistent matrix pool, one caller, typed weighted ML Programs. Inspect target-model device events inside the CoreML measurement signpost.'))
print('Recordings complete; event inspection is still required.', flush=True)
