from pathlib import Path
import gzip,hashlib,json,shutil,subprocess,tarfile,difflib,re,statistics as st
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');B=Path('/private/tmp/swiftsci-csv-vector-mask-control-20261022');P=Path('/private/tmp/swiftsci-csv-loop-profile-20261022');N=Path('/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
head=json.loads((R/'final-head.json').read_text())['commit']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()==head
assert subprocess.check_output(['git','branch','--show-current'],cwd=N,text=True).strip()=='codex/engineering-notes'
for root in [S,B,N]:assert not subprocess.check_output(['git','status','--porcelain'],cwd=root)
phases=json.loads((R/'finish-status.json').read_text());assert len(phases)==6 and all(p.get('exit_code')==0 for p in phases)
for label in ['small-null-release-final','small-null-debug','small-null-asan']:
 d=json.loads((R/(label+'-summary.json')).read_text());assert d['passedTests']==387 and d['failedTests']==0 and d['skippedTests']==0
 rec=json.loads((R/(label+'-command.json')).read_text());assert all(h(S/p)==sha for p,sha in rec['source_sha256'].items())
assert len(list((R/'standardized').glob('*.response.json')))==190
assert json.loads((R/'grammar-result.json').read_text())==json.loads((P/'grammar-result.json').read_text())
summaries={}
for scope,count in [('acceptance',512),('mode-controls',544),('text-controls',1024)]:
 assert sum(1 for _ in (R/scope/'workers.jsonl').open())==count
 assert not json.loads((R/scope/'review-flags.json').read_text()),scope
 summaries[scope]=json.loads((R/scope/'summary.json').read_text())
D=N/'Documentation/EngineeringNotes/benchmarks/2026-10-22-csv-small-null-lookup';D.mkdir(parents=True,exist_ok=False)
pilots=[]
for file in ['pilot.json','bounded-pilot.json','batch-pilot.json']:
 data=json.loads((R/file).read_text());records=data['records'];keys=sorted({(r['case'],r['mode'],r['policy'],r['engine']) for r in records})
 for case,mode,policy,e in keys:
  rs=[r['result']['samples'][0] for r in records if (r['case'],r['mode'],r['policy'],r['engine'])==(case,mode,policy,e)]
  pilots.append(dict(study=file,case=case,mode=mode,policy=policy,engine=e,samples=len(rs),medians={k:st.median(r[k] for r in rs) for k in ['total_cpu_ns','total_ns','process_peak_held_bytes']}))
(R/'pilot-summaries.json').write_text(json.dumps(pilots,indent=2)+'\n')
for p in [*R.glob('*.py'),*R.glob('*.swift'),*R.glob('*.json'),*R.glob('*.md')]:
 if p.is_file():shutil.copy2(p,D/p.name)
for pattern in ['*.log','*.sample.txt','*disassembly*.txt','*.stderr']:
 for p in R.glob(pattern):
  with gzip.open(D/(p.name+'.gz'),'wb') as f:f.write(p.read_bytes())
for scope in [*summaries,'fallback-followup']:
 out=D/scope;out.mkdir()
 for p in (R/scope).iterdir():
  if p.suffix=='.jsonl':
   with gzip.open(out/(p.name+'.gz'),'wb') as f:f.write(p.read_bytes())
  elif p.is_file():shutil.copy2(p,out/p.name)
for label,root in [('parent',P/'build/production'),*[(label,R/'build'/label) for label in json.loads((R/'variants.json').read_text())]]:
 out=D/'build-receipts'/label;out.mkdir(parents=True)
 for name in ['build.json','module-signature.json','GrammarProbe.build.json','StreamProbe.build.json']:
  if (root/name).is_file():shutil.copy2(root/name,out/name)
shutil.copy2(R/'standard-worker/SwiftSciBenchmarkWorker.build.json',D/'standard-worker.build.json')
assert sum(1 for _ in (R/'fallback-followup/workers.jsonl').open())==2052
follow=json.loads((R/'fallback-followup/summary.json').read_text())
ft=['| Input | Policy | Samples per implementation | CPU ms, parent → committed → boundary trial | Committed CPU change | Peak RSS MiB, parent → committed |','|---|---|---:|---:|---:|---:|']
for a in follow:
 if a['engine']!='row-null':continue
 group={b['engine']:b['medians'] for b in follow if b['case']==a['case'] and b['policy']==a['policy']};y=group['parent'];x=a['medians'];t=group['batch-null']
 ft.append(f"| {a['case']} | {a['policy']} | {a['samples']} | {y['total_cpu_ns']/1e6:.3f} → {x['total_cpu_ns']/1e6:.3f} → {t['total_cpu_ns']/1e6:.3f} | {(x['total_cpu_ns']/y['total_cpu_ns']-1)*100:+.1f}% | {y['process_peak_held_bytes']/2**20:.2f} → {x['process_peak_held_bytes']/2**20:.2f} |")
(D/'fallback-followup.md').write_text('# Additional fallback measurements\n\nThese native fresh-process observations retain the original final matrix unchanged. The committed column uses row-null in the raw records. Boundary trial uses batch-null. The trial is not production code. Control cases have 42 samples per implementation and policy. The default air-quality reference has six. No outliers are removed. See [study methods](README.md).\n\n'+'\n'.join(ft)+'\n')

with tarfile.open(D/'standardized-artifacts.tar.gz','w:gz') as archive:
 for p in sorted((R/'standardized').iterdir()):
  if p.is_file():archive.add(p,arcname=p.name)
patches=R/'trial-patches';patches.mkdir(exist_ok=False)
for label in json.loads((R/'variants.json').read_text()):
 if label=='production':continue
 diff=[]
 for p in sorted((R/(label+'-trial')/'Sources/SwiftDataFrame').rglob('*.swift')):
  rel=p.relative_to(R/(label+'-trial'));old=B/rel
  if old.read_bytes()!=p.read_bytes():diff.extend(difflib.unified_diff(old.read_text().splitlines(keepends=True),p.read_text().splitlines(keepends=True),fromfile='a/'+str(rel),tofile='b/'+str(rel)))
 (patches/(label+'.patch')).write_text(''.join(diff))
with tarfile.open(D/'experiments.tar.gz','w:gz') as archive:
 archive.add(patches,arcname='trial-patches');archive.add(B/'Sources/SwiftDataFrame',arcname='parent-sources/SwiftDataFrame');archive.add(R/'text-inputs',arcname='text-inputs')
 for case,inp in json.loads((R/'acceptance/plan.json').read_text())['inputs'].items():archive.add(inp['path'],arcname='reference-input-contracts/'+case+'.json')
with gzip.open(D/'source-change.patch.gz','wb') as f:f.write(subprocess.check_output(['git','diff','46a9b9bf951918cd2eb281dadf554efb30c7b0a0...HEAD'],cwd=S))
header=['| Input and schema | Policy | CPU ms, parent → final | CPU change | Elapsed ms, parent → final | Peak RSS MiB, parent → final |','|---|---|---:|---:|---:|---:|']
deltas=[];tables={}
for scope,rows in summaries.items():
 table=list(header)
 for a in rows:
  if a['engine'] not in ['parallel','serial']:continue
  b=next(b for b in rows if b['engine']=='parent-'+a['engine'] and all(b.get(k)==a.get(k) for k in ['scope','case','mode']))
  x=a['medians'];y=b['medians'];mem='peak_after_bytes' if a.get('scope')=='stream' else 'process_peak_held_bytes'
  delta=(x['total_cpu_ns']/y['total_cpu_ns']-1)*100
  label=' '.join(str(a[k]) for k in ['scope','case','mode'] if a.get(k) is not None)
  table.append(f"| {label} | {a['engine']} | {y['total_cpu_ns']/1e6:.3f} → {x['total_cpu_ns']/1e6:.3f} | {delta:+.1f}% | {y['total_ns']/1e6:.3f} → {x['total_ns']/1e6:.3f} | {y[mem]/2**20:.2f} → {x[mem]/2**20:.2f} |")
  deltas.append(dict(scope=scope,case=a['case'],read_scope=a.get('scope'),mode=a.get('mode'),policy=a['engine'],cpu_change_percent=delta,peak_change_mib=(x[mem]-y[mem])/2**20))
 tables[scope]='\n'.join(table)
(D/'final-changes.json').write_text(json.dumps(deltas,indent=2)+'\n')
(D/'controls.md').write_text('# Complete control results\n\nLower CPU time means less process user-plus-system time per correct result. Both policies compare with the same parent policy. See [study methods](README.md).\n\n## Width and numeric null controls\n\n'+tables['mode-controls']+'\n\n## Text null-set controls\n\n'+tables['text-controls']+'\n')
body=(R/'report-body.md').read_text().replace('REFERENCE_TABLE',tables['acceptance']).replace('FINAL_DECISION',(R/'final-decision.md').read_text().strip()).replace('REVIEW_STATUS','No final reference or control median exceeds the CPU or peak-RSS review trigger. Smaller increases remain visible in the tables and raw observations.')
(D/'README.md').write_text(body)
for p in D.glob('*.json'):
 if p.stat().st_size>256*1024:
  data=p.read_bytes()
  with gzip.open(str(p)+'.gz','wb') as f:f.write(data)
  assert gzip.decompress(Path(str(p)+'.gz').read_bytes())==data;p.unlink()
files={str(p.relative_to(D)):h(p) for p in D.rglob('*') if p.is_file() and p.name!='artifact-sha256.json'}
(D/'artifact-sha256.json').write_text(json.dumps(files,indent=2)+'\n')
for body in [(D/'README.md').read_text(),(D/'controls.md').read_text()]:
 for target in re.findall(r'\]\(([^)]+)\)',body):assert (D/target).exists(),target
assert all(h(D/p)==sha for p,sha in files.items())
print(D,len(files),'verified artifacts',flush=True)
