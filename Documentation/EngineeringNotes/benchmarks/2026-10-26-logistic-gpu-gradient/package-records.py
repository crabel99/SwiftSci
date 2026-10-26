from pathlib import Path
import argparse,gzip,hashlib,json,shutil
parser=argparse.ArgumentParser();parser.add_argument('destination',type=Path);args=parser.parse_args()
root=Path(__file__).resolve().parent;out=args.destination
qualification=json.loads((root/'qualified-commit.json').read_text());assert qualification['status']=='passed'
out.mkdir(parents=True,exist_ok=False)
files=set()
for pattern in ['*.md','*.py','*.swift','*.json','*.log','*.patch']:
 files.update(root.glob(pattern))
for name in ['native-red','native-green','native-full-debug','native-full-release','compatibility','compatibility-initial-relocated-cache','ci-main','ci-main-final','ci-bench','ci-bench-final','ci-security-python','verification']:
 folder=root/name
 for p in folder.rglob('*'):
  relative=p.relative_to(folder)
  if p.name!='coverage.json' and p.is_file() and p.suffix in ['.json','.log','.sarif','.py','.swift','.txt','.tsv','.csv','.jsonl','.lcov'] and not any(x in ['codeql-python','standardized','packages','module-cache','tests.xcresult','regression-candidate-release'] for x in relative.parts):files.add(p)
# Keep the regression proof, not its objects or binary.
files.add(root/'verification/regression-candidate-release/proof.json')
for source in sorted(files):
 relative=source.relative_to(root)
 target=out/relative;target.parent.mkdir(parents=True,exist_ok=True)
 if source.suffix in ['.log','.lcov']:
  target=target.with_suffix(source.suffix+'.gz')
  with target.open('wb') as stream:
   with gzip.GzipFile(filename='',mode='wb',fileobj=stream,mtime=0) as zipped:zipped.write(source.read_bytes())
 else:shutil.copyfile(source,target)
worker=root/'ci-bench/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker.build.json'
shutil.copyfile(worker,out/'worker-build.json')
manifest={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Packaged',len(manifest),'files;',sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),'bytes')
