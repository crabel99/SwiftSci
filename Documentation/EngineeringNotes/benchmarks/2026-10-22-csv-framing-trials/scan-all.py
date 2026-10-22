from pathlib import Path
import json,subprocess,statistics as st,hashlib
R=Path(__file__).resolve().parent;E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');P=Path('/private/tmp/swiftsci-csv-wide-profile-20261022')
engines=['parent','consume','header','derived-count'];orders=[engines[i:]+engines[:i] for i in range(4)]+[list(reversed(engines[i:]+engines[:i])) for i in range(4)];records=[]
for case,path in [('wide',E/'inputs/Aotizhongxin.json'),('bike',E/'inputs/bike-hour.json'),('energy',E/'inputs/energy.json'),('small',P/'width-inputs/width-18-rows-257.json')]:
 inp=json.loads(path.read_text());hashes=set()
 for rnd,order in enumerate(orders):
  for e in order:
   p=subprocess.run([str(R/('ScanProbe-'+e)),inp['path'],str(ord(inp['delimiter'])),'16384'],capture_output=True,text=True,timeout=180);assert p.returncode==0,p.stderr;d=json.loads(p.stdout);hashes.add((d['rows'],d['fields'],d['sha256'],d['batches']));records.append(dict(case=case,round=rnd,engine=e,result=d))
 assert len(hashes)==1,hashes
 print(case,{e:round(st.median(d['result']['cpu_ns'] for d in records if d['case']==case and d['engine']==e)/1e6,3) for e in engines},flush=True)
(R/'scan-pilot.json').write_text(json.dumps(records,indent=2)+'\n')
