from pathlib import Path
import json,hashlib,subprocess,statistics,sys
R=Path(__file__).resolve().parent;E=Path('/private/tmp/swiftsci-csv-eager-checks-20261021');sys.path.insert(0,'/private/tmp/swiftsci-csv-scoped-simd-20261021/Benchmarks/Tools')
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state
assert power_state()['source']=='AC'
D=R/sys.argv[1];D.mkdir(exist_ok=False);records=[]
for label in ['indexed','counted']:
 receipt=json.loads((E/'build'/label/'build.json').read_text());b=E/'build'/label/'ResourceProbe';assert hashlib.sha256(b.read_bytes()).hexdigest()==receipt['binary_sha256']
for case in ['Aotizhongxin','late-bool']:
 inp=E/'inputs'/(case+'.json');mode='infer' if case=='late-bool' else 'known'
 for rnd in range(6):
  for label in (['indexed','counted'] if rnd%2==0 else ['counted','indexed']):
   p=subprocess.run([str(E/'build'/label/'ResourceProbe'),str(inp),mode,'fresh','1'],capture_output=True,text=True,env=worker_environment(PRODUCTION_MODE));assert p.returncode==0,p.stderr
   d=json.loads(p.stdout);assert d['validated'];d.update(case=case,round=rnd,engine=label);records.append(d)
(D/'workers.json').write_text(json.dumps(records,indent=2)+'\n')
ratios={}
for case in ['Aotizhongxin','late-bool']:
 m={label:statistics.median(d['samples'][0]['total_cpu_ns'] for d in records if d['case']==case and d['engine']==label)/1e6 for label in ['indexed','counted']};ratios[case]=m['counted']/m['indexed'];print(case,m,'CPU ratio',ratios[case],flush=True)
red=ratios['late-bool']>1.10
print('RED: late Boolean CPU exceeds the 10% review gate' if red else 'GREEN: no reproduced late Boolean CPU regression',flush=True)
(D/'verdict.json').write_text(json.dumps(dict(ratios=ratios,regression_reproduced=red),indent=2)+'\n')
raise SystemExit(1 if red else 0)
