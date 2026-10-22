from pathlib import Path
import hashlib,json,subprocess,statistics,sys
R=Path(__file__).resolve().parent;E=Path('/private/tmp/swiftsci-csv-eager-checks-20261021');sys.path.insert(0,'/private/tmp/swiftsci-csv-scoped-simd-20261021/Benchmarks/Tools')
from execution_policy import worker_environment,PRODUCTION_MODE
results=[]
for rows in [1_001,16_385,32_769,100_001]:
 csv=R/f'bool-{rows}.csv';csv.write_text('value\n'+'1\n'*(rows-1)+'true\n');p=R/f'bool-{rows}.json';p.write_text(json.dumps(dict(id=f'bool-{rows}',path=str(csv),delimiter=',',rows=rows,names=['value'],types=['Bool'],hashes=[hashlib.sha256(b'\1\1'*rows).hexdigest()],null_tokens=['','NA'],integral=[False],null_counts=[0])))
 for rnd in range(4):
  for label in (['indexed','counted'] if rnd%2==0 else ['counted','indexed']):
   c=subprocess.run([str(E/'build'/label/'ResourceProbe'),str(p),'infer','fresh','1'],capture_output=True,text=True,env=worker_environment(PRODUCTION_MODE));assert c.returncode==0,c.stderr;d=json.loads(c.stdout);assert d['validated'];d.update(engine=label,rows=rows,round=rnd);results.append(d)
 m={l:statistics.median(d['samples'][0]['total_cpu_ns'] for d in results if d['rows']==rows and d['engine']==l)/1e6 for l in ['indexed','counted']};print(rows,m,'ratio',m['counted']/m['indexed'])
(R/'minimization.json').write_text(json.dumps(results,indent=2)+'\n')
