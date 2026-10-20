from pathlib import Path
import json,hashlib,tarfile,shutil,re
R=Path(__file__).resolve().parent
D=Path('/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018/Documentation/EngineeringNotes/benchmarks/2026-10-20-csv-blocks');D.mkdir(exist_ok=True)
J=Path('/private/tmp/swiftsci-csv-blocks-replay-20261020')
for v in ['baseline','blocked','active','flattened']:
 b=json.loads((R/'build'/v/'build.json').read_text())
 for name,digest in b['sources'].items():assert hashlib.sha256((J/v/name).read_bytes()).hexdigest()==digest
for prefix in ['', 'active-','heldout-','flattened-']:
 plan=json.loads((R/(prefix+'comparison-plan.json')).read_text())
 for fixture,digest in plan['fixtures'].items():
  p=Path(fixture)
  if p.name=='02-pr39-csv-quoted-1000000-4.csv':q=J/'fixtures/1000000-4-True.csv'
  else:q=J/('heldout-fixtures' if 'heldout-fixtures' in p.parts else 'fixtures')/p.name
  assert hashlib.sha256(q.read_bytes()).hexdigest()==digest
names=['README.md','audit.json',*[p.name for p in R.glob('*.py') if p.name not in ['prepare.py','prepare-active.py','prepare-flat.py']],*[p.name for p in R.glob('*.swift')],*[p.name for p in R.glob('*.patch')],*[p.name for p in R.glob('*RESULTS.md')],*[p.name for p in R.glob('*summary.json')]]
for name in names:shutil.copy2(R/name,D/name)
files=[R/'variants.json']
for prefix in ['', 'active-','heldout-','flattened-']:
 files += [R/(prefix+n) for n in ['comparison-plan.json','workers.jsonl','power-end.json']]
for prefix in ['', 'active-','flattened-']:files.append(R/(prefix+'checks.json'))
for v in ['baseline','blocked','active','flattened']:
 files += [R/'build'/v/n for n in ['build.json','module-signature.json','module.log','link.log']]
with tarfile.open(D/'evidence.tar.gz','w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)))
hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(D/'evidence-sha256.json').write_text(json.dumps(dict(archive_sha256=hashlib.sha256((D/'evidence.tar.gz').read_bytes()).hexdigest(),members=hashes,replay_source_and_fixture_hashes='verified'),indent=2)+'\n')
with tarfile.open(D/'evidence.tar.gz') as tar:
 assert set(tar.getnames())==set(hashes)
 for name,digest in hashes.items():assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==digest
for p in D.glob('*.md'):
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' not in link:assert (D/link).exists(),link
print('Verified archive members, document links, replay source hashes and regenerated fixture hashes:',D)
