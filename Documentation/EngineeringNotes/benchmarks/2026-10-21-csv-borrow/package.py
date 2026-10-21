from pathlib import Path
import json,hashlib,tarfile,shutil
r=Path(__file__).resolve().parent;h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=Path('/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018/Documentation/EngineeringNotes/benchmarks/2026-10-21-csv-borrow')
d.mkdir(parents=True,exist_ok=False);variants=list(json.loads((r/'variants.json').read_text()));sets=json.loads((r/'accepted-sets.json').read_text())
identity={'sources':{v:json.loads((r/'build'/v/'build.json').read_text())['sources'] for v in variants},'fixtures':{}}
for name in sets:
 for path,digest in json.loads((r/name/'plan.json').read_text())['fixtures'].items():
  p=Path(path);key=p.parent.name+'/'+p.name
  if p.name=='02-pr39-csv-quoted-1000000-4.csv':key='fixtures/1000000-4-True.csv'
  assert key not in identity['fixtures'] or identity['fixtures'][key]==digest
  identity['fixtures'][key]=digest
(r/'replay-identities.json').write_text(json.dumps(identity,indent=2)+'\n')
for pattern in ['*.py','*.swift','*.patch']:
 for p in r.glob(pattern):
  if p.name.endswith('BoundaryParser.swift'):continue
  shutil.copy2(p,d/p.name)
for name in ['README.md','CLOSEOUT.md','audit.json','codegen.json','replay-identities.json','accepted-sets.json']:shutil.copy2(r/name,d/name)
shutil.copytree(r/'tests',d/'tests')
for name in sets:
 (d/name).mkdir()
 for file in ['RESULTS.md','summary.json']:shutil.copy2(r/name/file,d/name/file)
raw=[]
for name in sets:
 raw.extend((r/name).glob('*.json'));raw.append(r/name/'workers.jsonl')
raw.extend(r.glob('*.json'))
for v in variants:raw.append(r/'build'/v/'build.json')
raw.append(r/'test-build/scoped/tests.log');raw.extend(r.glob('*BoundaryParser.swift'));raw=sorted(set(raw))
with tarfile.open(d/'evidence.tar.gz','w:gz') as archive:
 for p in raw:archive.add(p,arcname=str(p.relative_to(r)),recursive=False)
(d/'evidence-sha256.json').write_text(json.dumps(dict(archive_sha256=h(d/'evidence.tar.gz'),members={str(p.relative_to(r)):h(p) for p in raw}),indent=2)+'\n')
print(d)
