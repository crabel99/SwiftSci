from pathlib import Path
import json,hashlib,tarfile,shutil,re
R=Path(__file__).resolve().parent
D=Path('/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018/Documentation/EngineeringNotes/benchmarks/2026-10-20-csv-cursor');D.mkdir(exist_ok=True)
J=Path('/private/tmp/swiftsci-csv-cursor-replay-20261020')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for v in ['baseline','active','cursor','specialized']:
 b=json.loads((R/'build'/v/'build.json').read_text())
 for name,digest in b['sources'].items():assert sha(J/v/name)==digest
for prefix in ['', 'heldout-','specialized-','heldout-specialized-','production-','heldout-production-']:
 plan=json.loads((R/(prefix+'comparison-plan.json')).read_text())
 for path,digest in plan['fixtures'].items():
  p=Path(path)
  if p.name=='02-pr39-csv-quoted-1000000-4.csv':q=J/'fixtures/1000000-4-True.csv'
  else:q=J/('heldout-fixtures' if 'heldout-fixtures' in p.parts else 'fixtures')/p.name
  assert sha(q)==digest
for name in ['README.md','audit.json',*[p.name for p in R.glob('*.py') if p.name not in ['prepare.py','prepare-specialized.py']],*[p.name for p in R.glob('*.swift')],*[p.name for p in R.glob('*.patch')],*[p.name for p in R.glob('*RESULTS.md')],*[p.name for p in R.glob('*summary.json')]]:shutil.copy2(R/name,D/name)
shutil.copytree(R/'tests',D/'tests',dirs_exist_ok=True)
files=[R/n for n in ['variants.json','lookup-builds.json','lookup-workers.jsonl','index-plan.json','index-workers.jsonl','index-power-end.json','checks.json','specialized-checks.json','test-receipts.json']]
for prefix in ['', 'heldout-','specialized-','heldout-specialized-','production-','heldout-production-']:
 files += [R/(prefix+n) for n in ['comparison-plan.json','workers.jsonl','power-end.json']]
for v in ['baseline','active','cursor','specialized']:
 files += [R/'build'/v/n for n in ['build.json','module-signature.json','module.log','link.log']]
for v in ['cursor','specialized']:files.append(R/'test-build'/v/'tests.log')
with tarfile.open(D/'evidence.tar.gz','w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)))
hashes={str(p.relative_to(R)):sha(p) for p in files}
(D/'evidence-sha256.json').write_text(json.dumps(dict(archive_sha256=sha(D/'evidence.tar.gz'),members=hashes,replay_source_and_fixture_hashes='verified'),indent=2)+'\n')
with tarfile.open(D/'evidence.tar.gz') as tar:
 assert set(tar.getnames())==set(hashes)
 for name,digest in hashes.items():assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==digest
for p in D.glob('*.md'):
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' not in link:assert (D/link).exists(),link
print('Verified archive, replay source and fixture hashes, and report links:',D)
