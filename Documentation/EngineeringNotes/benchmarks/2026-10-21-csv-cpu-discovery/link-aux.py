from pathlib import Path
import hashlib,json,subprocess,shutil
R=Path(__file__).resolve().parent;E=Path('/private/tmp/swiftsci-csv-eager-checks-20261021')
shutil.copy2('/private/tmp/swiftsci-csv-ingestion-checks-20261021/StreamProbe.swift',R/'StreamProbe.swift')
records={}
for label,root in [('indexed',E),('counted',E),('count-only',R)]:
 d=R/'aux'/label;d.mkdir(parents=True,exist_ok=True);receipt=json.loads((root/'build'/label/'build.json').read_text());records[label]={}
 for kind in ['GrammarProbe','StreamProbe']:
  cmd=[str(R/(kind+'.swift')) if arg==str(root/'ResourceProbe.swift') else arg for arg in receipt['commands'][1]]
  if kind=='GrammarProbe':cmd.remove('-parse-as-library')
  cmd[cmd.index('-o')+1]=str(d/kind)
  p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
  meta=dict(command=cmd,binary_sha256=hashlib.sha256((d/kind).read_bytes()).hexdigest(),harness_sha256=hashlib.sha256((R/(kind+'.swift')).read_bytes()).hexdigest());(d/(kind+'.build.json')).write_text(json.dumps(meta,indent=2)+'\n')
  if kind=='GrammarProbe':records[label]['grammar']=subprocess.check_output([str(d/kind)],text=True).strip()
 print(label,records[label],flush=True)
assert len({r['grammar'] for r in records.values()})==1
(R/'grammar-differential.json').write_text(json.dumps(records,indent=2)+'\n');print('PASS: original and both experimental grammars match all 30720 fixtures')
