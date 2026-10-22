from pathlib import Path
import gzip,hashlib,json,shutil,subprocess,tarfile,difflib,re
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');B=Path('/private/tmp/swiftsci-csv-small-null-control-20261022');N=Path('/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018');P=Path('/private/tmp/swiftsci-csv-number-loop-20261022')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
head=json.loads((R/'final-head.json').read_text())['commit']
for root in [S,B,N]:assert not subprocess.check_output(['git','status','--porcelain'],cwd=root)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()==head
assert subprocess.check_output(['git','branch','--show-current'],cwd=N,text=True).strip()=='codex/engineering-notes'
phases=json.loads((R/'finish-status.json').read_text());assert len(phases)==7 and all(p.get('exit_code')==0 for p in phases)
for label in ['typed-boundary-release','typed-boundary-debug','typed-boundary-asan']:
 d=json.loads((R/(label+'-summary.json')).read_text());assert d['passedTests']==389 and d['failedTests']==0 and d['skippedTests']==0
 rec=json.loads((R/(label+'-command.json')).read_text());assert all(h(S/p)==sha for p,sha in rec['source_sha256'].items())
assert len(list((R/'standardized').glob('*.response.json')))==190
assert json.loads((R/'grammar-result.json').read_text())==json.loads((P/'grammar-result.json').read_text())
expected={'acceptance':512,'mode-controls':544,'text-controls':1024,'long-key-controls':256,'screen':400,'repro':32,'argument-control':72,'launcher-control':18,'local-builder-screen':432}
for label,count in expected.items():assert sum(1 for _ in (R/label/'workers.jsonl').open())==count
D=N/'Documentation/EngineeringNotes/benchmarks/2026-10-22-csv-stream-layout';D.mkdir(parents=True,exist_ok=False)
for p in [*R.glob('*.py'),*R.glob('*.swift'),*R.glob('*.json')]:shutil.copy2(p,D/p.name)
shutil.copy2(R/'report-body.md',D/'report-body.md.in')
def compress(p,out):
 data=p.read_bytes();out.parent.mkdir(parents=True,exist_ok=True)
 with gzip.open(out,'wb') as f:f.write(data)
 assert gzip.decompress(out.read_bytes())==data
for p in R.glob('*.log'):compress(p,D/(p.name+'.gz'))
for label in [*expected,'assembly']:
 out=D/label;out.mkdir()
 for p in (R/label).iterdir():
  if not p.is_file():continue
  if p.suffix in ['.jsonl','.txt','.stderr']:compress(p,out/(p.name+'.gz'))
  elif p.suffix in ['.json','.swift']:shutil.copy2(p,out/p.name)
for label,root in [('parent',P/'build/production'),*[(a,R/'build'/a) for a in json.loads((R/'variants.json').read_text())]]:
 out=D/'build-receipts'/label;out.mkdir(parents=True)
 for name in ['build.json','module-signature.json','GrammarProbe.build.json','StreamProbe.build.json']:
  if (root/name).is_file():shutil.copy2(root/name,out/name)
shutil.copy2(R/'standard-worker/SwiftSciBenchmarkWorker.build.json',D/'standard-worker.build.json')
with tarfile.open(D/'standardized-artifacts.tar.gz','w:gz') as t:
 for p in sorted((R/'standardized').iterdir()):
  if p.is_file():t.add(p,arcname=p.name)
patches=R/'trial-patches';patches.mkdir(exist_ok=True)
for label,v in json.loads((R/'variants.json').read_text()).items():
 if label=='production':continue
 diff=[];root=Path(v['path'])
 for p in sorted((root/'Sources/SwiftDataFrame').rglob('*.swift')):
  rel=p.relative_to(root);old=B/rel
  if old.read_bytes()!=p.read_bytes():diff.extend(difflib.unified_diff(old.read_text().splitlines(keepends=True),p.read_text().splitlines(keepends=True),fromfile='a/'+str(rel),tofile='b/'+str(rel)))
 (patches/(label+'.patch')).write_text(''.join(diff))
with tarfile.open(D/'experiments.tar.gz','w:gz') as t:
 t.add(patches,arcname='trial-patches');t.add(B/'Sources/SwiftDataFrame',arcname='parent-sources/SwiftDataFrame')
 t.add(Path('/private/tmp/swiftsci-csv-null-dispatch-20261022/long-key-inputs'),arcname='long-key-inputs');t.add(P/'text-inputs',arcname='text-inputs')
 for casepath in json.loads(Path('/private/tmp/swiftsci-csv-wide-profile-20261022/width-contracts.json').read_text()):
  t.add(casepath,arcname='width-input-contracts/'+Path(casepath).name)
 for label in expected:
  plan=json.loads((R/label/'plan.json').read_text())
  for case,inp in plan.get('inputs',{}).items():
   path=inp['path'] if isinstance(inp,dict) else inp
   if Path(path).is_file():t.add(path,arcname=label+'-contracts/'+case+'.json')
with gzip.open(D/'source-change.patch.gz','wb') as f:f.write(subprocess.check_output(['git','diff','680ac74b96ab6c6968d83a9511ebdce69d30093b...HEAD'],cwd=S))
header=['| Input and schema | Policy | CPU ms, parent to final | CPU change | Elapsed ms, parent to final | Peak RSS MiB, parent to final |','|---|---|---:|---:|---:|---:|']
tables={};deltas=[]
for label in ['acceptance','mode-controls','text-controls','long-key-controls']:
 rows=json.loads((R/label/'summary.json').read_text());table=list(header)
 for a in rows:
  if a['engine'] not in ['parallel','serial']:continue
  b=next(b for b in rows if b['engine']=='parent-'+a['engine'] and all(b.get(k)==a.get(k) for k in ['scope','case','mode']))
  x=a['medians'];y=b['medians'];mem='peak_after_bytes' if a.get('scope')=='stream' else 'process_peak_held_bytes';delta=(x['total_cpu_ns']/y['total_cpu_ns']-1)*100
  case=' '.join(str(a[k]) for k in ['scope','case','mode'] if a.get(k) is not None)
  table.append(f"| {case} | {a['engine']} | {y['total_cpu_ns']/1e6:.3f} to {x['total_cpu_ns']/1e6:.3f} | {delta:+.1f}% | {y['total_ns']/1e6:.3f} to {x['total_ns']/1e6:.3f} | {y[mem]/2**20:.2f} to {x[mem]/2**20:.2f} |")
  deltas.append(dict(study=label,case=a['case'],scope=a.get('scope'),mode=a.get('mode'),policy=a['engine'],cpu_change_percent=delta,peak_change_mib=(x[mem]-y[mem])/2**20))
 tables[label]='\n'.join(table)
(D/'final-changes.json').write_text(json.dumps(deltas,indent=2)+'\n')
(D/'controls.md').write_text('# Complete resource controls\n\nCPU means process user-plus-system time per correct result. Each policy compares with the same parent policy. See the [study methods](README.md).\n\n## Width and numeric null controls\n\n'+tables['mode-controls']+'\n\n## Text controls\n\n'+tables['text-controls']+'\n\n## Long String keys and values\n\n'+tables['long-key-controls']+'\n')
st=['| Scope | Case | Policy | Implementation | CPU ms | Elapsed ms | Peak RSS MiB |','|---|---|---|---|---:|---:|---:|']
for a in json.loads((R/'screen/summary.json').read_text()):
 x=a['medians'];mem='process_peak_held_bytes' if a['scope']=='eager' else 'peak_after_bytes';st.append(f"| {a['scope']} | {a['case']} | {a['policy']} | {a['engine']} | {x['total_cpu_ns']/1e6:.3f} | {x['total_ns']/1e6:.3f} | {x[mem]/2**20:.2f} |")
(D/'screens.md').write_text('# Compiler-boundary screening\n\nThese 400 diagnostic observations select the candidate for final qualification. The earlier 32-process reproduction overlapped a build and contributes no timing evidence. See the [study methods](README.md).\n\n'+'\n'.join(st)+'\n')
with gzip.open(D/'incremental-change.patch.gz','wb') as f:f.write(subprocess.check_output(['git','diff','1c15702331ed68ea1bd214daf844d1c9d571dacd...HEAD'],cwd=S))
layout=[]
for label in ['argument-control','launcher-control','local-builder-screen']:
 layout+=['## '+label,'','| Scope | Input | Policy | Implementation | CPU ms | Elapsed ms | Peak RSS MiB |','|---|---|---|---|---:|---:|---:|']
 for a in json.loads((R/label/'summary.json').read_text()):
  x=a['medians'];mem='process_peak_held_bytes' if a['scope']=='eager' else 'peak_after_bytes'
  layout.append(f"| {a['scope']} | {a['case']} | {a['policy']} | {a['engine']} | {x['total_cpu_ns']/1e6:.3f} | {x['total_ns']/1e6:.3f} | {x[mem]/2**20:.2f} |")
 layout.append('')
(D/'layout-controls.md').write_text('# Additional setup and builder controls\n\nThese diagnostic controls retain complete native-output checks. Launcher control uses the same executable with a different argv[0]. Local-builder controls use a common launcher name for every executable. These are not final production qualifications. See the [study methods](README.md).\n\n'+'\n'.join(layout)+'\n')
body=(R/'report-body.md').read_text().replace('FINAL_HEAD',head).replace('REFERENCE_TABLE',tables['acceptance']).replace('FINAL_DECISION',(R/'final-decision.md').read_text().strip()).replace('REVIEW_STATUS',(R/'review-status.md').read_text().strip()).replace('VALIDATION_STATUS','All 389 DataFrame tests pass separately in Release, Debug, and Release with Address Sanitizer, with zero failures or skips. The 30,720-case grammar digest matches the parent. All 2,336 final resource workers validate complete native output contracts. The standard tabular-smoke production-default run produces 190 SwiftSci and pandas responses, and its artifact audit passes.')
assert not any(k in body for k in ['FINAL_','REFERENCE_TABLE','REVIEW_STATUS','VALIDATION_STATUS'])
(D/'README.md').write_text(body)
files={str(p.relative_to(D)):h(p) for p in D.rglob('*') if p.is_file() and p.name!='artifact-sha256.json'}
(D/'artifact-sha256.json').write_text(json.dumps(files,indent=2)+'\n')
for p in D.rglob('*.md'):
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):assert (p.parent/target).exists(),(p,target)
assert all(h(D/p)==sha for p,sha in files.items())
print(D,len(files),'verified artifacts',flush=True)
