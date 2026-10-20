from pathlib import Path
import json,hashlib,tarfile,shutil,re
R=Path(__file__).resolve().parent
D=Path('/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018/Documentation/EngineeringNotes/benchmarks/2026-10-20-csv-compact');D.mkdir(exist_ok=True)
J=Path('/private/tmp/swiftsci-csv-compact-replay-20261020');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for v in ['baseline','active','compact','inlined','packed']:
 b=json.loads((R/'build'/v/'build.json').read_text())
 for name,digest in b['sources'].items():assert sha(J/v/name)==digest
plans=[*R.glob('*comparison-plan.json'),R/'return-layout-heldout/plan.json']
for p in plans:
 for path,digest in json.loads(p.read_text())['fixtures'].items():
  old=Path(path)
  target=J/'fixtures/1000000-4-True.csv' if old.name=='02-pr39-csv-quoted-1000000-4.csv' else J/('heldout-fixtures' if 'heldout-fixtures' in old.parts else 'fixtures')/old.name
  assert sha(target)==digest
names=['README.md','audit.json','codegen.json','runner-guard-check.json',*[p.name for p in R.glob('*.patch')],*[p.name for p in R.glob('*RESULTS.md')],*[p.name for p in R.glob('*summary.json')]]
names += [p.name for p in R.glob('*.py') if p.name not in ['prepare.py','prepare-packed-return.py']]
names += ['ResourceProbe.swift','Inspect.swift','Semantics.swift','ParserParity.swift','CompactChecks.swift','RangeChecks.swift']
for name in names:shutil.copy2(R/name,D/name)
shutil.copytree(R/'tests',D/'tests',dirs_exist_ok=True)
(D/'return-layout-heldout').mkdir(exist_ok=True)
for name in ['RESULTS.md','summary.json']:shutil.copy2(R/'return-layout-heldout'/name,D/'return-layout-heldout'/name)
files=[R/'variants.json']
files += list(R.glob('*comparison-plan.json'))+list(R.glob('*workers.jsonl'))+list(R.glob('*power-end.json'))+list(R.glob('*checks.json'))+list(R.glob('*test-receipts.json'))
files += [R/'return-layout-heldout'/name for name in ['plan.json','workers.jsonl','power-end.json']]
files += list((R/'excluded-heldout').glob('*'))
for v in ['baseline','active','compact','inlined','packed']:files += [R/'build'/v/n for n in ['build.json','module-signature.json','module.log','link.log']]
for v in ['compact','packed']:files.append(R/'test-build'/v/'tests.log')
# Include exact generated test-only parser sources referenced by the boundary receipts.
files += [R/'BoundaryParser.swift',R/'packed-BoundaryParser.swift']
assert len(files)==len(set(files))
with tarfile.open(D/'evidence.tar.gz','w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)))
hashes={str(p.relative_to(R)):sha(p) for p in files}
(D/'evidence-sha256.json').write_text(json.dumps(dict(archive_sha256=sha(D/'evidence.tar.gz'),members=hashes,replay_source_and_fixture_hashes='verified'),indent=2)+'\n')
with tarfile.open(D/'evidence.tar.gz') as tar:
 assert set(tar.getnames())==set(hashes)
 for name,digest in hashes.items():assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==digest
for p in D.rglob('*.md'):
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' not in link:assert (p.parent/link).exists(),link
print('Verified replay sources, regenerated fixtures, archive hashes and report links:',D)
