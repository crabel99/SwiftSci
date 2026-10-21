from pathlib import Path
import json,shutil
r=Path('/private/tmp/swiftsci-csv-eager-checks-20261021');old=Path('/private/tmp/swiftsci-csv-ingestion-checks-20261021')
for name in ['build.py','ResourceProbe.swift','PythonProbe.py']:
 if (old/name).exists():shutil.copy2(old/name,r/name)
(r/'variants.json').write_text(json.dumps({'indexed':{'path':'/private/tmp/swiftsci-csv-scoped-simd-20261021','pr':None},'eager':{'path':'/private/tmp/swiftsci-csv-eager-batches-20261021','pr':None}},indent=2)+'\n')
shutil.copytree(old/'inputs',r/'inputs',dirs_exist_ok=True)
(r/'build-standard-worker.py').write_text((old/'build-standard-worker-simd.py').read_text().replace('/private/tmp/swiftsci-csv-scoped-simd-20261021','/private/tmp/swiftsci-csv-eager-batches-20261021').replace('standard-worker-simd','standard-worker').replace('scoped-streaming head','eager-batch head'))
