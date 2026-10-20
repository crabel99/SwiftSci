from pathlib import Path
import json,hashlib,tarfile,shutil
R=Path(__file__).resolve().parent
N=Path('/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018/Documentation/EngineeringNotes')
D=N/'benchmarks/2026-10-19-serial-gather-resources';D.mkdir(exist_ok=True)
for name in ['ResourceProbe.swift','prepare.py','build.py','run.py','summarize.py','audit.py','package.py','PLAN.md','README.md','RESULTS.md','summary.json','audit.json','plan.json','toolchain.json','power-end.json']:
 shutil.copy2(R/name,D/name)
files=[R/'processes.jsonl',R/'variants.json',*sorted((R/'preliminary').iterdir())]
for v in ['baseline','candidate']:
 files += [R/'build'/v/name for name in ['build.json','module-signature.json','module.log','link.log']]
with tarfile.open(D/'evidence.tar.gz','w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)))
hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(D/'evidence-sha256.json').write_text(json.dumps({'archive_sha256':hashlib.sha256((D/'evidence.tar.gz').read_bytes()).hexdigest(),'members':hashes},indent=2)+'\n')
with tarfile.open(D/'evidence.tar.gz') as tar:
 assert set(tar.getnames())==set(hashes)
 for name,digest in hashes.items():assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==digest
print(D)

B=Path('/private/tmp/swiftsci-string-bool-resource-20261019')
F=D/'narrowed';F.mkdir(exist_ok=True)
for name in ['README.md','ResourceProbe.swift','prepare.py','build.py','run.py','summarize.py','audit.py','PLAN.md','RESULTS.md','summary.json','audit.json','plan.json','power-end.json','run-regressions.py','ScalarGatherSpecializationTests.swift','TestMain.swift','regression-tests.log','regression-receipt.json','regression-build.log']:
 shutil.copy2(B/name,F/name)
files=[B/'processes.jsonl',B/'variants.json']
for v in ['baseline','candidate']:
 files += [B/'build'/v/name for name in ['build.json','module-signature.json','module.log','link.log']]
with tarfile.open(F/'evidence.tar.gz','w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(B)))
hashes={str(p.relative_to(B)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(F/'evidence-sha256.json').write_text(json.dumps({'archive_sha256':hashlib.sha256((F/'evidence.tar.gz').read_bytes()).hexdigest(),'members':hashes},indent=2)+'\n')
with tarfile.open(F/'evidence.tar.gz') as tar:
 assert set(tar.getnames())==set(hashes)
 for name,digest in hashes.items():assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==digest
