from pathlib import Path
import subprocess,json,hashlib,time,os,statistics,sys
R=Path(__file__).resolve().parent
OUT=R/'runs';OUT.mkdir(exist_ok=True)
cases=json.loads((R/'cases.json').read_text())
for n,w in [(1,32),(32,32),(256,32),(4096,32),(256,128),(4096,128)]:
 cases.append(dict(id=f'mlp-{n}-{w}',pr=70,mode='mlp',rows=n,width=w))
(R/'all-cases.json').write_text(json.dumps(cases,indent=2)+'\n')
env=os.environ.copy()
removed={}
for k in ['VECLIB_MAXIMUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','POLARS_MAX_THREADS','RAYON_NUM_THREADS']:
 if k in env:removed[k]=env.pop(k)
def command(args):return subprocess.check_output(args,text=True).strip()
host={'hardware':command(['sysctl','-n','machdep.cpu.brand_string']),'os':command(['sw_vers']),'compiler':command(['xcrun','swiftc','--version']),'power':command(['pmset','-g','custom']),'power_source':command(['pmset','-g','batt']),'removed_thread_overrides':removed,'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
assert 'AC Power' in host['power_source']
(R/'host.json').write_text(json.dumps(host,indent=2)+'\n')
receipts={}
for pr in [39,45,70,82]:
 for side in ['before','after']:
  label=f'pr{pr}-{side}';d=R/'build'/label;name='MLPProbe' if pr==70 else 'ResourceProbe';rec=json.loads((d/'build.json').read_text())
  assert hashlib.sha256((d/name).read_bytes()).hexdigest()==rec['binary_sha256']
  receipts[label]=rec
 assert receipts[f'pr{pr}-before']['dependency_objects']==receipts[f'pr{pr}-after']['dependency_objects']
 assert receipts[f'pr{pr}-before']['harness_sha256']==receipts[f'pr{pr}-after']['harness_sha256']
for phase,rounds in [('qualification',1),('timing',5),('memory',3)]:
 for rd in range(rounds):
  order=cases[rd:]+cases[:rd]
  for c in order:
   for side in (['before','after'] if (rd+cases.index(c))%2==0 else ['after','before']):
    dst=OUT/f'{c["id"]}-{phase}-{rd}-{side}.json'
    if dst.exists():raise RuntimeError('Refusing to overwrite '+str(dst))
    assert 'AC Power' in command(['pmset','-g','batt'])
    exe=R/'build'/f'pr{c["pr"]}-{side}'/('MLPProbe' if c['pr']==70 else 'ResourceProbe')
    args=[str(exe),c['mode'],str(c['rows']),str(c['width']),'1' if phase=='qualification' else '7','memory' if phase in ['memory','qualification'] else 'timing']
    if 'file' in c:assert hashlib.sha256(Path(c['file']).read_bytes()).hexdigest()==c['file_sha256'];args.append(c['file'])
    started=time.time();p=subprocess.run(args,env=env,capture_output=True,text=True,timeout=180)
    if p.returncode:
     dst.with_suffix('.failure.json').write_text(json.dumps({'command':args,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2));raise RuntimeError('Worker failure '+dst.name+' '+p.stderr[-500:])
    result=json.loads(p.stdout);assert result['validated'] is True
    expected=1 if phase in ['memory','qualification'] else 7;assert len(result['samples'])==expected
    assert all(s['total_cpu_ns']>=0 and s['total_ns']>0 for s in result['samples'])
    record={'case':c,'phase':phase,'round':rd,'side':side,'command':args,'binary_sha256':receipts[f'pr{c["pr"]}-{side}']['binary_sha256'],'duration_s':time.time()-started,'result':result}
    dst.write_text(json.dumps(record,indent=2)+'\n')
   before=json.loads((OUT/f'{c["id"]}-{phase}-{rd}-before.json').read_text())
   after=json.loads((OUT/f'{c["id"]}-{phase}-{rd}-after.json').read_text())
   if c['pr']==70:assert before['result']['context']==after['result']['context']
  print(phase,'round',rd+1,'complete',flush=True)
print('COMPLETE',len(cases),'cases',len(list(OUT.glob('*.json'))),'workers',flush=True)
