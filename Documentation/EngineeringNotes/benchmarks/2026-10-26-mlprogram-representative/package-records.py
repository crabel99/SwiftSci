from pathlib import Path
import gzip, hashlib, json, xml.etree.ElementTree as E

r = Path(__file__).resolve().parent
out = r / 'records'
out.mkdir(exist_ok=False)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
compression, transforms = {}, {}
host = json.loads((r / 'workflows/provenance.json').read_text())['build']['environment']['host'].encode()

def published_bytes(path):
    return path.read_bytes().replace(host, b'<redacted-host>')

def note_transform(path, target, data):
    if data != path.read_bytes():
        transforms[str(target.relative_to(out))] = dict(original_sha256=sha(path),
            published_sha256=sha(target), published_uncompressed_sha256=hashlib.sha256(data).hexdigest(),
            redaction='Hostname replaced with redacted marker; authorized filesystem paths retained')

def copy(path, relative=None):
    relative = relative or str(path.relative_to(r))
    target = out / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    data = published_bytes(path)
    target.write_bytes(data)
    note_transform(path, target, data)


def compress(path):
    relative = str(path.relative_to(r)) + '.gz'
    target = out / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    data = published_bytes(path)
    target.write_bytes(gzip.compress(data, compresslevel=6, mtime=0))
    compression[relative] = dict(original_path=str(path), original_sha256=sha(path),
        original_size_bytes=path.stat().st_size, published_uncompressed_sha256=hashlib.sha256(data).hexdigest(),
        published_uncompressed_size_bytes=len(data))
    note_transform(path, target, data)

for name in ['README.md', 'ProgramWorkflowProbe.swift', 'audit-interim.md', 'publication-audit.md', 'scalar-reference.json',
             'prepare-representative.py', 'run-workflows.py', 'run-concurrency.py', 'fullprecision-control.py',
             'verify-scalar-reference.py', 'inspect-program-traces.py', 'trace-programs.py',
             'trace-programs-before.py', 'trace-programs-resume-capture.py',
             'package-records.py', 'verify-publication.py', 'plan.md', 'decisions.tsv',
             'adapter-grounding.md', 'harness-grounding.md', 'how-synthesis.md', 'next-items.md',
             'llm-completion-grounding.md', 'probe/proof.json', 'probe/probe.LinkFileList']:
    copy(r / name)
copy(Path('/private/tmp/swiftsci-gpu-logistic-correctness-20261026/verification/link-public-probe.py'), 'link-public-probe.py')
copy(Path('/private/tmp/swiftsci-coreml-representative-20261026/ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker.build.json'), 'worker-build.json')
for folder in ['models', 'workflows', 'concurrency', 'fullprecision']:
    for path in sorted((r / folder).rglob('*')):
        if not path.is_file(): continue
        if path.suffix in ['.json', '.log'] and path.stat().st_size > 100_000:
            compress(path)
        else:
            copy(path)
for name in ['recordings.json', 'inspected-events.json', 'inspection-completed.json', 'provenance.json', 'provenance-capture.json', 'entitlements.plist', 'initial-driver-failure.json']:
    copy(r / 'traces' / name)
for recording in json.loads((r / 'traces/recordings.json').read_text()):
    name = recording['name']
    for suffix in ['.json', '.request.json', '.command.json', '.log']:
        copy(r / 'traces' / (name + suffix))
    for suffix in ['.coreml.xml', '.intervals.xml', '.ane.xml']:
        compress(r / 'traces' / (name + suffix))
    path = r / 'traces' / (name + '.toc.xml')
    tree = E.parse(path)
    for device in tree.findall('.//device'):
        for key in ['name', 'uuid']: device.attrib.pop(key, None)
    relative = 'traces/' + name + '.toc.xml'
    published = out / relative
    tree.write(published, encoding='utf-8', xml_declaration=True)
    transforms[relative] = dict(original_sha256=sha(path), published_sha256=sha(published),
        redaction='Device name and UUID removed; target process, measurement and table scope retained')
(out / 'compression-map.json').write_text(json.dumps(compression, indent=2) + '\n')
(out / 'publication-transforms.json').write_text(json.dumps(transforms, indent=2) + '\n')
files = sorted(p for p in out.rglob('*') if p.is_file())
assert all(p.stat().st_size < 50_000_000 for p in files)
(out / 'FILES.sha256').write_text(''.join(f'{sha(p)}  {p.relative_to(out)}\n' for p in files))
print(json.dumps(dict(files=len(files)+1, bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))))
