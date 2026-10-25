"""Reject incomplete telemetry or invalid native results; do not infer hardware cause."""
import json,plistlib,sys
from pathlib import Path
root=Path(sys.argv[1])
summary=json.loads((root/'native/rate-probe-summary.json').read_text())
if summary['samples']!=240 or summary['checksum_count']!=1 or not summary['all_p_user_zero']:
    raise ValueError('Native probe output is incomplete or invalid')
parts=[x.strip() for x in (root/'power.plist').read_bytes().split(b'\0') if x.strip()]
reports=[plistlib.loads(part) for part in parts]
if len(reports)<600 or any(not isinstance(r,dict) or not r for r in reports):
    raise ValueError('Missing or malformed periodic telemetry samples')
result=dict(native_samples=summary['samples'],plist_reports=len(reports),
            status='Raw capture format and native invariants passed. Hardware correlation remains unreviewed.')
(root/'capture-validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
