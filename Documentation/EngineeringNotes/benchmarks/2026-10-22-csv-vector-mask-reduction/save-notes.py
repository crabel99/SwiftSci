from pathlib import Path
import gzip,hashlib,json,shutil,subprocess,tarfile,difflib,re
R=Path(__file__).resolve().parent
S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021')
B=Path('/private/tmp/swiftsci-csv-column-concurrency-control-20261022')
P=Path('/private/tmp/swiftsci-csv-wide-profile-20261022')
Q=Path('/private/tmp/swiftsci-csv-plan-profile-20261022')
E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021')
N=Path('/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
head='46a9b9bf951918cd2eb281dadf554efb30c7b0a0'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()==head
assert subprocess.check_output(['git','branch','--show-current'],cwd=N,text=True).strip()=='codex/engineering-notes'
for root in [S,B,N]:assert not subprocess.check_output(['git','status','--porcelain'],cwd=root)
phases=json.loads((R/'finish-status.json').read_text())
assert len(phases)==5 and all(p.get('exit_code')==0 for p in phases)
for label in ['vector-mask-release','vector-mask-debug','vector-mask-asan']:
 d=json.loads((R/(label+'-summary.json')).read_text());assert d['passedTests']==385 and d['failedTests']==0 and d['skippedTests']==0
 rec=json.loads((R/(label+'-command.json')).read_text());assert all(h(S/p)==sha for p,sha in rec['source_sha256'].items())
assert len(list((R/'standardized').glob('*.response.json')))==190
assert json.loads((R/'grammar-result.json').read_text())==json.loads((P/'grammar-result.json').read_text())
summary=json.loads((R/'acceptance/summary.json').read_text())
controls=json.loads((R/'mode-controls/summary.json').read_text())
assert sum(1 for _ in (R/'acceptance/workers.jsonl').open())==800
assert sum(1 for _ in (R/'mode-controls/workers.jsonl').open())==544
flags={scope:json.loads((R/scope/'review-flags.json').read_text()) for scope in ['acceptance','mode-controls']}
assert not any(flags.values()),flags
D=N/'Documentation/EngineeringNotes/benchmarks/2026-10-22-csv-vector-mask-reduction'
D.mkdir(parents=True,exist_ok=False)
for p in [*R.glob('*.py'),*R.glob('*.swift'),*R.glob('*.json'),R/'reviews.md']:
 if p.is_file():shutil.copy2(p,D/p.name)
for pattern in ['*.log','*.sample.txt','*disassembly*.txt','*.stderr']:
 for p in R.glob(pattern):
  with gzip.open(D/(p.name+'.gz'),'wb') as f:f.write(p.read_bytes())
for folder in ['acceptance','mode-controls']:
 out=D/folder;out.mkdir()
 for p in (R/folder).iterdir():
  if not p.is_file():continue
  if p.suffix=='.jsonl':
   with gzip.open(out/(p.name+'.gz'),'wb') as f:f.write(p.read_bytes())
  else:shutil.copy2(p,out/p.name)
for label,root in [('original',E/'build/indexed'),('parent',P/'build/production'),*[(label,R/'build'/label) for label in json.loads((R/'variants.json').read_text())]]:
 out=D/'build-receipts'/label;out.mkdir(parents=True)
 for name in ['build.json','module-signature.json','GrammarProbe.build.json','StreamProbe.build.json']:
  if (root/name).is_file():shutil.copy2(root/name,out/name)
shutil.copy2(R/'standard-worker/SwiftSciBenchmarkWorker.build.json',D/'standard-worker.build.json')
shutil.copy2(P/'grammar-result.json',D/'parent-grammar-result.json')
with tarfile.open(D/'standardized-artifacts.tar.gz','w:gz') as archive:
 for p in sorted((R/'standardized').iterdir()):
  if p.is_file():archive.add(p,arcname=p.name)
patches=R/'trial-patches';patches.mkdir(exist_ok=False)
for label in ['apple-full','apple-wide']:
 diff=[]
 for p in sorted((R/(label+'-trial')/'Sources/SwiftDataFrame').rglob('*.swift')):
  rel=p.relative_to(R/(label+'-trial'));old=B/rel
  if old.read_bytes()!=p.read_bytes():diff.extend(difflib.unified_diff(old.read_text().splitlines(keepends=True),p.read_text().splitlines(keepends=True),fromfile='a/'+str(rel),tofile='b/'+str(rel)))
 (patches/(label+'.patch')).write_text(''.join(diff))
with tarfile.open(D/'experiments.tar.gz','w:gz') as archive:
 archive.add(patches,arcname='trial-patches')
 archive.add(B/'Sources/SwiftDataFrame',arcname='parent-sources/SwiftDataFrame')
 archive.add(P/'width-inputs',arcname='width-inputs')
 for n in [0,50,90]:
  for suffix in ['.csv','.json']:
   p=Q/('nullable-'+str(n)+suffix)
   if p.is_file():archive.add(p,arcname='nullable-inputs/'+p.name)
 plan=json.loads((R/'acceptance/plan.json').read_text())
 for case,inp in plan['inputs'].items():archive.add(inp['path'],arcname='reference-input-contracts/'+case+'.json')
with gzip.open(D/'source-change.patch.gz','wb') as f:f.write(subprocess.check_output(['git','diff','9c067c6c5116d78c0849073acea7fb150404efab...HEAD'],cwd=S))
reference=['| Read, input, schema | Conversion policy | CPU ms, parent → final | CPU change | Elapsed ms, parent → final | Peak RSS MiB, parent → final |','|---|---|---:|---:|---:|---:|']
changes=[]
for a in summary:
 if a['engine'] not in ['parallel','serial']:continue
 b=next(b for b in summary if b['engine']=='parent-'+a['engine'] and (b['scope'],b['case'],b['mode'])==(a['scope'],a['case'],a['mode']))
 v=a['medians'];p=b['medians'];delta=(v['total_cpu_ns']/p['total_cpu_ns']-1)*100
 changes.append(dict(scope=a['scope'],case=a['case'],mode=a['mode'],policy=a['engine'],cpu_change_percent=delta))
 mem='process_peak_held_bytes' if a['scope']=='eager' else 'peak_after_bytes'
 reference.append(f"| {a['scope']} {a['case']} {a['mode']} | {a['engine']} | {p['total_cpu_ns']/1e6:.3f} → {v['total_cpu_ns']/1e6:.3f} | {delta:+.1f}% | {p['total_ns']/1e6:.3f} → {v['total_ns']/1e6:.3f} | {p[mem]/2**20:.2f} → {v[mem]/2**20:.2f} |")
ct=['| Input | Conversion policy | CPU ms, parent → final | CPU change | Elapsed ms, parent → final | Peak RSS MiB, parent → final |','|---|---|---:|---:|---:|---:|']
for a in controls:
 if a['engine'] not in ['parallel','serial']:continue
 b=next(b for b in controls if b['engine']=='parent-'+a['engine'] and b['case']==a['case']);v=a['medians'];p=b['medians']
 ct.append(f"| {a['case']} | {a['engine']} | {p['total_cpu_ns']/1e6:.3f} → {v['total_cpu_ns']/1e6:.3f} | {(v['total_cpu_ns']/p['total_cpu_ns']-1)*100:+.1f}% | {p['total_ns']/1e6:.3f} → {v['total_ns']/1e6:.3f} | {p['process_peak_held_bytes']/2**20:.2f} → {v['process_peak_held_bytes']/2**20:.2f} |")
(D/'cpu-changes.json').write_text(json.dumps(changes,indent=2)+'\n')
body=(R/'report-body.md').read_text().replace('REFERENCE_TABLE','\n'.join(reference)).replace('CONTROL_TABLE','\n'.join(ct))
body=body.replace('REVIEW_STATUS','No final reference or control case exceeds the 10% CPU review threshold. No peak-RSS increase exceeds 5% plus 8 MiB. Smaller increases remain visible in the tables and raw samples.')
body=body.replace('FINAL_DECISION',(R/'final-decision.md').read_text().strip())
(D/'README.md').write_text(body)
for p in D.glob('*.json'):
 if p.stat().st_size>256*1024:
  data=p.read_bytes()
  with gzip.open(str(p)+'.gz','wb') as f:f.write(data)
  assert gzip.decompress(Path(str(p)+'.gz').read_bytes())==data
  p.unlink()
files={str(p.relative_to(D)):h(p) for p in D.rglob('*') if p.is_file() and p.name!='artifact-sha256.json'}
(D/'artifact-sha256.json').write_text(json.dumps(files,indent=2)+'\n')
for target in re.findall(r'\]\(([^)]+)\)',body):assert (D/target).exists(),target
assert all(h(D/p)==sha for p,sha in files.items())
print(D,len(files),'verified artifacts',flush=True)
