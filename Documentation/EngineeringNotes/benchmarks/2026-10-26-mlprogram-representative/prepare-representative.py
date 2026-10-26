#!/usr/bin/env python3
"""Convert verified frozen WDBC/wine fixtures with the existing model converter."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

for key in ('VECLIB_MAXIMUM_THREADS', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[key] = '1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def prepare_fixture(source, frozen, output, kind, rows, np):
    original = frozen / 'fixtures' / ('%s-%d.json' % (kind, rows))
    metadata_path = frozen / 'fixtures' / (kind + '-training.json')
    fixture = json.loads(original.read_text())
    metadata = json.loads(metadata_path.read_text())
    require(metadata['dataset'] == kind, 'Training metadata dataset differs')
    require(digest(original) == metadata['fixture_hashes'][str(rows)], 'Frozen fixture checksum differs')
    require(fixture['layers'] == metadata['layers'], 'Frozen fixture parameters differ from training metadata')
    require(len(metadata['heldout_targets']) == rows == len(metadata['test_row_ids']), 'Heldout row count differs')
    source_fixture = source / metadata['source_manifest']['fixture']
    require(digest(source_fixture) == metadata['source_manifest']['sha256'], 'Repository dataset checksum differs')
    raw = json.loads(source_fixture.read_text())
    require(raw['splits'] == metadata['split_ids'], 'Repository splits differ from frozen training')
    require([raw['row_ids'][i] for i in raw['splits']['test']] == metadata['test_row_ids'],
            'Heldout source-row identities differ')
    require(np.array_equal(np.asarray(raw['targets'], dtype=np.float64)[raw['splits']['test']],
                           np.asarray(metadata['heldout_targets'], dtype=np.float64)),
            'Heldout targets differ')
    inputs = np.asarray(fixture['columns'], dtype=np.float64).T.copy()
    expected = np.asarray(fixture['expected'], dtype=np.float64)
    require(inputs.ndim == 2 and inputs.shape[0] == rows and np.isfinite(inputs).all(), 'Invalid frozen inputs')
    value = inputs
    for index, layer in enumerate(fixture['layers']):
        weights = np.asarray(layer['W'], dtype=np.float64).reshape(layer['inDim'], layer['outDim'])
        biases = np.asarray(layer['b'], dtype=np.float64)
        require(np.isfinite(weights).all() and np.isfinite(biases).all(), 'Nonfinite frozen parameters')
        require(np.array_equal(weights, weights.astype(np.float32).astype(np.float64)) and
                np.array_equal(biases, biases.astype(np.float32).astype(np.float64)),
                'Frozen parameters are not the shared Float32 values')
        value = value @ weights + biases
        if index < len(fixture['layers']) - 1:
            value = np.maximum(value, 0)
    require(value.shape == (rows, 1) and expected.shape == (rows,), 'Unexpected representative output shape')
    require(np.isfinite(value).all() and np.isfinite(expected).all(), 'Nonfinite independent reference')
    np.testing.assert_allclose(value[:, 0], expected, atol=1e-12, rtol=1e-12)
    directory = output / kind
    directory.mkdir()
    shutil.copyfile(original, directory / 'frozen-fixture.json')
    shutil.copyfile(metadata_path, directory / 'training.json')
    binary_entries = {}
    for key, name, values in [('inputBinary', 'input.f64', inputs),
                               ('expectedBinary', 'expected.f64', expected.reshape(rows, 1))]:
        binary = directory / name
        payload = np.ascontiguousarray(values, dtype='<f8').tobytes(order='C')
        binary.write_bytes(payload)
        restored = np.frombuffer(binary.read_bytes(), dtype='<f8').reshape(values.shape)
        require(restored.tobytes() == np.ascontiguousarray(values, dtype='<f8').tobytes(), 'Binary roundtrip differs')
        binary_entries[key] = dict(path=name, rows=rows, columns=values.shape[1], sha256=digest(binary))
    descriptor = directory / 'fixture.json'
    save(descriptor, dict(layers=fixture['layers'], **binary_entries))
    require(json.loads(descriptor.read_text())['layers'] == fixture['layers'], 'Derived parameters differ')
    files = {str(path.resolve()): digest(path) for path in
             [original, metadata_path, source_fixture, directory / 'frozen-fixture.json',
              directory / 'training.json', descriptor, directory / 'input.f64', directory / 'expected.f64']}
    return dict(dataset=kind, rows=rows, width=inputs.shape[1], outputs=1,
                original_fixture=str(original), training_metadata=str(metadata_path),
                fixture=str(descriptor.resolve()), models=str((directory / 'models').resolve()),
                independent_reference=dict(atol=1e-12, rtol=1e-12,
                    maximum_absolute_difference=float(np.max(np.abs(value[:, 0] - expected)))),
                files=files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--frozen', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    import numpy as np
    source = args.source.resolve(strict=True)
    frozen = args.frozen.resolve(strict=True)
    output = args.output.resolve()
    converter = source / 'Benchmarks/CoreMLInference/prepare_models.py'
    prior_controller = source / 'Benchmarks/CoreMLInference/trained.py'
    prior_provenance_path = frozen / 'provenance.json'
    prior = json.loads(prior_provenance_path.read_text())
    require(prior['controller_sha256'] == digest(prior_controller), 'Frozen training controller checksum differs')
    require(prior['build']['source'] == prior['source'], 'Frozen source/build identities differ')
    script = Path(__file__).resolve()
    bound = {str(path): digest(path) for path in [script, converter, prior_controller, prior_provenance_path]}
    output.mkdir(parents=True, exist_ok=False)
    provenance = dict(schema_version=1, source=str(source), frozen=str(frozen),
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip(),
        source_status=subprocess.check_output(['git', 'status', '--porcelain'], cwd=source, text=True),
        python=sys.version, executable=sys.executable, numpy=np.__version__,
        frozen_provenance=prior, files=bound, datasets=[],
        reference_tolerance=dict(atol=1e-12, rtol=1e-12),
        converted_model_compute_precision='float16', program32_transport='float32', program16_transport='float16',
        retraining=False, conversion_completed=False)
    save(output / 'provenance.json', provenance)
    for kind, rows in [('wdbc', 126), ('wine', 342)]:
        record = prepare_fixture(source, frozen, output, kind, rows, np)
        provenance['datasets'].append(record)
        provenance['files'].update(record['files'])
        command = [sys.executable, str(converter), '--fixture', record['fixture'], '--output', record['models']]
        directory = output / kind
        save(directory / 'conversion-command.json', command)
        save(output / 'provenance.json', provenance)
        print('Converting frozen %s, %d rows' % (kind, rows), flush=True)
        start = time.perf_counter()
        with (directory / 'conversion.log').open('w') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        record['conversion_seconds'] = time.perf_counter() - start
        record['conversion_exit_code'] = result.returncode
        save(output / 'provenance.json', provenance)
        require(result.returncode == 0, 'Model conversion failed; inspect ' + str(directory / 'conversion.log'))
        model_dir = Path(record['models'])
        manifest_path = model_dir / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        require(manifest['fixture_sha256'] == digest(Path(record['fixture'])), 'Converter fixture identity differs')
        require((manifest['rows'], manifest['width'], manifest['outputs'], manifest['program_compute_precision']) ==
                (rows, record['width'], 1, 'float16'), 'Converted model metadata differs')
        for name, checksum in manifest['files'].items():
            require(digest(model_dir / name) == checksum, 'Converted file checksum differs: ' + name)
        record['manifest'] = manifest
        for path in directory.rglob('*'):
            if path.is_file():
                provenance['files'][str(path.resolve())] = digest(path)
        save(output / 'provenance.json', provenance)
    for path, checksum in provenance['files'].items():
        require(digest(Path(path)) == checksum, 'Source or artifact changed during conversion: ' + path)
    provenance['conversion_completed'] = True
    save(output / 'provenance.json', provenance)
    print('Verified frozen conversions completed: ' + str(output), flush=True)


if __name__ == '__main__':
    main()
