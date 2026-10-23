from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-prefix-selection-20261022')
(R/'baseline').symlink_to(P/'baseline',target_is_directory=True)
for name in ['run-acceptance.py','run-mode-controls.py','run-text-controls.py','run-long-key-controls.py','text-contracts.json','long-key-contracts.json']:
 shutil.copy2(P/name,R/name)
for name in ['run-acceptance.py','run-mode-controls.py','run-text-controls.py','run-long-key-controls.py']:
 p=R/name;s=p.read_text()
 if name=='run-acceptance.py':s=s.replace("'parallel':R/'build/production','serial':R/'build/production'","'parallel':R/'build/metadata','serial':R/'build/metadata'")
 else:s=s.replace("bins={e:(P if e.startswith('parent-') else R)/'build/production/ResourceProbe' for e in engines}","bins={e:(P/'build/production/ResourceProbe' if e.startswith('parent-') else R/'build/metadata/ResourceProbe') for e in engines}")
 p.write_text(s)
# Reuse the independently hashed generator with an additional prospective budget.
s=(P/'prepare-controls.py').read_text();s=s[:s.index('# Retain the wider')];s=s.replace("D=R/'crossover-inputs'","D=R/'metadata-boundary-inputs'").replace('b in [byte_work,combined_work]','b in [byte_work,combined_work,2*count+byte_work]').replace("R/'crossover-contracts.json'","R/'metadata-boundary-contracts.json'")
(R/'prepare-boundaries.py').write_text(s)
# Freeze a prospective performance panel around the new64long-token boundary.
s='''from pathlib import Path
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
(R/'metadata-calibration-panel.json').write_text(json.dumps(dict(cases=rows,workers_per_label_per_case=120,labels=['cleanup','twin','metadata'],hashing='native',review_limits='Existing10percentCPU,5percent+8MiBpeak.Identical-binarycontrolmustpass.Noflagwaivers.'),indent=2)+'\\n')
print(len(contracts),'boundary contracts;',len(rows),'prospective calibration scope/policy cases')
'''
(R/'prepare-panel.py').write_text(s)
