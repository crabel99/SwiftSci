from pathlib import Path
import gzip, hashlib, io, json, re, tarfile
r = Path(__file__).resolve().parent
out = r / 'records'
qualification = json.loads((r / 'qualification.json').read_text())
assert qualification['status'] == 'passed' and qualification['source'] == (r / 'source-head.txt').read_text().strip()
assert 'Pending final source-bound verifier' not in (r / 'README.md').read_text()
assert (r / 'audit.md').is_file()
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

for name in ['README.md', 'audit.md', 'audit-initial.md', 'audit-controller.md', 'qualification.json', 'qualification-verifier.log', 'qualification-verifier-build-overlap-attempt.log', 'verify-qualification.py', 'package-records.py', 'verify-publication.py', 'validate-native.py', 'check-swift633.py', 'full-ci-runner.py', 'benchmark-ci-runner.py', 'check-swift-codeql-replay.py', 'run-native-matrix.py', 'launch-ci.py', 'prepare-ci-caches.py', 'source-head.txt', 'source-publication.json', 'source-reconciliation.json', 'execution-head.txt', 'execution-reconciliation.json', 'execution.patch', 'cache-preparation.json', 'standards-review.md', 'spec-review.md', 'standards-review-initial.md', 'spec-review-initial.md', 'spec.md', 'plan.md', 'decisions.tsv', 'production.patch', 'security-extraction.json', 'upstream-status.json', 'publish-source.py', 'delivery-scope.md', 'exercise-example.py', 'run-documented-example.py', 'check-empty-column.py', 'export-agent-coverage.py', 'export-example-coverage.py', 'check-initial-example.py', 'metadata-clarification.json', 'finalize-metadata.py', 'record-final-source.py', 'publish-notes.py']:
    save(r / name)
# Include final source files for reviewers without requiring a checkout.
for name in qualification['changed_files']:
    save(r / 'source' / name, 'source-files/' + name)
save(r / 'documented-xcode-build.log', compressed=True)
for path in [*r.glob('before-xcode-guide-*'), *r.glob('before-scope-correction-*')]:
    if path.is_file(): save(path)
save(Path(str(r / 'ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker') + '.build.json'), 'worker-build.json')
for folder in ['native-full-debug', 'native-full-release', 'compatibility', 'ci-main', 'ci-bench', 'ci-security-python', 'ci-security-swift633', 'coverage-supplement', 'example-coverage', 'example-coverage-path-filter-attempt', 'example-coverage-filename-filter-attempt', 'initial-example', 'initial-controls', 'spec-probes', 'empty-column-control', 'documented-example', 'example-native-debug', 'example-native-release', 'example-swift633-debug-before-xcode-guide', 'example-swift633-release-before-xcode-guide', 'documented-example-before-xcode-guide', 'example-native-debug-before-xcode-guide', 'example-native-release-before-xcode-guide', 'example-native-release-during-documented-build', 'empty-column-control-before-xcode-guide']:
    for path in sorted((r / folder).iterdir()):
        if path.is_file() and path.suffix in ['.json','.log','.sarif','.py','.txt','.patch','.lcov','.csv','.stdout']:
            save(path, compressed=path.suffix in ['.log','.lcov'] or path.stat().st_size > 100_000)
for folder in ['ci-security-swift633/extractor-out', 'initial-example', 'initial-controls', 'documented-example', 'example-native-debug', 'example-native-release', 'example-swift633-debug-before-xcode-guide', 'example-swift633-release-before-xcode-guide', 'documented-example-before-xcode-guide', 'example-native-debug-before-xcode-guide', 'example-native-release-before-xcode-guide', 'example-native-release-during-documented-build', 'empty-column-control-before-xcode-guide']:
    for path in sorted((r / folder).rglob('*')):
        if path.is_file() and path.parent != r / folder and path.suffix in ['.log', '.json', '.txt', '.csv']:
            save(path, compressed=path.suffix == '.log' or path.stat().st_size > 100_000)
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
