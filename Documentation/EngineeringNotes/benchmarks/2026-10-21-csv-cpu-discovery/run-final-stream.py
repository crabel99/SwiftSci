from pathlib import Path
import hashlib,json,subprocess,sys,time
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE,policy
from runner import environment,power_state,verify_uninstrumented
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cases=['bike-hour','unique-shuffled','Aotizhongxin','energy','energy-date-full'];engines=['indexed','counted','count-only'];builds={}
for label in engines:
 d=R/'aux'/label;record=json.loads((R/'build'/label/'build.json').read_text());link=json.loads((d/'StreamProbe.build.json').read_text());assert h(d/'StreamProbe')==link['binary_sha256'];verify_uninstrumented(d/'StreamProbe')
 source=Path(record['variant']['path']);assert not subprocess.check_output(['git','status','--porcelain'],cwd=source)
 for rel,digest in record['sources'].items():assert h(source/rel)==digest
 builds[label]={'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),'binary_sha256':link['binary_sha256'],'build_receipt_sha256':h(R/'build'/label/'build.json'),'link_receipt_sha256':h(d/'StreamProbe.build.json')}
inputs={case:json.loads((R/'inputs'/(case+'.json')).read_text()) for case in cases}
for d in inputs.values():assert h(Path(d['path']))==d.get('sha256',d.get('source_sha256'))
# Untimed exact-output preflight for every configuration before accepting timing evidence.
P=R/'final-stream-preflight';P.mkdir(exist_ok=False)
for case in cases:
 for label in engines:
  p=subprocess.run([str(R/'aux'/label/'StreamProbe'),str(R/'inputs'/(case+'.json')),'10000'],env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=120)
  (P/(case+'-'+label+'.stderr')).write_text(p.stderr);assert p.returncode==0,p.stderr
  d=json.loads(p.stdout);(P/(case+'-'+label+'.json')).write_text(json.dumps(d,indent=2)+'\n');assert d['validated'],d
print('Preflight15passed',flush=True)
D=R/'final-stream-measurement';D.mkdir(exist_ok=False);power=power_state();assert power['source']=='AC',power
plan={'builds':builds,'inputs':inputs,'cases':cases,'engines':engines,'rounds':6,'chunk_size':10000,'orders':[engines[i:]+engines[:i] for i in range(3)]+[list(reversed(engines[i:]+engines[:i])) for i in range(3)],'power_start':power,'environment':environment(),'policy':policy(PRODUCTION_MODE),'controller_sha256':h(Path(__file__)),'harness_sha256':h(R/'StreamProbe.swift'),'criteria':{'correctness':'Every worker must validate all per-column hashes, native types, row and column order and total rows in a separate untimed repeat; timed pass checks total rows.','cpu':'Review any median CPU regression above10percent, not automatically hidden by elapsed speed or memory savings.','memory':'Shared scanner change must preserve streaming memory bounds; compare peak and held RSS. RSS includes mapped file pages and is not allocation count.','scope':'Natural native parallelism on matching CPU backend. No build/tests run by this task during measurements. No caller retention; one consumer requests immediately after each owned frame is released. No universal weighted efficiency score.'}}
(D/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
with (D/'workers.jsonl').open('x') as out:
 for case in cases:
  for rnd,order in enumerate(plan['orders']):
   power=power_state();assert power['source']=='AC',power
   inp=json.loads((R/'inputs'/(case+'.json')).read_text())
   with Path(inp['path']).open('rb') as f:
    while f.read(1024*1024):pass
   for label in order:
    p=subprocess.run([str(R/'aux'/label/'StreamProbe'),str(R/'inputs'/(case+'.json')),'10000'],env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=120)
    (D/(case+'-'+str(rnd)+'-'+label+'.stderr')).write_text(p.stderr)
    if p.returncode:
     out.write(json.dumps({'case':case,'engine':label,'round':rnd,'failed':True,'exit_code':p.returncode,'stderr':p.stderr})+'\n');out.flush();raise RuntimeError(p.stderr)
    d=json.loads(p.stdout);assert d['validated'],d
    d.update(case=case,engine=label,round=rnd,power=power)
    out.write(json.dumps(d)+'\n');out.flush();print(case,rnd,label,round(d['total_cpu_ns']/1e6,3),'CPUms',round(d['peak_after_bytes']/2**20,3),'peakMiB',flush=True)
end=power_state();assert end['source']=='AC';(D/'power-end.json').write_text(json.dumps(end,indent=2)+'\n');print('Complete90validatedstreamworkers',flush=True)
