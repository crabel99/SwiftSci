from pathlib import Path
import argparse, hashlib, json, os, random, subprocess, sys

p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--repeats', type=int, choices=range(1, 6), default=3)
a = p.parse_args()
r = a.root.resolve()
source = r / 'source'
sys.path[:0] = [str(source / 'Benchmarks/CoreMLInference'), str(source / 'Benchmarks/Tools')]
from bounded_process import execute
from runner import source_identity, verify_uninstrumented, metal_build_record
from trained import scores
import numpy as np
from scipy.special import expit

sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
save = lambda path, value: path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')
worker = Path('/private/tmp/swiftsci-coreml-representative-20261026/ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker')
build = json.loads(Path(str(worker) + '.build.json').read_text())
identity = source_identity(source)
assert identity == build['source'] and sha(worker) == build['binary_sha256']
verify_uninstrumented(worker)
assert metal_build_record(worker) == build['metal']
probe = r / 'probe/probe'
proof = json.loads((r / 'probe/proof.json').read_text())
assert sha(probe) == proof['binary_sha256']
assert sha(r / 'ProgramWorkflowProbe.swift') == proof['probe_source_sha256']
assert all(sha(Path(path)) == digest for path, digest in proof['objects'].items())
models = json.loads((r / 'models/provenance.json').read_text())
assert models['conversion_completed']
assert all(sha(Path(path)) == digest for path, digest in models['files'].items())
scalar = json.loads((r / 'scalar-reference.json').read_text())
assert scalar['script_sha256'] == sha(r / 'verify-scalar-reference.py')
cases = [(kind, bits, policy, repeat) for kind in ['wdbc', 'wine'] for bits in [16, 32]
         for policy in ['cpu', 'neural'] for repeat in range(a.repeats)]
random.Random(20261026).shuffle(cases)
a.output.mkdir(parents=True, exist_ok=False)
bound = {str(path): sha(path) for path in [Path(__file__).resolve(), r / 'ProgramWorkflowProbe.swift',
    r / 'models/provenance.json', r / 'scalar-reference.json', r / 'probe/proof.json']}
save(a.output / 'provenance.json', dict(source=identity, build=build, probe=proof,
    cases=cases, files=bound, models=models, scalar_reference=scalar,
    power=subprocess.check_output(['pmset', '-g', 'batt'], text=True),
    load_average=os.getloadavg(), application_quality_threshold='not established',
    tolerance=dict(atol=1e-5, rtol=1e-5), performance_baseline=False))
results = []
for kind, bits, policy, repeat in cases:
    folder = r / 'models' / kind
    metadata = json.loads((folder / 'training.json').read_text())
    fixture = json.loads((folder / 'frozen-fixture.json').read_text())
    raw = source / metadata['source_manifest']['fixture']
    name = f'{kind}-program{bits}-{policy}-{repeat}'
    result_path = a.output / (name + '.json')
    command = [str(probe), str(raw), str(folder / 'frozen-fixture.json'),
        str(folder / f'models/program{bits}.mlpackage'), policy, str(bits // 8), str(result_path)]
    save(a.output / (name + '.command.json'), command)
    print(name, flush=True)
    execute(command, a.output / (name + '.log'), 180)
    record = json.loads(result_path.read_text())
    assert record['rows'] == len(metadata['heldout_targets']) and len(record['samples']) == 36
    assert record['finalPoolReservedBytes'] == record['finalInputReservedBytes'] == 0
    assert record['invalidInputRecoveryVerified'] and record['crossPoolOwnerAndPreparationVerified']
    assert record['rawSHA256'] == metadata['source_manifest']['sha256']
    assert record['fixtureSHA256'] == sha(folder / 'frozen-fixture.json')
    assert record['transportElementBytes'] == bits // 8
    orders = [list(range(record['rows'])), list(reversed(range(record['rows']))),
        [(i // 2 * 7 + 3) % record['rows'] for i in range(record['rows'])]]
    hashes = {}
    for item in record['samples']:
        variant = item['variant']
        values = np.asarray(item['values'], dtype=np.float64)
        assert np.isfinite(values).all()
        assert item['originalRowIndices'] == [metadata['split_ids']['test'][i] for i in orders[variant]]
        expected = np.asarray(fixture['expected'])[orders[variant]]
        difference = np.abs(values - expected)
        assert abs(float(np.max(difference)) - item['maximumAbsoluteError']) < 1e-12
        assert int(np.count_nonzero(difference > 1e-5 + 1e-5 * np.abs(expected))) == item['mismatchedValues']
        assert item['outputSHA256'] == hashlib.sha256(values.astype('<f8').tobytes()).hexdigest()
        if variant in hashes:
            assert hashes[variant] == item['outputSHA256']
        hashes[variant] = item['outputSHA256']
    normal = next(item for item in record['samples'] if item['variant'] == 0 and item['route'] == 'direct')
    output = np.asarray(normal['values'])
    expected = np.asarray(fixture['expected'])
    quality = scores(kind, np.asarray(metadata['heldout_targets']), output,
        metadata['target_mean'], metadata['target_scale'])
    assessment = dict(dataset=kind, bits=bits, policy=policy, repeat=repeat,
        execution='completed', integration='verified',
        reference_accuracy='outside_tolerance' if any(x['mismatchedValues'] for x in record['samples']) else 'within_tolerance',
        maximum_absolute_error=max(x['maximumAbsoluteError'] for x in record['samples']),
        full_heldout_mismatched_values=normal['mismatchedValues'],
        application_suitability='not_assessed', task_quality=quality,
        original_reference_quality=metadata['quality']['test'],
        constant_quality=metadata['quality']['constant_test'], normal_output_sha256=normal['outputSHA256'],
        result_sha256=sha(result_path), complete_predictions=len(record['samples']))
    if kind == 'wdbc':
        assessment['label_disagreements'] = int(np.count_nonzero((output > 0) != (expected > 0)))
        assessment['maximum_probability_difference'] = float(np.max(np.abs(expit(output) - expit(expected))))
    peers = [x for x in results if x['dataset'] == kind and x['bits'] == bits and x['policy'] == policy]
    assert all(x['normal_output_sha256'] == assessment['normal_output_sha256'] for x in peers)
    results.append(assessment)
    save(a.output / 'assessment.json', results)
assert source_identity(source) == identity and sha(worker) == build['binary_sha256']
assert sha(probe) == proof['binary_sha256']
assert all(sha(Path(path)) == digest for path, digest in models['files'].items())
assert all(sha(Path(path)) == digest for path, digest in bound.items())
save(a.output / 'completed.json', dict(cases=len(results), predictions=sum(x['complete_predictions'] for x in results),
    reference_accuracy_met=all(x['reference_accuracy'] == 'within_tolerance' for x in results),
    integration='verified', application_suitability='not_assessed'))
print('All public workflow cases completed; strict precision results retained separately.', flush=True)
