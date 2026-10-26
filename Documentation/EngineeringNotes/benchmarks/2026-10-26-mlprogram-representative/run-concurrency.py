from pathlib import Path
import argparse, hashlib, json, os, random, sys

p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--seconds', type=int, choices=range(1, 61), default=8)
p.add_argument('--sustain-seconds', type=int, choices=range(0, 301), default=60)
a = p.parse_args()
r = a.root.resolve()
source = r / 'source'
sys.path[:0] = [str(source / 'Benchmarks/CoreMLInference'), str(source / 'Benchmarks/Tools')]
from concurrency import run_case
from program_pool import validate_backing_counts
from runner import source_identity, verify_uninstrumented, metal_build_record

sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
save = lambda path, value: path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')
worker = Path('/private/tmp/swiftsci-coreml-representative-20261026/ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker')
build = json.loads(Path(str(worker) + '.build.json').read_text())
identity = source_identity(source)
assert build['source'] == identity and sha(worker) == build['binary_sha256']
verify_uninstrumented(worker)
assert metal_build_record(worker) == build['metal']
models = json.loads((r / 'models/provenance.json').read_text())
assert models['conversion_completed'] and all(sha(Path(path)) == digest for path, digest in models['files'].items())
workflows = json.loads((r / 'workflows/assessment.json').read_text())
assert json.loads((r / 'workflows/completed.json').read_text())['integration'] == 'verified'
cases = [(kind, bits, policy, mode, slots, a.seconds, 'sweep')
    for kind in ['wdbc', 'wine'] for bits in [16, 32] for policy in ['cpu', 'neural']
    for mode in ['synchronous', 'asynchronous', 'persistent'] for slots in [1, 2]]
random.Random(20261026).shuffle(cases)
if a.sustain_seconds:
    cases += [(kind, 16, policy, 'persistent', 2, a.sustain_seconds, 'sustained')
              for kind in ['wdbc', 'wine'] for policy in ['cpu', 'neural']]
a.output.mkdir(parents=True, exist_ok=False)
bound = {str(path): sha(path) for path in [Path(__file__).resolve(), r / 'models/provenance.json',
    r / 'workflows/assessment.json', source / 'Benchmarks/CoreMLInference/concurrency.py',
    source / 'Benchmarks/CoreMLInference/program_pool.py']}
save(a.output / 'provenance.json', dict(source=identity, build=build, cases=cases, files=bound,
    load_average=os.getloadavg(), performance_baseline=False,
    timing_scope='Existing concurrency worker: latency includes actor queue, admission, input packing, native call and owned output. Throughput also includes full-output hashing. No compilation or other benchmark runs overlap.'))
results = []
for kind, bits, policy, mode, slots, duration, phase in cases:
    folder = r / 'models' / kind
    metadata = json.loads((folder / 'training.json').read_text())
    name = f'{phase}-{kind}-program{bits}-{policy}-{mode}-s{slots}'
    request = dict(modelPackage=str(folder / f'models/program{bits}.mlpackage'),
        execution=mode, fixture=str(folder / 'fixture.json'), rows=len(metadata['heldout_targets']),
        policy=policy, callers=1 if slots == 1 else 4, instances=1, admissionSlots=slots,
        seconds=duration, rssLimitBytes=1_073_741_824)
    if mode == 'persistent':
        request['retainedBytes'] = 33_554_432
    print(name, flush=True)
    record = run_case(worker, a.output, name, request)
    validate_backing_counts(record)
    baseline = next(item for item in workflows if item['dataset'] == kind and item['bits'] == bits and item['policy'] == policy)
    assert record['outputHashes'][0] == baseline['normal_output_sha256']
    assert record['preflightReferenceMismatches'] == baseline['full_heldout_mismatched_values']
    assert record['transportElementBytes'] == bits // 8
    result = dict(name=name, dataset=kind, bits=bits, policy=policy, mode=mode, slots=slots, phase=phase,
        requests=sum(caller['latency']['count'] for caller in record['callers']),
        elapsed_seconds=record['elapsedSeconds'], rss_first=record['memory'][0]['residentBytes'],
        rss_last=record['memory'][-1]['residentBytes'], rss_peak_sampled=max(point['residentBytes'] for point in record['memory']),
        reference_mismatches=record['preflightReferenceMismatches'], output_hashes=record['outputHashes'],
        cancelled_requests_verified=record['cancelledRequestsVerified'],
        output_backing_identity_matches=record.get('poolOutputBackingIdentityMatches'),
        pool_predictions=record.get('poolPredictions'), model_sha256=record['modelSHA256'],
        result_sha256=sha(a.output / (name + '.json')))
    peers = [item for item in results if item['dataset'] == kind and item['bits'] == bits and item['policy'] == policy]
    assert all(item['model_sha256'] == result['model_sha256'] and item['output_hashes'] == result['output_hashes'] for item in peers)
    results.append(result)
    save(a.output / 'summary.json', results)
assert source_identity(source) == identity and sha(worker) == build['binary_sha256']
assert all(sha(Path(path)) == digest for path, digest in models['files'].items())
assert all(sha(Path(path)) == digest for path, digest in bound.items())
save(a.output / 'completed.json', dict(cases=len(results), requests=sum(item['requests'] for item in results),
    integration='verified', strict_reference_accuracy_met=False,
    scope='All per-request and lifetime ownership checks passed; strict precision exceedances retained. Persistent cancellation is covered by existing unit tests, not this stress run.'))
print('Concurrency and bounded sustained cases completed.', flush=True)
