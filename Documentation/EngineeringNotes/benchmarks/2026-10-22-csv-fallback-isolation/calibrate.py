from pathlib import Path
import hashlib,json,subprocess,statistics as st,sys,time
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');P=Path('/private/tmp/swiftsci-csv-prefix-selection-20261022');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state,environment,verify_uninstrumented
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
label=sys.argv[1];cycles=int(sys.argv[2]);D=R/label;D.mkdir(exist_ok=False)
source={'cleanup':'cleanup','twin':'cleanup','selected':'production','noprep':'no-preparation','preflight':'preflight'}
engines=[f'{e}-{mode}' for e in source for mode in ['native','fixed']]
roots={e:R/'build'/source[e.rsplit('-',1)[0]] for e in engines}
v=json.loads((R/'variants.json').read_text())
receipts={}
for e,d in roots.items():
 base=source[e.rsplit('-',1)[0]];rec=json.loads((d/'build.json').read_text());assert all(h(Path(v[base]['path'])/p)==sha for p,sha in rec['sources'].items());b=d/'StreamRepeatProbe';verify_uninstrumented(b)
 sr=json.loads((d/'StreamRepeatProbe.build.json').read_text());assert h(b)==sr['binary_sha256']
 receipts[e]=dict(binary=str(b),sha256=h(b),module_receipt_sha256=h(d/'build.json'))
assert receipts['cleanup-native']['sha256']==receipts['twin-native']['sha256']
orders=([engines[i:]+engines[:i] for i in range(len(engines))]+[list(reversed(engines[i:]+engines[:i])) for i in range(len(engines))])*cycles
cases=[('long-keys-64-rows-3328-nulls-0','serial'),('long-keys-64-rows-3392-nulls-0','parallel')]
(D/'plan.json').write_text(json.dumps(dict(engines=engines,orders=orders,cases=cases,receipts=receipts,environment=environment(),controller_sha256=h(Path(__file__)),scope='Interleaved native and diagnostic fixed hashing, exact same bytes/schema/nulls/row count, two warmups and five measured streams per worker, per-worker medians. Fixed hashing never qualifies production. Existing10percentCPU and5percent+8MiBpeak review thresholds retained. A/A must pass before interpreting A/B.'),indent=2)+'\n')
rs=[]
with (D/'workers.jsonl').open('x') as out:
 for case,policy in cases:
  path=P/'crossover-inputs'/(case+'.json');inp=json.loads(path.read_text());assert h(Path(inp['path']))==inp['source_sha256']
  for rnd,order in enumerate(orders):
   assert power_state()['source']=='AC'
   for e in order:
    mode=e.rsplit('-',1)[1];env=worker_environment(PRODUCTION_MODE);env.pop('SWIFT_DETERMINISTIC_HASHING',None)
    if mode=='fixed':env['SWIFT_DETERMINISTIC_HASHING']='1'
    p=subprocess.run(['StreamRepeatProbe',str(path),str(inp['rows']),policy],executable=str(roots[e]/'StreamRepeatProbe'),env=env,capture_output=True,text=True,timeout=120);assert p.returncode==0,(e,p.stderr)
    d=json.loads(p.stdout);assert d['validated'];assert len(d['samples'])==5
    d.update(case=case,policy=policy,engine=e,round=rnd,hash_mode=mode,comparison_sample={k:st.median(x[k] for x in d['samples']) for k in d['samples'][0]})
    rs.append(d);out.write(json.dumps(d)+'\n');out.flush()
  print(case,policy,{e:round(st.median(x['comparison_sample']['total_cpu_ns'] for x in rs if x['case']==case and x['engine']==e)/1e6,3) for e in engines},flush=True)
summary=[];flags=[]
for case,policy in cases:
 for e in engines:
  a=[r['comparison_sample'] for r in rs if r['case']==case and r['engine']==e]
  summary.append(dict(case=case,policy=policy,engine=e,workers=len(a),medians={k:st.median(x[k] for x in a) for k in ['total_cpu_ns','total_ns','peak_after_bytes']},mean_cpu_ns=st.mean(x['total_cpu_ns'] for x in a)))
for a in summary:
 base,mode=a['engine'].rsplit('-',1)
 if base=='cleanup':continue
 b=next(b for b in summary if b['case']==a['case'] and b['engine']=='cleanup-'+mode)
 if a['medians']['total_cpu_ns']>b['medians']['total_cpu_ns']*1.10:flags.append(dict(candidate=a,parent=b,reason='CPU review limit'))
 if a['medians']['peak_after_bytes']>b['medians']['peak_after_bytes']*1.05+8*2**20:flags.append(dict(candidate=a,parent=b,reason='Memory review limit'))
(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(D/'review-flags.json').write_text(json.dumps(flags,indent=2)+'\n')
print(len(rs),'validated workers; flags',[(f['candidate']['engine'],f['candidate']['case'],f['reason']) for f in flags],flush=True)
