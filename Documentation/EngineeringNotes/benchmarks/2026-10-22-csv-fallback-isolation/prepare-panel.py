from pathlib import Path
import json
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-prefix-selection-20261022')
contracts=[Path(p) for p in json.loads((R/'metadata-boundary-contracts.json').read_text())]
rows=[]
for p in contracts:
 d=json.loads(p.read_text());a=d['preparation'];budget=2*a['tokens']+a['bytes']
 if p.stem.startswith('long-keys-64-') and d['rows'] in [budget-1,budget,budget+1]:
  for scope in ['eager','stream']:
   for policy in ['parallel','serial']:rows.append(dict(case=p.stem,path=str(p),scope=scope,policy=policy))
for name,policy in [('long-keys-64-rows-3328-nulls-0','serial'),('long-keys-64-rows-3392-nulls-0','parallel')]:rows.append(dict(case=name,path=str(P/'crossover-inputs'/(name+'.json')),scope='stream',policy=policy))
assert len(rows)==26
(R/'metadata-calibration-panel.json').write_text(json.dumps(dict(cases=rows,workers_per_label_per_case=120,labels=['cleanup','twin','metadata'],hashing='native',review_limits='Existing10percentCPU,5percent+8MiBpeak.Identical-binarycontrolmustpass.Noflagwaivers.'),indent=2)+'\n')
print(len(contracts),'boundary contracts;',len(rows),'prospective calibration scope/policy cases')
