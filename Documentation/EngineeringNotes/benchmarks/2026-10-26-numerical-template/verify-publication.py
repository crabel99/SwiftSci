from pathlib import Path
import argparse
import gzip
import hashlib
import json

parser = argparse.ArgumentParser(description='Verify a standalone numerical-template records directory without original builds.')
parser.add_argument('--records', type=Path, default=Path(__file__).resolve().parent)
args = parser.parse_args()
root = args.records.resolve()
sha = lambda data: hashlib.sha256(data).hexdigest()
manifest = {}
for line in (root / 'FILES.sha256').read_text().splitlines():
    digest, name = line.split('  ', 1)
    path = (root / name).resolve()
    assert path.is_relative_to(root) and sha(path.read_bytes()) == digest, name
    assert name not in manifest, name
    manifest[name] = digest
assert set(manifest) == {str(path.relative_to(root)) for path in root.rglob('*') if path.is_file() and path.name != 'FILES.sha256'}
records = json.loads((root / 'publication-records.json').read_text())
qualification = json.loads((root / 'qualification.json').read_text())
assert qualification['status'] == 'passed'
assert set(records) == set(qualification['artifacts']) | {'qualification.json'}
for name, item in records.items():
    path = (root / item['path']).resolve()
    assert path.is_relative_to(root)
    data = path.read_bytes()
    assert sha(data) == item['published_sha256'], name
    if item['compressed']:
        data = gzip.decompress(data)
    assert sha(data) == item['uncompressed_sha256'] and len(data) == item['uncompressed_bytes'], name
    if name != 'qualification.json':
        assert item['original_sha256'] == qualification['artifacts'][name], name
print(json.dumps(dict(status='passed', source=qualification['source'], manifest_files=len(manifest),
                      compressed_payloads=sum(item['compressed'] for item in records.values()),
                      limits='Standalone integrity and original-to-published transformation checks; no numerical rerun or repeated remote fetch'), indent=2))
