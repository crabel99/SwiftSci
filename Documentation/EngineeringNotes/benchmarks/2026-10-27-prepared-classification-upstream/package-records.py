from pathlib import Path
import gzip, hashlib, io, json, re, tarfile
r = Path(__file__).resolve().parent
out = r / 'records'
out.mkdir(exist_ok=False)
sha = lambda data: hashlib.sha256(data).hexdigest()
build = json.loads(Path(str(r / 'ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker') + '.build.json').read_text())
host = build['environment']['host'].encode()
device_ids = set()
for folder in ['native-full-debug','native-full-release']:
    for path in (r / folder).glob('*'):
        if path.is_file() and path.suffix in ['.json', '.log']:
            device_ids.update(re.findall(rb'\b[0-9A-F]{8}-[0-9A-F]{16}\b', path.read_bytes()))
compression, transforms, archive_members = {}, {}, {}

def published_bytes(raw):
    data = raw.replace(host, b'<redacted-host>')
    for identifier in device_ids: data = data.replace(identifier, b'<redacted-device-id>')
    return data

def save(path, relative=None, compressed=False):
    relative = relative or str(path.relative_to(r))
    raw = path.read_bytes()
    data = published_bytes(raw)
    if compressed: relative += '.gz'
    target = out / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(gzip.compress(data, compresslevel=6, mtime=0) if compressed else data)
    if compressed: compression[relative] = dict(original_sha256=sha(raw), published_uncompressed_sha256=sha(data), published_uncompressed_size_bytes=len(data))
    if raw != data: transforms[relative] = dict(original_sha256=sha(raw), published_sha256=sha(target.read_bytes()), redaction='Hostname and native hardware identifier replaced; authorized filesystem paths retained')

for name in ['README.md','audit.md','qualification.json','qualification-verifier.log','publish-git-objects.py','verify-qualification.py','package-records.py','verify-publication.py',
             'validate-native.py','check-swift633.py','check-swift633-before-metal-bootstrap.py','check-swift633-combined-cold-start.py','full-ci-runner.py','benchmark-ci-runner.py','check-swift-codeql-replay.py',
             'run-native-matrix.py','launch-ci.py','prepare-ci-caches.py','check-pca-integration.py','flatten-object-references.py',
             'source-head.txt','source-publication.json','source-reconciliation.json','cache-preparation.json','public-workflow-plan.json',
             'compatibility-initial-failure.json','compatibility-cold-start-failure.json','cold-start-assessment.json','pca-integration-initial-failure.json','object-reference-repair.json',
             'standards-review.md','spec-review.md','spec.md','plan.md','decisions.tsv',
             'production.patch','classification.patch','controller-derivation.json']:
    save(r / name)
save(Path(str(r / 'ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker') + '.build.json'), 'worker-build.json')
for folder in ['native-full-debug','native-full-release','compatibility','compatibility-initial-metal-failure','compatibility-combined-cold-start','compatibility-serial-probe','ci-main','ci-bench','ci-security-python','ci-security-swift633','pca-integration','pca-integration/native-pca-classification','verification','verification/public-baseline','verification/public-candidate','verification/public-workflow']:
    for path in sorted((r / folder).iterdir()):
        if path.is_file() and path.suffix in ['.json','.log','.sarif','.py','.swift','.txt']:
            save(path, compressed=path.suffix == '.log' or path.stat().st_size > 100_000)
save(Path('/private/tmp/swiftsci-upstream-gpu-gradient-20261027/native-full-release/build.log'), 'verification/baseline-library-build.log', compressed=True)
for path in sorted((r/'ci-security-swift633/extractor-out').rglob('*')):
    if path.is_file(): save(path, compressed=path.suffix=='.log')
# Preserve complete small workflow/reference artifacts in one deterministic archive.
buffer = io.BytesIO()
with tarfile.open(fileobj=buffer, mode='w') as archive:
    for path in sorted((r / 'ci-bench').rglob('*')):
        if not path.is_file() or path.parent == r / 'ci-bench' or path.suffix not in ['.json','.log','.md','.sarif']: continue
        relative = str(path.relative_to(r)); raw = path.read_bytes(); data = published_bytes(raw)
        info = tarfile.TarInfo(relative);info.size=len(data);info.mode=0o644
        archive.addfile(info, io.BytesIO(data))
        archive_members[relative] = dict(original_sha256=sha(raw), published_sha256=sha(data), bytes=len(data), identifiers_redacted=raw!=data)
(out / 'ci-comparisons.tar.gz').write_bytes(gzip.compress(buffer.getvalue(), compresslevel=6, mtime=0))
for name,value in [('compression-map.json',compression),('publication-transforms.json',transforms),('archive-members.json',archive_members)]:
    (out / name).write_text(json.dumps(value,indent=2)+'\n')
files=sorted(p for p in out.rglob('*') if p.is_file())
assert all(p.stat().st_size < 50_000_000 for p in files)
(out / 'FILES.sha256').write_text(''.join(f'{sha(p.read_bytes())}  {p.relative_to(out)}\n' for p in files))
print(json.dumps(dict(files=len(files)+1, bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file()), archive_members=len(archive_members))))
