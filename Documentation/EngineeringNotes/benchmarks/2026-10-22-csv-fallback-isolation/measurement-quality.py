from pathlib import Path
import json,statistics as st,random
R=Path(__file__).resolve().parent;D=R/'metadata-calibration';rows=json.loads((D/'summary.json').read_text());flags=[]
for a in rows:
 if a['engine']!='twin':continue
 b=next(b for b in rows if b['engine']=='cleanup' and all(b[k]==a[k] for k in ['case','scope','policy']))
 delta=a['medians']['total_cpu_ns']/b['medians']['total_cpu_ns']-1
 if abs(delta)>0.10:flags.append(dict(control=a,reference=b,reason='Identical-binary CPU deviation exceeds10percent in either direction'))
 m='process_peak_held_bytes' if a['scope']=='eager' else 'peak_after_bytes'
 if abs(a['medians'][m]-b['medians'][m])>b['medians'][m]*0.05+8*2**20:flags.append(dict(control=a,reference=b,reason='Identical-binary peak deviation exceeds5percent+8MiB in either direction'))
(D/'quality-gate.json').write_text(json.dumps(dict(passed=not flags,flags=flags,scope='Additional two-sided A/A quality gate. Keeps every original directional review flag. Does not waive candidate limits or treat fixed hashing as production acceptance.'),indent=2)+'\n');print('Two-sided identical-binary quality flags:',len(flags))
