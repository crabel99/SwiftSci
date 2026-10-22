from pathlib import Path
import gzip,hashlib,json,shutil,subprocess,tarfile
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');N=Path('/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018')
assert subprocess.check_output(['git','branch','--show-current'],cwd=N,text=True).strip()=='codex/engineering-notes'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=N)
assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
D=N/'Documentation/EngineeringNotes/benchmarks/2026-10-22-csv-count-row-events';D.mkdir(parents=True,exist_ok=False)
for p in R.glob('*.py'):shutil.copy2(p,D/p.name)
for name in ['ResourceProbe.swift','StreamProbe.swift','GrammarProbe.swift','variants.json','repro.json','minimization.json','pilot.json','adapter-pilot.json','final-null-measurement.json','final-null-summary.json','finish-status.json','grammar-result.json','gate-verdict.json','standardized-run.log','standardized-audit.log','null.log','eager.log','stream.log','reviews.md','standard-worker-build-result.json','CountParity.swift','CountParity-pilot.swift','count-parity-current.json','count-parity-count.json','count-parity-before.json','count-parity-production.json']:
 if (R/name).is_file():shutil.copy2(R/name,D/name)
for p in [*R.glob('row-events-*-summary.json'),*R.glob('row-events-*-command.json')]:shutil.copy2(p,D/p.name)
for name in ['final-measurement','final-stream-measurement','final-stream-preflight']:
 out=D/name;out.mkdir()
 for p in (R/name).glob('*.json*'):shutil.copy2(p,out/p.name)
for label in json.loads((R/'variants.json').read_text()):
 out=D/'build-receipts'/label;out.mkdir(parents=True)
 for name in ['build.json','module-signature.json','StreamProbe.build.json','GrammarProbe.build.json']:
  if (R/'build'/label/name).is_file():shutil.copy2(R/'build'/label/name,out/name)
for label,root in [('original',Path('/private/tmp/swiftsci-csv-cpu-profile-20261021/build/indexed')),('parent',Path('/private/tmp/swiftsci-csv-cell-profile-20261021/build/production'))]:
 out=D/'build-receipts'/label;out.mkdir(parents=True)
 for name in ['build.json','StreamProbe.build.json']:
  if (root/name).exists():shutil.copy2(root/name,out/name)
original_link=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021/aux/indexed/StreamProbe.build.json')
shutil.copy2(original_link,D/'build-receipts/original/StreamProbe.build.json')
shutil.copy2(R/'standard-worker/SwiftSciBenchmarkWorker.build.json',D/'standard-worker.build.json')
with tarfile.open(D/'standardized-artifacts.tar.gz','w:gz') as archive:
 for p in sorted((R/'standardized').glob('*')):
  if p.is_file():archive.add(p,arcname=p.name)
with tarfile.open(D/'diagnostic-inputs-and-trials.tar.gz','w:gz') as archive:
 for p in sorted(R.glob('*.csv')):archive.add(p,arcname='inputs/'+p.name)
 for p in sorted(R.glob('*.json')):
  if p.stem.startswith(('numeric-','nullable-','date-')):archive.add(p,arcname='inputs/'+p.name)
 for label in ['count','batch','view']:
  for p in sorted((R/(label+'-trial')/'Sources/SwiftDataFrame').rglob('*.swift')):archive.add(p,arcname='trial-sources/'+label+'/'+str(p.relative_to(R/(label+'-trial'))))
for p in (R/'inputs').glob('*.json'):
 out=D/'input-contracts';out.mkdir(exist_ok=True);shutil.copy2(p,out/p.name)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()
patch=subprocess.check_output(['git','diff','5375f261c28c5cb1ee94f6c0892ba6d830e4312a...HEAD'],cwd=S)
with gzip.open(D/'source-change.patch.gz','wb') as f:f.write(patch)
tables={}
for name in ['final-measurement','final-stream-measurement']:
 report=json.loads((R/name/'summary.json').read_text());table=['| Input and mode | Original CPU ms | Parent CPU ms | New CPU ms | CPU vs parent | CPU vs original | Peak RSS MiB, original → new | Elapsed ms, original → parent → new |','|---|---:|---:|---:|---:|---:|---:|---:|']
 for a in report['medians']:
  if a['engine']!='production':continue
  refs={r['engine']:r for r in report['medians'] if r['case']==a['case'] and r.get('mode')==a.get('mode')};b=refs['indexed'];c=refs['before'];peak='process_peak_held_bytes' if name=='final-measurement' else 'peak_after_bytes'
  table.append(f"| {a['case']} {a.get('mode','known')} | {b['total_cpu_ns']/1e6:.3f} | {c['total_cpu_ns']/1e6:.3f} | {a['total_cpu_ns']/1e6:.3f} | {(a['total_cpu_ns']/c['total_cpu_ns']-1)*100:+.1f}% | {(a['total_cpu_ns']/b['total_cpu_ns']-1)*100:+.1f}% | {b[peak]/2**20:.2f} → {a[peak]/2**20:.2f} | {b['total_ns']/1e6:.3f} → {c['total_ns']/1e6:.3f} → {a['total_ns']/1e6:.3f} |")
 tables[name]='\n'.join(table)
null=json.loads((R/'final-null-summary.json').read_text())['medians'];nt=['| Null fraction and mode | Original CPU ms | Parent CPU ms | New CPU ms | CPU vs parent |','|---|---:|---:|---:|---:|']
for a in null:
 if a['engine']!='production':continue
 refs={d['engine']:d for d in null if d['null_percent']==a['null_percent'] and d['mode']==a['mode']};b=refs['original'];c=refs['before'];nt.append(f"| {a['null_percent']}% {a['mode']} | {b['total_cpu_ns']/1e6:.3f} | {c['total_cpu_ns']/1e6:.3f} | {a['total_cpu_ns']/1e6:.3f} | {(a['total_cpu_ns']/c['total_cpu_ns']-1)*100:+.1f}% |")
for label in ['row-events-release','row-events-debug','row-events-asan']:
 x=json.loads((R/(label+'-summary.json')).read_text());assert x['passedTests']==383 and x['failedTests']==0 and x['skippedTests']==0
assert len(list((R/'standardized').glob('*.response.json')))==190
verdict=json.loads((R/'gate-verdict.json').read_text())
assert not verdict['new_cpu_regressions_above_review_limit'],verdict['new_cpu_regressions_above_review_limit']
body=(R/'report-body.md').read_text().replace('HEAD_COMMIT',head).replace('EAGER_TABLE',tables['final-measurement']).replace('STREAM_TABLE',tables['final-stream-measurement']).replace('NULL_TABLE','\n'.join(nt))
(D/'README.md').write_text(body)
files={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in D.rglob('*') if p.is_file() and p.name!='artifact-sha256.json'}
(D/'artifact-sha256.json').write_text(json.dumps(files,indent=2)+'\n');print(D)
