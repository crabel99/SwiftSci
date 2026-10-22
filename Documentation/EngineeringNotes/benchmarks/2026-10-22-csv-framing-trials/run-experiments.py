from pathlib import Path
import subprocess,json,time
R=Path(__file__).resolve().parent;records=[]
for label,script in [('derived','derived-pilot.py'),('framing','scan-all.py')]:
 print('Starting',label,flush=True);start=time.time()
 with (R/(label+'.log')).open('w') as log:p=subprocess.run(['python3',str(R/script)],stdout=log,stderr=subprocess.STDOUT,timeout=900)
 records.append(dict(label=label,script=script,exit_code=p.returncode,elapsed_seconds=time.time()-start));(R/'experiment-status.json').write_text(json.dumps(records,indent=2)+'\n');assert p.returncode==0,(R/(label+'.log')).read_text()[-2000:];print('Finished',label,flush=True)
