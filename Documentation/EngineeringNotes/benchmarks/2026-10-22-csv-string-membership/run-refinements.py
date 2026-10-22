from pathlib import Path
import json,subprocess,time
R=Path(__file__).resolve().parent;records=[]
phases=[('refined-screen','screen.py',['refined-screen','1','production','required-prep','prefix-required-prep']),('refined-setup','setup-controls.py',['refined-setup','2','production','required-prep','prefix-required-prep'])]
for name,script,args in phases:
 record=dict(label=name,command=['python3',str(R/script),*args],start=time.time());records.append(record)
 (R/'refinement-status.json').write_text(json.dumps(records,indent=2)+'\n');print('Starting',name,flush=True)
 with (R/(name+'.log')).open('w') as f:p=subprocess.run(record['command'],stdout=f,stderr=subprocess.STDOUT,timeout=1200)
 record.update(exit_code=p.returncode,seconds=time.time()-record['start']);(R/'refinement-status.json').write_text(json.dumps(records,indent=2)+'\n')
 assert p.returncode==0,(R/(name+'.log')).read_text()[-2000:]
 print(name,'finished; review flags',len(json.loads((R/name/'review-flags.json').read_text())),flush=True)
