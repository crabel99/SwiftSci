#!/usr/bin/env python3
"""Compare full-Float32-compute programs using frozen models and the existing public probe."""
import argparse
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def assess(record, metadata, fixture, policy, np):
    rows = len(metadata['heldout_targets'])
    require(record['rows'] == rows and record['columns'] == len(fixture['columns']) and
            record['policy'] == policy and record['transportElementBytes'] == 4, 'Probe request differs')
    require(len(record['samples']) == 36, 'Incomplete public workflow samples')
    require(record['finalPoolReservedBytes'] == record['finalInputReservedBytes'] == 0,
            'Outstanding input or pool reservation')
    require(record['invalidInputRecoveryVerified'] and record['crossPoolOwnerAndPreparationVerified'],
            'Recovery or ownership checks failed')
    require(record['concurrentCallers'] == 4 and record['poolSlots'] == 2, 'Concurrent test shape differs')
    require(record['maximumScalingError'] < 1e-10, 'Training-fitted scaling differs')
    expected_routes = dict(direct=11, prepared=11, fused=11, afterRejection=1,
                           crossPoolRetained=1, crossPoolPreparation=1)
    require(dict(Counter(item['route'] for item in record['samples'])) == expected_routes, 'Workflow routes differ')
    orders = [list(range(rows)), list(reversed(range(rows))), [(i // 2 * 7 + 3) % rows for i in range(rows)]]
    original = np.asarray(fixture['expected'], dtype=np.float64)
    hashes = {}
    for item in record['samples']:
        variant = item['variant']
        require(variant in range(3), 'Unknown input variant')
        order = orders[variant]
        values = np.asarray(item['values'], dtype=np.float64)
        require(values.shape == (rows,) and np.isfinite(values).all(), 'Incomplete or nonfinite outputs')
        require(item['originalRowIndices'] == [metadata['split_ids']['test'][i] for i in order],
                'Source-row identity differs')
        expected = original[order]
        differences = np.abs(values - expected)
        require(abs(float(np.max(differences)) - item['maximumAbsoluteError']) < 1e-12,
                'Reported maximum error differs')
        require(int(np.count_nonzero(differences > 1e-5 + 1e-5 * np.abs(expected))) == item['mismatchedValues'],
                'Reported strict mismatch count differs')
        output_hash = hashlib.sha256(values.astype('<f8').tobytes()).hexdigest()
        require(item['outputSHA256'] == output_hash, 'Output checksum differs')
        require(variant not in hashes or hashes[variant] == output_hash, 'Routes disagree on outputs')
        hashes[variant] = output_hash
        require(item['inputPackingBytes'] == rows * len(fixture['columns']) * 4 and
                item['outputCopyBytes'] == rows * 8, 'Logical byte counts differ')
    normal = next(item for item in record['samples'] if item['variant'] == 0 and item['route'] == 'direct')
    summary = dict(integration='verified', complete_samples=36,
        reference_accuracy='outside_tolerance' if any(s['mismatchedValues'] for s in record['samples']) else 'within_tolerance',
        maximum_absolute_error=max(s['maximumAbsoluteError'] for s in record['samples']),
        full_heldout_mismatched_values=normal['mismatchedValues'], normal_output_sha256=normal['outputSHA256'],
        application_suitability='not_assessed', original_reference_quality=metadata['quality']['test'],
        constant_quality=metadata['quality']['constant_test'])
    if metadata['dataset'] == 'wdbc':
        values = np.asarray(normal['values'], dtype=np.float64)
        summary['label_disagreements'] = int(np.count_nonzero((values > 0) != (original > 0)))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repeats', type=int, choices=range(1, 6), default=3)
    args = parser.parse_args()
    import numpy as np
    root = args.root.resolve(strict=True)
    sys.path.insert(0, str(root / 'source/Benchmarks/CoreMLInference'))
    from bounded_process import execute
    output = args.output.resolve()
    converter = root / 'source/Benchmarks/CoreMLInference/prepare_models.py'
    original = converter.read_text()
    replacements = [('for io16 in [False, True]:', 'for io16 in [False]:'),
                    ('compute_precision=ct.precision.FLOAT16,', 'compute_precision=ct.precision.FLOAT32,'),
                    ("program_compute_precision='float16'", "program_compute_precision='float32'")]
    derived = original
    for before, after in replacements:
        require(derived.count(before) == 1, 'Expected exactly one converter expression: ' + before)
        derived = derived.replace(before, after)
    models_path = root / 'models/provenance.json'
    models = json.loads(models_path.read_text())
    require(models['conversion_completed'], 'Frozen model preparation incomplete')
    require(all(sha(Path(path)) == digest for path, digest in models['files'].items()), 'Prepared provenance differs')
    probe = root / 'probe/probe'
    proof_path = root / 'probe/proof.json'
    proof = json.loads(proof_path.read_text())
    require(sha(probe) == proof['binary_sha256'], 'Probe binary differs')
    require(sha(root / 'ProgramWorkflowProbe.swift') == proof['probe_source_sha256'], 'Probe source differs')
    require(all(sha(Path(path)) == digest for path, digest in proof['objects'].items()), 'Linked objects differ')
    output.mkdir(parents=True, exist_ok=False)
    original_copy = output / 'prepare_models-original.py'
    original_copy.write_bytes(converter.read_bytes())
    derived_path = output / 'prepare_models-float32.py'
    derived_path.write_text(derived)
    (output / 'converter.diff').write_text(''.join(difflib.unified_diff(
        original.splitlines(True), derived.splitlines(True), fromfile='prepare_models-original.py',
        tofile='prepare_models-float32.py')))
    bound = {str(path): sha(path) for path in [Path(__file__).resolve(), converter, original_copy,
        root / 'source/Benchmarks/CoreMLInference/bounded_process.py',
        derived_path, output / 'converter.diff', models_path, proof_path, probe, root / 'ProgramWorkflowProbe.swift']}
    bound.update(proof['objects'])
    bound.update(models['files'])
    provenance = dict(schema_version=1, root=str(root), python=sys.version, executable=sys.executable,
        numpy=np.__version__, source_commit=subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=root / 'source', text=True).strip(),
        files=bound, converter_replacements=replacements, program_compute_precision='float32',
        transport='float32', inference_reference_tolerance=dict(atol=1e-5, rtol=1e-5),
        repeats=args.repeats, retraining=False, application_quality_threshold='not established',
        performance_evidence=False, models=[], cases=[])
    save(output / 'provenance.json', provenance)
    for kind in ['wdbc', 'wine']:
        directory = output / kind
        directory.mkdir()
        fixture = root / 'models' / kind / 'fixture.json'
        model_dir = directory / 'models'
        command = [sys.executable, str(derived_path), '--fixture', str(fixture), '--output', str(model_dir)]
        save(directory / 'conversion-command.json', command)
        print('Converting full-Float32 control: ' + kind, flush=True)
        start = time.perf_counter()
        execute(command, directory / 'conversion.log', 300)
        elapsed = time.perf_counter() - start
        manifest_path = model_dir / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        original_manifest = json.loads((root / 'models' / kind / 'models/manifest.json').read_text())
        require(manifest['fixture_sha256'] == sha(fixture), 'Control fixture identity differs')
        require(manifest['program_compute_precision'] == 'float32', 'Control compute precision differs')
        require(all(manifest[key] == original_manifest[key] for key in ['rows', 'width', 'outputs', 'fixture_sha256']),
                'Control model shape or weights fixture differs')
        require((model_dir / 'program32.mlpackage').is_dir() and not (model_dir / 'program16.mlpackage').exists(),
                'Unexpected control artifacts')
        for name, digest in manifest['files'].items():
            require(sha(model_dir / name) == digest, 'Control model file changed: ' + name)
        provenance['models'].append(dict(dataset=kind, manifest=manifest, conversion_seconds=elapsed,
                                         model=str(model_dir / 'program32.mlpackage')))
        bound.update({str(path): sha(path) for path in directory.rglob('*') if path.is_file()})
        save(output / 'provenance.json', provenance)
    cases = [(kind, policy, repeat) for kind in ['wdbc', 'wine'] for policy in ['cpu', 'neural']
             for repeat in range(args.repeats)]
    random.Random(20261026).shuffle(cases)
    provenance['cases'] = cases
    save(output / 'provenance.json', provenance)
    results = []
    for kind, policy, repeat in cases:
        folder = root / 'models' / kind
        metadata = json.loads((folder / 'training.json').read_text())
        fixture_path = folder / 'frozen-fixture.json'
        fixture = json.loads(fixture_path.read_text())
        raw = root / 'source' / metadata['source_manifest']['fixture']
        bound[str(raw)] = sha(raw)
        name = '%s-float32-%s-%d' % (kind, policy, repeat)
        result_path = output / (name + '.json')
        command = [str(probe), str(raw), str(fixture_path),
            str(output / kind / 'models/program32.mlpackage'), policy, '4', str(result_path)]
        save(output / (name + '.command.json'), command)
        print(name, flush=True)
        execute(command, output / (name + '.log'), 180)
        record = json.loads(result_path.read_text())
        require(record['rawSHA256'] == metadata['source_manifest']['sha256'] and
                record['fixtureSHA256'] == sha(fixture_path), 'Probe input identity differs')
        summary = assess(record, metadata, fixture, policy, np)
        summary.update(dataset=kind, policy=policy, repeat=repeat, result_sha256=sha(result_path))
        peers = [item for item in results if item['dataset'] == kind and item['policy'] == policy]
        require(all(item['normal_output_sha256'] == summary['normal_output_sha256'] for item in peers),
                'Independent processes disagree')
        results.append(summary)
        save(output / 'assessment.json', results)
    for path, digest in bound.items():
        require(sha(Path(path)) == digest, 'Source or artifact changed: ' + path)
    bound.update({str(path): sha(path) for path in output.iterdir()
                  if path.is_file() and path.name not in ['provenance.json', 'completed.json']})
    save(output / 'provenance.json', provenance)
    accurate = all(item['reference_accuracy'] == 'within_tolerance' for item in results)
    save(output / 'completed.json', dict(cases=len(results), predictions=36 * len(results),
        integration='verified', reference_accuracy_met=accurate, program_compute_precision='float32',
        transport='float32', application_suitability='not_assessed', performance_evidence=False))
    print('Full-Float32 control complete; strict accuracy met: ' + str(accurate), flush=True)


if __name__ == '__main__':
    main()
