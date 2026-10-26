from pathlib import Path
import argparse
import gzip
import hashlib
import json
import re

parser = argparse.ArgumentParser(description='Assemble reviewed numerical-template records, excluding builds, caches and binaries.')
parser.add_argument('--output', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent
out = args.output or root / 'records'
qualification = json.loads((root / 'qualification.json').read_text())
assert qualification['status'] == 'passed'
assert 'No open findings after re-review' in (root / 'standards-review.md').read_text()
sha = lambda data: hashlib.sha256(data).hexdigest()
inputs = dict(qualification['artifacts'])
inputs['qualification.json'] = sha((root / 'qualification.json').read_bytes())
assert all(sha((root / name).read_bytes()) == digest for name, digest in inputs.items())
host = json.loads((root / 'final-run-qualified/provenance.json').read_text())['build']['environment']['host'].encode()
# Device UUIDs and native hardware identifiers are not needed to interpret these records.
identifier = re.compile(rb'\b(?:[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}|[0-9A-Fa-f]{8}-[0-9A-Fa-f]{16})\b')
out.mkdir(parents=True, exist_ok=False)
transforms = {}
for name, digest in inputs.items():
    raw = (root / name).read_bytes()
    published = identifier.sub(b'<redacted-device-id>', raw.replace(host, b'<redacted-host>'))
    compressed = name in ['package-build.log', 'remote-package/build.log']
    relative = name + ('.gz' if compressed else '')
    path = out / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(published, compresslevel=6, mtime=0) if compressed else published)
    transforms[name] = dict(path=relative, original_sha256=digest, published_sha256=sha(path.read_bytes()),
                            uncompressed_sha256=sha(published), uncompressed_bytes=len(published),
                            compressed=compressed, identifiers_redacted=published != raw)
(out / 'publication-records.json').write_text(json.dumps(transforms, indent=2) + '\n')
files = sorted(path for path in out.rglob('*') if path.is_file())
(out / 'FILES.sha256').write_text(''.join(f'{sha(path.read_bytes())}  {path.relative_to(out)}\n' for path in files))
print(json.dumps(dict(files=len(files) + 1, output=str(out), compressed_payloads=sum(item['compressed'] for item in transforms.values()))))
