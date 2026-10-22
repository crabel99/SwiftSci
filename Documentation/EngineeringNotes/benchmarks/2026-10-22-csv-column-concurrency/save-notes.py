from pathlib import Path
import gzip,hashlib,json,shutil,subprocess,tarfile,difflib,re
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');B=Path('/private/tmp/swiftsci-csv-double-validation-control-20261022');N=Path('/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert subprocess.check_output(['git','branch','--show-current'],cwd=N,text=True).strip()=='codex/engineering-notes'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=N)
assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
assert all(p.get('exit_code')==0 for p in json.loads((R/'finish-status.json').read_text()))
assert not json.loads((R/'acceptance/review-flags.json').read_text())
for label in ['column-mode-release-fixed','column-mode-debug','column-mode-asan']:
 d=json.loads((R/(label+'-summary.json')).read_text());assert d['passedTests']==384 and d['failedTests']==0 and d['skippedTests']==0
 receipt=json.loads((R/(label+'-command.json')).read_text());assert all(h(S/p)==sha for p,sha in receipt['source_sha256'].items())
assert len(list((R/'standardized').glob('*.response.json')))==190
D=N/'Documentation/EngineeringNotes/benchmarks/2026-10-22-csv-column-concurrency';D.mkdir(parents=True,exist_ok=False)
for p in [*R.glob('*.py'),*R.glob('*.swift'),*R.glob('*.json'),R/'reviews.md']:
 if p.is_file() and not p.name.endswith('-progress.json'):shutil.copy2(p,D/p.name)
for p in R.glob('*.log'):
 with gzip.open(D/(p.name+'.gz'),'wb') as f:f.write(p.read_bytes())
for folder in ['acceptance','mode-controls']:
 out=D/folder;out.mkdir()
 for p in (R/folder).iterdir():
  if p.is_file():shutil.copy2(p,out/p.name)
for label in json.loads((R/'variants.json').read_text()):
 out=D/'build-receipts'/label;out.mkdir(parents=True)
 for name in ['build.json','module-signature.json','GrammarProbe.build.json','StreamProbe.build.json']:
  p=R/'build'/label/name
  if p.is_file():shutil.copy2(p,out/p.name)
for label,root in [('original',Path('/private/tmp/swiftsci-csv-cpu-profile-20261021/build/indexed')),('parent',Path('/private/tmp/swiftsci-csv-plan-profile-20261022/build/production'))]:
 out=D/'build-receipts'/label;out.mkdir(parents=True)
 for name in ['build.json','module-signature.json','StreamProbe.build.json']:
  if (root/name).exists():shutil.copy2(root/name,out/name)
shutil.copy2(R/'standard-worker/SwiftSciBenchmarkWorker.build.json',D/'standard-worker.build.json')
with tarfile.open(D/'standardized-artifacts.tar.gz','w:gz') as archive:
 for p in sorted((R/'standardized').iterdir()):
  if p.is_file():archive.add(p,arcname=p.name)
patchdir=R/'trial-patches';patchdir.mkdir()
for label in ['parity','paired','strided','quartet','serial']:
 diff=[]
 for p in sorted((R/(label+'-trial')/'Sources/SwiftDataFrame').rglob('*.swift')):
  rel=p.relative_to(R/(label+'-trial'));old=B/rel
  if old.read_bytes()!=p.read_bytes():diff.extend(difflib.unified_diff(old.read_text().splitlines(keepends=True),p.read_text().splitlines(keepends=True),fromfile='a/'+str(rel),tofile='b/'+str(rel)))
 (patchdir/(label+'.patch')).write_text(''.join(diff))
with tarfile.open(D/'experiments.tar.gz','w:gz') as archive:
 for folder in ['width-inputs','trial-patches']:
  archive.add(R/folder,arcname=folder)
 archive.add(B/'Sources/SwiftDataFrame',arcname='parent-sources/SwiftDataFrame')
 for name in ['SystemsCSVParser.swift','CSVEagerReader.swift','CSVCPUProfile.swift']:
  p=R/'instrumented/Sources/SwiftDataFrame/IO'/name
  if p.is_file():archive.add(p,arcname='instrumented-sources/'+name)
plan=json.loads((R/'acceptance/plan.json').read_text());out=D/'input-contracts';out.mkdir()
for name,inp in plan['inputs'].items():shutil.copy2(Path(inp['path']),out/(name+'.json'))
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()
with gzip.open(D/'source-change.patch.gz','wb') as f:f.write(subprocess.check_output(['git','diff','c8c56d1eb25f51afa27c452c6f656cb79dec73a6...HEAD'],cwd=S))
summary=json.loads((R/'acceptance/summary.json').read_text());table=['| Read, input, schema | Original CPU ms | Parent CPU ms | Parallel CPU ms | Serial CPU ms | Serial CPU vs parallel | Elapsed ms, parallel → serial | Peak RSS MiB, parallel → serial |','|---|---:|---:|---:|---:|---:|---:|---:|']
for a in summary:
 if a['engine']!='serial':continue
 refs={d['engine']:d['medians'] for d in summary if (d['scope'],d['case'],d['mode'])==(a['scope'],a['case'],a['mode'])};v=a['medians'];p=refs['parallel'];mem='process_peak_held_bytes' if a['scope']=='eager' else 'peak_after_bytes'
 table.append(f"| {a['scope']} {a['case']} {a['mode']} | {refs['original']['total_cpu_ns']/1e6:.3f} | {refs['parent']['total_cpu_ns']/1e6:.3f} | {p['total_cpu_ns']/1e6:.3f} | {v['total_cpu_ns']/1e6:.3f} | {(v['total_cpu_ns']/p['total_cpu_ns']-1)*100:+.1f}% | {p['total_ns']/1e6:.3f} → {v['total_ns']/1e6:.3f} | {p[mem]/2**20:.2f} → {v[mem]/2**20:.2f} |")
controls=json.loads((R/'mode-controls/summary.json').read_text());flags=[]
for a in controls:
 if a['engine']!='parallel':continue
 b=next(b for b in controls if b['case']==a['case'] and b['engine']=='parent')
 if a['medians']['total_cpu_ns']>b['medians']['total_cpu_ns']*1.10:flags.append(dict(new=a,parent=b))
(R/'control-review-flags.json').write_text(json.dumps(flags,indent=2)+'\n');shutil.copy2(R/'control-review-flags.json',D/'control-review-flags.json')
assert not flags,flags
status='No parallel-default CPU increases exceeded the 10% review threshold in either final matrix. No reference-case peak-RSS increase exceeded 5% plus8MiB. These are review limits, not proof that smaller regressions are zero. The serial prototype comparison checks that the public selector retains the direct-loop result; it does not prove serial is optimal for every input.'
body=(R/'report-body.md').read_text().replace('HEAD_COMMIT',head).replace('REFERENCE_TABLE','\n'.join(table)).replace('REVIEW_STATUS',status)
(D/'README.md').write_text(body)
for p in [*D.glob('*.json'),*D.glob('*/*.jsonl')]:
 if p.stat().st_size>256*1024:
  content=p.read_bytes()
  with gzip.open(str(p)+'.gz','wb') as out:out.write(content)
  assert gzip.decompress(Path(str(p)+'.gz').read_bytes())==content
  p.unlink()
files={str(p.relative_to(D)):h(p) for p in D.rglob('*') if p.is_file() and p.name!='artifact-sha256.json'}
(D/'artifact-sha256.json').write_text(json.dumps(files,indent=2)+'\n')
for target in re.findall(r'\]\(([^)]+)\)',body):assert (D/target).exists(),target
assert all(h(D/p)==sha for p,sha in files.items())
print(D, len(files),'verified artifacts',flush=True)
