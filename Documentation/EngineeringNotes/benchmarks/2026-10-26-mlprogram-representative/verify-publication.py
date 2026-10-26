from pathlib import Path
import argparse, gzip, hashlib, json, shutil, subprocess, sys, tempfile, xml.etree.ElementTree as E

parser = argparse.ArgumentParser()
parser.add_argument('--records', type=Path, default=Path(__file__).resolve().parent)
parser.add_argument('--receipt', type=Path)
a = parser.parse_args()
r = a.records.resolve()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
files = {}
for line in (r / 'FILES.sha256').read_text().splitlines():
    expected, name = line.split('  ', 1)
    path = (r / name).resolve()
    assert path.is_relative_to(r) and sha(path) == expected, name
    files[name] = expected
assert set(files) == {str(p.relative_to(r)) for p in r.rglob('*') if p.is_file() and p.name != 'FILES.sha256'}
compression = json.loads((r / 'compression-map.json').read_text())
transforms = json.loads((r / 'publication-transforms.json').read_text())
for name, meta in compression.items():
    data = gzip.decompress((r / name).read_bytes())
    assert hashlib.sha256(data).hexdigest() == meta['published_uncompressed_sha256'], name
    assert len(data) == meta['published_uncompressed_size_bytes'], name
for name, meta in transforms.items():
    path = r / name
    assert sha(path) == meta['published_sha256']
    if name.endswith('.toc.xml'):
        assert all('name' not in d.attrib and 'uuid' not in d.attrib for d in E.parse(path).findall('.//device'))

with tempfile.TemporaryDirectory(prefix='swiftsci-event-replay-') as directory:
    replay = Path(directory)
    recordings = json.loads((r / 'traces/recordings.json').read_text())
    expected_events = json.loads((r / 'traces/inspected-events.json').read_text())
    assert len(recordings) == len(expected_events) == 8
    for recording in recordings:
        name = recording['name']
        relative = 'traces/' + name + '.toc.xml'
        assert recording['toc_sha256'] == transforms[relative]['original_sha256']
        recording['toc_sha256'] = transforms[relative]['published_sha256']
        for suffix in ['.json', '.toc.xml']:
            shutil.copy2(r / 'traces' / (name + suffix), replay / (name + suffix))
        for suffix in ['.coreml.xml', '.intervals.xml', '.ane.xml']:
            relative = 'traces/' + name + suffix + '.gz'
            (replay / (name + suffix)).write_bytes(gzip.decompress((r / relative).read_bytes()))
    (replay / 'recordings.json').write_text(json.dumps(recordings))
    # Reuse the original inspector, replacing only export with retained-export verification.
    original = (r / 'inspect-program-traces.py').read_text()
    start = original.index("        assert not path.exists(), 'Choose fresh exports")
    end = original.index('        exports[key] = path', start)
    derived = original[:start] + '        assert path.is_file(), path\n' + original[end:]
    (replay / 'inspect-replay.py').write_text(derived)
    result = subprocess.run([sys.executable, str(replay / 'inspect-replay.py'), '--folder', str(replay)],
                            capture_output=True, text=True, check=True)
    actual = json.loads((replay / 'inspected-events.json').read_text())
    for expected, found in zip(expected_events, actual):
        for key in ['name', 'target_pid', 'model_sha256', 'measurement_start_ns', 'measurement_end_ns',
                    'completed_requests', 'event_counts', 'dispatch_counts', 'positive_dispatch_counts',
                    'models', 'examples', 'global_ane_hardware_rows', 'record_sha256', 'attribution']:
            assert expected[key] == found[key], (expected['name'], key)
        for key in ['coreml', 'intervals', 'ane']:
            assert expected['event_exports'][key]['sha256'] == found['event_exports'][key]['sha256']
        assert found['positive_dispatch_counts'] == {'CPU': found['completed_requests']}
        assert found['global_ane_hardware_rows'] == 0
    replay_hash = sha(replay / 'inspect-replay.py')
receipt = dict(status='passed', files_verified=len(files), compressed_files_verified=len(compression),
               event_replay_cases=len(actual), positive_cpu_dispatches=sum(v['completed_requests'] for v in actual),
               original_inspector_sha256=sha(r / 'inspect-program-traces.py'), replay_inspector_sha256=replay_hash,
               replay_transformation='Replace fresh xctrace export block with existence check for retained exports',
               verifier_sha256=sha(Path(__file__)))
if a.receipt: a.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
