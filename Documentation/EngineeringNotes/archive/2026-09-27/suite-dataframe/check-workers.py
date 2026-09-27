import hashlib
import json
import struct
import subprocess
from pathlib import Path

root = Path('/Users/crabel/Documents/src/SwiftSci')
run_dir = root / 'Benchmarks/Runs/suite-dataframe-01'
out = Path('/private/tmp/swiftsci-suite-dataframe/negative-workers')
out.mkdir(exist_ok=True)
commands = {
 'swiftsci': ['/Users/crabel/Library/Caches/SwiftSci/standardized-benchmarks/derived/Build/Products/Release/SwiftSciBenchmarkWorker'],
 'pandas': [str(root/'Benchmarks/.venv-standardized/bin/python'), str(root/'Benchmarks/Python/standard_worker.py')],
}
slugs = ['gather-int64', 'select-order', 'sort-int64-desc', 'filter-float-ne', 'matrix-nonsquare', 'replace-isolation', 'group-string-components']
results = []
for slug in slugs:
 case = 'dataframe-' + slug
 original = json.loads((run_dir/(case+'-swiftsci-0.request.json')).read_text())
 for variant in ['control', 'wrong-first-word', 'wrong-last-word', 'bad-input', 'input-change'] + (['float-index', 'bool-index', 'negative-index', 'overflow-int'] if slug=='gather-int64' else []):
  req = dict(original)
  if variant.startswith('wrong-'):
   raw = Path(req['expected_path']).read_bytes()
   values = list(struct.unpack('<'+'d'*(len(raw)//8), raw))
   values[0 if variant=='wrong-first-word' else -1] += 1
   raw = struct.pack('<'+'d'*len(values), *values)
   path = out/(case+'-'+variant+'.f64'); path.write_bytes(raw)
   req.update(expected_path=str(path), expected_sha256=hashlib.sha256(raw).hexdigest())
  elif variant in ('bad-input', 'input-change', 'float-index', 'bool-index', 'negative-index', 'overflow-int'):
   payload = json.loads(Path(req['input_path']).read_text())
   if variant in ('float-index', 'bool-index', 'negative-index'):
    payload['parameters']['indices'] = {'float-index': [1.0], 'bool-index': [True], 'negative-index': [-1]}[variant]
   elif variant == 'overflow-int':
    payload['columns'][0]['values'][0] = '9223372036854775808'
   elif variant == 'bad-input':
    payload['parameters']['expected_answer'] = []
   else:
    c = next(c for c in payload['columns'] if c['type']=='int64') if slug!='group-string-components' else payload['columns'][0]
    i = next(i for i,v in enumerate(c['values']) if v is not None)
    c['values'][i] = '123' if c['type']=='int64' else 'changed-key'
   raw = (json.dumps(payload)+'\n').encode()
   path = out/(case+'-'+variant+'.json'); path.write_bytes(raw)
   req.update(input_path=str(path), input_sha256=hashlib.sha256(raw).hexdigest(), input_bytes=len(raw))
  for engine, command in commands.items():
   path = out/(case+'-'+variant+'-'+engine+'.request.json'); path.write_text(json.dumps(req))
   response = path.with_suffix('.response.json')
   proc = subprocess.run(command+[str(path), str(response)], capture_output=True, text=True, timeout=120)
   record = json.loads(response.read_text())
   assert (record['status']=='passed') == (variant=='control'), (case, variant, engine, record)
   results.append(dict(case=case, variant=variant, engine=engine, status=record['status'], exit_code=proc.returncode, error=record.get('error')))
(out/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
print('PASS: 14 controls and 64 changed-output/input rejections')
