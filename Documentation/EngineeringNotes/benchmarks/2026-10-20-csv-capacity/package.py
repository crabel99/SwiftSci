from pathlib import Path
import json,hashlib,tarfile,shutil
R=Path(__file__).resolve().parent
D=Path('/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018/Documentation/EngineeringNotes/benchmarks/2026-10-20-csv-capacity');D.mkdir(exist_ok=True)
names=['README.md','PLAN.md','RESULTS.md','summary.json','audit.json','audit.py','AllocatorReproducer.swift','allocator-reproduction.log','Inspect.swift','Semantics.swift','ResourceProbe.swift','reproduce.py','minimize.py','prepare-trial.py','build.py','compare.py','check.py','checks.json','summarize.py','package.py','trace.log','trace-columns.json','presized.patch','instrumented.patch']
for name in names:shutil.copy2(R/name,D/name)
files=[R/n for n in ['reproduction.json','minimization.json','current-reproduction.json','current-inspector-build.json','comparison-plan.json','workers.jsonl','power-end.json','variants.json']]
for v in ['baseline','presized','instrumented']:
 files += [R/'build'/v/name for name in ['build.json','module-signature.json','module.log','link.log']]
with tarfile.open(D/'evidence.tar.gz','w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)))
hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(D/'evidence-sha256.json').write_text(json.dumps({'archive_sha256':hashlib.sha256((D/'evidence.tar.gz').read_bytes()).hexdigest(),'members':hashes},indent=2)+'\n')
with tarfile.open(D/'evidence.tar.gz') as tar:
 assert set(tar.getnames())==set(hashes)
 for name,digest in hashes.items():assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==digest
print(D)
