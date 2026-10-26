from pathlib import Path
import argparse,gzip,hashlib,json,shutil
p=argparse.ArgumentParser();p.add_argument('destination',type=Path);a=p.parse_args()
root=Path(__file__).resolve().parent
out=a.destination
out.mkdir(parents=True,exist_ok=False)
files=['README.md','plan.md','decisions.tsv','production.patch','validate-native.py','package-records.py','finalize-records.py']
files += [str(x.relative_to(root)) for x in (root/'design').glob('*.md')]
files += [str(x.relative_to(root)) for x in (root/'design').glob('*.json')]
for folder in ('native-debug-initial','native-debug','native-release'):
    files += [str(x.relative_to(root)) for x in (root/folder).glob('*.json')]
    files += [str(x.relative_to(root)) for x in (root/folder).glob('*.log')]
for pattern in ('*.py','*.swift','*.json','*.log'):
    files += [str(x.relative_to(root)) for x in (root/'verification').glob(pattern)]
for folder in ('public-baseline','public-candidate'):
    for pattern in ('proof.json','*.log'):
        files += [str(x.relative_to(root)) for x in (root/'verification'/folder).glob(pattern)]
files += [str(x.relative_to(root)) for x in (root/'verification/public-workflow').glob('*.json')]
files += [str(x.relative_to(root)) for x in (root/'supervised-conformance').rglob('*') if x.is_file()]
worker=root/'derived/Build/Products/Release/SwiftSciBenchmarkWorker.build.json'
for name in sorted(set(files)):
    source=root/name
    dest=out/name
    dest.parent.mkdir(parents=True,exist_ok=True)
    if source.suffix=='.log':
        dest=dest.with_suffix('.log.gz')
        with dest.open('wb') as raw:
            with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as target:target.write(source.read_bytes())
    else:shutil.copyfile(source,dest)
shutil.copyfile(worker,out/'verification/standardized-worker-build.json')
old=Path('/private/tmp/swiftsci-prepared-pca-20261026/baseline-standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker.build.json')
shutil.copyfile(old,out/'verification/original-worker-build.json')
manifest={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file()}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Packaged',len(manifest),'files;',sum(f.stat().st_size for f in out.rglob('*') if f.is_file()),'bytes')
