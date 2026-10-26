from pathlib import Path
import hashlib,json,subprocess,sys,statistics
import numpy as np
from sklearn.datasets import load_wine
root=Path(__file__).resolve().parent
rng=np.random.default_rng(42)
fixtures=[('wine',load_wine().data,4),('tall',rng.normal(size=(12000,6))@rng.normal(size=(6,24))+rng.normal(scale=.1,size=(12000,24)),6),('wide',rng.normal(size=(160,8))@rng.normal(size=(8,512))+rng.normal(scale=.1,size=(160,512)),8)]
rows=[];checks=[];identity={}
for name,x,k in fixtures:
 path=root/(name+'.csv')
 np.savetxt(path,x,delimiter=',',header=','.join('x'+str(c) for c in range(x.shape[1])),comments='',fmt='%.17g')
 identity[name]={'shape':list(x.shape),'k':k,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'generator':'sklearn.datasets.load_wine' if name=='wine' else 'numpy.default_rng(42), sequential latent Gaussian + noise'}
 split=len(x)*4//5;qi=list(range(split,len(x)))+[split,split]
 train=x[:split];query=x[qi];mu=train.mean(axis=0);sd=train.std(axis=0);sd[sd==0]=1
 z=(train-mu)/sd;zq=(query-mu)/sd;pm=z.mean(axis=0)
 _,singular,vt=np.linalg.svd(z-pm,full_matrices=False)
 for r in range(len(vt)):
  if vt[r,np.argmax(np.abs(vt[r]))]<0:vt[r]*=-1
 ref={'mean':pm,'components':vt[:k],'variance':singular[:k]**2/(len(z)-1),'ratios':singular[:k]**2/(singular**2).sum(),'training':((z-pm)@vt[:k].T).reshape(-1),'query':((zq-pm)@vt[:k].T).reshape(-1)}
 for solver in ['full','randomized']:
  baseline=None
  for repetition in range(3):
   modes=[('baseline','legacy'),('candidate','legacy'),('candidate','batch'),('candidate','row'),('candidate','column')]
   if repetition%2:modes=modes[::-1]
   for binary,mode in modes:
    cmd=[str(root/binary),str(path),str(x.shape[1]),str(k),solver,mode]
    done=subprocess.run(cmd,capture_output=True,text=True)
    if done.returncode:raise RuntimeError(str(cmd)+'\n'+done.stderr)
    d=json.loads(done.stdout);out=root/'raw'/f'{name}-{solver}-{binary}-{mode}-{repetition}.json';out.parent.mkdir(exist_ok=True);out.write_text(done.stdout)
    assert d['sourceRows']==qi
    if binary=='baseline' and repetition==0:baseline=d
    rows.append({'fixture':name,'solver':solver,'binary':binary,'mode':mode,'repetition':repetition,**{m:d[m] for m in ['elapsed','userCPU','systemCPU','peakRSSBytes','retainedRSSBytes']}})
  base=json.loads((root/'raw'/f'{name}-{solver}-baseline-legacy-0.json').read_text())
  for binary,mode in [('baseline','legacy'),('candidate','legacy'),('candidate','batch'),('candidate','row'),('candidate','column')]:
   for repetition in range(3):
    d=json.loads((root/'raw'/f'{name}-{solver}-{binary}-{mode}-{repetition}.json').read_text())
    for key in ref:
     a=np.asarray(d[key]);b=np.asarray(base[key]);err=float(np.max(np.abs(a-b)))
     # Same solver, predeclared absolute/relative Double tolerance, no timing threshold.
     np.testing.assert_allclose(a,b,atol=1e-12,rtol=1e-12)
     checks.append({'fixture':name,'solver':solver,'binary':binary,'mode':mode,'repetition':repetition,'field':key,'baselineMaxAbs':err})
     if solver=='full':np.testing.assert_allclose(a,ref[key],atol=1e-12,rtol=1e-12)
  print(name,solver,'passed',flush=True)
(root/'identity.json').write_text(json.dumps(identity,indent=2)+'\n')
(root/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
(root/'measurements.json').write_text(json.dumps(rows,indent=2)+'\n')
summary=[]
for name,_,_ in fixtures:
 for solver in ['full','randomized']:
  for binary,mode in [('baseline','legacy'),('candidate','legacy'),('candidate','batch'),('candidate','row'),('candidate','column')]:
   group=[r for r in rows if (r['fixture'],r['solver'],r['binary'],r['mode'])==(name,solver,binary,mode)]
   summary.append({'fixture':name,'solver':solver,'binary':binary,'mode':mode,**{m:statistics.median(r[m] for r in group) for m in ['elapsed','userCPU','systemCPU','peakRSSBytes','retainedRSSBytes']}})
(root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print('PASS',len(rows),'fresh processes;',len(checks),'field checks')
