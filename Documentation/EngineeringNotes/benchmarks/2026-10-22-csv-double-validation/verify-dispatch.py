from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent;extract={}
for label,lo,hi in [('current',0x100032cb0,0x100032cfc),('production',0x1000324d0,0x100032530)]:
 receipt=json.loads((R/('sample-'+label+'-build.json')).read_text());assert hashlib.sha256((R/('SamplingNumeric-'+label)).read_bytes()).hexdigest()==receipt['binary_sha256']
 rows=[]
 for line in (R/('disassembly-'+label+'.txt')).read_text().splitlines():
  try:a=int(line.split()[0],16)
  except (ValueError,IndexError):continue
  if lo<=a<hi:rows.append(line)
 extract[label]=rows
assert any('\tblr\t' in line for line in extract['current'])
assert any('parseDouble' in line and '\tbl\t' in line for line in extract['production'])
a=json.loads((R/'sample-current-build.json').read_text());b=json.loads((R/'sample-production-build.json').read_text());assert a['harness_sha256']==b['harness_sha256']
(R/'dispatch-proof.json').write_text(json.dumps(dict(excerpts=extract,harness_sha256=a['harness_sha256'],note='Pinned binary offsets map to the hot inferred-Double frames. The parent branches through a decoder witness; the candidate calls the byte parser directly. This is not a CPU ratio derived from sample counts. A different compiler or build requires new symbol mapping.'),indent=2)+'\n')
print('Verified pinned indirect and direct call excerpts')
