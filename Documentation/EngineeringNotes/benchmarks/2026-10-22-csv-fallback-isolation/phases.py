from pathlib import Path
import hashlib,json,subprocess,statistics as st,sys,time
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');P=Path('/private/tmp/swiftsci-csv-prefix-selection-20261022');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state,verify_uninstrumented,environment
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
D=R/'phases';D.mkdir(exist_ok=False)
engines=['diagnostic-cleanup','diagnostic-selected','diagnostic-preflight'];v=json.loads((R/'variants.json').read_text());receipts={}
for e in engines:
 b=R/'build'/e/'PreparationProbe';verify_uninstrumented(b);rec=json.loads((b.parent/'build.json').read_text());assert all(h(Path(v[e]['path'])/p)==sha for p,sha in rec['sources'].items());receipts[e]=dict(path=str(b),sha256=h(b),receipt_sha256=h(b.parent/'build.json'))
long=P/'crossover-inputs/long-keys-64-rows-3392-nulls-0.json';default=Path('/private/tmp/swiftsci-csv-string-cost-20261022/inputs/Aotizhongxin-default.json')
cases=[('long-'+str(n),long,n) for n in [8,3328,3392,3393,3394,3456,3457,3458,13572]]+ [('default-'+str(n),default,n) for n in [8,38,48,4096]]
orders=([engines[i:]+engines[:i] for i in range(3)]+[list(reversed(engines[i:]+engines[:i])) for i in range(3)])
plan=dict(receipts=receipts,cases=[(n,str(p),rows) for n,p,rows in cases],orders=orders,environment=environment(),scope='Separate phases, native hash randomization. Constructor/factory10000repeatsperworker. Hash100fullvalue-arrayloopsperworker; native output SHA256 checked. Phases are diagnostic, not additive portions of a public CSV read. No production source changes.')
(D/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rs=[]
with (D/'workers.jsonl').open('x') as out:
 for case,path,rows in cases:
  inp=json.loads(path.read_text());tokens=inp['null_tokens'];n=len(tokens);byte_count=sum(len(t.encode()) for t in tokens)
  for action in ['prefix','factory']:
   for rnd,order in enumerate(orders):
    assert power_state()['source']=='AC'
    for e in order:
     cmd=[str(R/'build'/e/'PreparationProbe'),str(path),action,str(rows),'10000'];p=subprocess.run(cmd,env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=120);assert p.returncode==0,(cmd,p.stderr)
     d=json.loads(p.stdout);assert d['validated']
     if action=='prefix':
      expected=e!='diagnostic-cleanup' and rows>=byte_count+n*(2 if e=='diagnostic-preflight' else 1)
      assert d['admitted']==expected,(case,e,d,expected)
     d.update(case=case,engine=e,round=rnd,command=cmd);rs.append(d);out.write(json.dumps(d)+'\n');out.flush()
   print(case,action,{e:round(st.median(x['cpu_per_iteration_ns'] for x in rs if (x['case'],x['action'],x['engine'])==(case,action,e))/1000,4) for e in engines},flush=True)
 for name in ['long-keys-64-rows-3328-nulls-0','long-keys-64-rows-3392-nulls-0']:
  path=P/'crossover-inputs'/(name+'.json');inp=json.loads(path.read_text())
  for mode in ['native','fixed']:
   for rnd,order in enumerate(orders):
    assert power_state()['source']=='AC'
    for e in order:
     env=worker_environment(PRODUCTION_MODE);env.pop('SWIFT_DETERMINISTIC_HASHING',None)
     if mode=='fixed':env['SWIFT_DETERMINISTIC_HASHING']='1'
     cmd=[str(R/'build'/e/'PreparationProbe'),str(path),'hash',str(inp['rows']),'100'];p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=120);assert p.returncode==0,(cmd,p.stderr)
     d=json.loads(p.stdout);assert d['validated'];d.update(case=name,engine=e,round=rnd,hash_mode=mode,command=cmd);rs.append(d);out.write(json.dumps(d)+'\n');out.flush()
   print(name,'hash',mode,{e:round(st.median(x['cpu_per_iteration_ns'] for x in rs if (x['case'],x['action'],x.get('hash_mode'),x['engine'])==(name,'hash',mode,e))/1000,3) for e in engines},flush=True)
summary=[]
keys=sorted({(x['case'],x['action'],x.get('hash_mode','native'),x['engine']) for x in rs})
for case,action,mode,e in keys:
 a=[x for x in rs if (x['case'],x['action'],x.get('hash_mode','native'),x['engine'])==(case,action,mode,e)]
 summary.append(dict(case=case,action=action,hash_mode=mode,engine=e,workers=len(a),cpu_per_iteration_ns=st.median(x['cpu_per_iteration_ns'] for x in a),peak_bytes=st.median(x['peak_bytes'] for x in a),all_native_utf8_tokens=all(x['all_native_utf8_tokens'] for x in a)))
(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(len(rs),'validated phase workers',flush=True)
