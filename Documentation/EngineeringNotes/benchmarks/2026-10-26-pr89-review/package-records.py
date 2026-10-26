from pathlib import Path
import gzip, hashlib, json, subprocess

r = Path(__file__).resolve().parent
out = r / 'notes/Documentation/EngineeringNotes/benchmarks/2026-10-26-pr89-review'
out.mkdir(parents=True, exist_ok=False)
sha = lambda data: hashlib.sha256(data).hexdigest()
compression = {}

def copy(path, name=None):
    data = path.read_bytes()
    destination = out / (name or str(path.relative_to(r)))
    if path.suffix in ['.log', '.lcov']:
        destination = Path(str(destination) + '.gz')
        compression[str(destination.relative_to(out))] = {'original_path': str(path), 'original_sha256': sha(data), 'original_bytes': len(data)}
        data = gzip.compress(data, compresslevel=6, mtime=0)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)

for name in ['qualification.json', 'review-request.json', 'spec-review.md', 'spec-review-final.md', 'standards-review.md', 'standards-review-final.md', 'spec-workspace-query.swift', 'spec-workspace-query.log', 'PCAReview.md', 'LayoutProbe.swift', 'BaselineMeanProbe.swift', 'baseline-mean-source-proof.json', 'check-layout.py', 'validate-native.py', 'check-swift633.py', 'full-ci-runner.py', 'benchmark-ci-runner.py', 'verify-qualification.py', 'package-records.py']:
    copy(r / name, 'README.md' if name == 'PCAReview.md' else None)

copy(r / 'check-old-regressions.py')
copy(r / 'qualification-verification.log')
copy(r / 'compatibility-regressions/layout-coverage.txt')
for folder in ['layout-final', 'baseline-mean', 'native-full-debug-final', 'native-full-release-final', 'compatibility', 'compatibility-regressions', 'ci-main-final', 'ci-bench-final']:
    for path in sorted((r / folder).rglob('*')):
        if path.is_file() and path.suffix in ['.json', '.log', '.lcov', '.sarif'] and '.xcresult' not in str(path):
            copy(path)

for path in sorted((r / 'ci-security-python').glob('*')):
    if path.is_file():
        copy(path)
copy(r / 'ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker.build.json', 'worker-build.json')
copy(r / 'ci-bench-cache/standardized/build.log', 'worker-build.log')
patch = subprocess.check_output(['git', 'diff', '--binary', '09607a7e9caa2b7166651dcaaa167178f6097b55', 'HEAD'], cwd=r / 'source')
(out / 'production.patch').write_bytes(patch)
(out / 'compression-map.json').write_text(json.dumps(compression, indent=2) + '\n')
lines = [f'{sha(path.read_bytes())}  {path.relative_to(out)}' for path in sorted(out.rglob('*')) if path.is_file()]
(out / 'FILES.sha256').write_text('\n'.join(lines) + '\n')
print(out)
