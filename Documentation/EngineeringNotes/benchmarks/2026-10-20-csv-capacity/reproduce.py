from pathlib import Path
import subprocess,json
R=Path(__file__).resolve().parent
P=Path('/Users/crabel/local-ai/spl/swiftsci/pr-resource-metrics-20261018')
records=[]
for mode in ['before','after']:
 for repetition in range(3):
  p=subprocess.run([str(P/f'build/pr39-{mode}/inspect-csv'),str(P/'fixtures/02-pr39-csv-quoted-1000000-4.csv')],capture_output=True,text=True,check=True)
  columns=json.loads(p.stdout);excess=max(c['capacity']/c['count'] for c in columns)
  records.append(dict(variant=mode,repetition=repetition,columns=columns,capacity_ratio=excess))
  print(mode,repetition,'EXCESS' if excess>1.1 else 'bounded',round(excess,4))
(R/'reproduction.json').write_text(json.dumps(records,indent=2)+'\n')
assert all(e['capacity_ratio']>1.1 for e in records if e['variant']=='after'), 'Historical symptom no longer reproduces reliably'
assert all(e['capacity_ratio']<1.1 for e in records if e['variant']=='before')
print('Historical symptom reproduced in 3/3 after workers; absent in 3/3 before workers')
