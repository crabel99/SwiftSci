from pathlib import Path
import hashlib,json,subprocess,sys,statistics as st
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-wide-profile-20261022');Q=Path('/private/tmp/swiftsci-csv-plan-profile-20261022');E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE,policy
from runner import environment,power_state,verify_uninstrumented
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
engines=['original','parent-parallel','parallel','parent-serial','serial'];roots={'original':E/'build/indexed','parent-parallel':P/'build/production','parent-serial':P/'build/production','parallel':R/'build/production','serial':R/'build/production'}
sources={'original':Path('/private/tmp/swiftsci-csv-scoped-simd-20261021'),'parent-parallel':Path('/private/tmp/swiftsci-csv-column-concurrency-control-20261022'),'parent-serial':Path('/private/tmp/swiftsci-csv-column-concurrency-control-20261022'),'parallel':S,'serial':S}
receipts={};binaries={}
for e in engines:
 d=roots[e];rec=json.loads((d/'build.json').read_text());source=sources[e]
 assert not subprocess.check_output(['git','status','--porcelain'],cwd=source)
 for rel,digest in rec['sources'].items():assert h(source/rel)==digest
 stream=(E/'aux/indexed' if e=='original' else d)/'StreamProbe'
 binaries[e]={'eager':d/'ResourceProbe','stream':stream}
 for b in binaries[e].values():verify_uninstrumented(b)
 assert h(d/'ResourceProbe')==rec['binary_sha256']
 sr=json.loads(stream.with_name('StreamProbe.build.json').read_text());assert h(stream)==sr['binary_sha256']
 receipts[e]={'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),'module_receipt_sha256':h(d/'build.json'),'binaries':{k:{'path':str(b),'sha256':h(b)} for k,b in binaries[e].items()}}
cases=[('eager',case,mode) for case,mode in [('bike-day','known'),('bike-hour','known'),('unique-shuffled','known'),('Aotizhongxin','known'),('Wanliu','known'),('energy','known'),('energy','infer'),('energy-date-full','known'),('late-bool','infer'),('late-text','infer')]]
cases += [('stream',case,'known') for case in ['date-100000-1','bike-hour','unique-shuffled','Aotizhongxin','energy','energy-date-full']]
inputs={}
for scope,case,mode in cases:
 p=Q/'inputs'/(case+'.json')
 if not p.exists():p=E/'inputs'/(case+'.json')
 inp=json.loads(p.read_text());assert h(Path(inp['path']))==inp.get('sha256',inp.get('source_sha256'));inputs[case]={'path':str(p),'contract':inp}
orders=[engines[i:]+engines[:i] for i in range(len(engines))]+[list(reversed(engines[i:]+engines[:i])) for i in range(len(engines))]
D=R/'acceptance';D.mkdir(exist_ok=False)
assert power_state()['source']=='AC'
plan=dict(receipts=receipts,inputs=inputs,orders=orders,cases=cases,environment=environment(),policy=policy(PRODUCTION_MODE),power_start=power_state(),controller_sha256=h(Path(__file__)),criteria={'output':'Every value, native type, null position and row/column order must match each independent input contract. Streaming uses a separate untimed full-output repeat.','cpu':'Process user+system time. Review both final modes against their matching parent conversion policy. Review CPU median increases above10percent. Original is historical native-parallel context only.','memory':'Same internal16384-row bound. Review peak-RSS increase above5percent+8MiB. RSS is not allocation count.','conditions':'AC, CPU backend, native system scheduling in default mode; serial selector disables only column-conversion workers. Fresh processes, warmed input, no task builds/tests/profilers during acceptance. No outlier trimming. No energy claim.'})
(D/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
records=[]
with (D/'workers.jsonl').open('x') as out:
 for scope,case,mode in cases:
  config=Path(inputs[case]['path'])
  for rnd,order in enumerate(orders):
   assert power_state()['source']=='AC'
   with Path(inputs[case]['contract']['path']).open('rb') as f:
    while f.read(1024*1024):pass
   for e in order:
    args=[str(config),mode,'fresh','1'] if scope=='eager' else [str(config),'10000']
    if e in ['serial','parent-serial']:args+=['serial']
    cmd=[str(binaries[e][scope]),*args];p=subprocess.run(cmd,capture_output=True,text=True,timeout=180,env=worker_environment(PRODUCTION_MODE));assert p.returncode==0,(cmd,p.stderr)
    d=json.loads(p.stdout);assert d['validated'],d
    d.update(scope=scope,case=case,mode=mode,engine=e,round=rnd);records.append(d);out.write(json.dumps(d)+'\n');out.flush()
  subset=[r for r in records if (r['scope'],r['case'],r['mode'])==(scope,case,mode)]
  print(scope,case,mode,{e:round(st.median(r.get('samples',[r])[0]['total_cpu_ns'] for r in subset if r['engine']==e)/1e6,3) for e in engines},flush=True)
summary=[]
for scope,case,mode in cases:
 for e in engines:
  rs=[r.get('samples',[r])[0] for r in records if (r['scope'],r['case'],r['mode'],r['engine'])==(scope,case,mode,e)]
  summary.append(dict(scope=scope,case=case,mode=mode,engine=e,medians={k:st.median(r[k] for r in rs) for k in ['total_cpu_ns','total_ns',('process_peak_held_bytes' if scope=='eager' else 'peak_after_bytes')]}))
(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(D/'power-end.json').write_text(json.dumps(power_state(),indent=2)+'\n')
flags=[]
for a in summary:
 if a['engine'] not in ['parallel','serial']:continue
 b=next(b for b in summary if b['engine']=='parent-'+a['engine'] and (b['scope'],b['case'],b['mode'])==(a['scope'],a['case'],a['mode']))
 if a['medians']['total_cpu_ns']>b['medians']['total_cpu_ns']*1.10:flags.append(dict(candidate=a,parent=b,reason='CPU review limit'))
 mem='process_peak_held_bytes' if a['scope']=='eager' else 'peak_after_bytes'
 if a['medians'][mem]>b['medians'][mem]*1.05+8*2**20:flags.append(dict(candidate=a,parent=b,reason='Memory review limit'))
(D/'review-flags.json').write_text(json.dumps(flags,indent=2)+'\n');print(len(records),'validated workers;',len(flags),'review flags',flush=True)
