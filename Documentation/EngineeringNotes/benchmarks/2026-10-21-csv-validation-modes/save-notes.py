from pathlib import Path
import gzip,hashlib,json,shutil,subprocess,tarfile,statistics as st
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');N=Path('/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018')
assert subprocess.check_output(['git','branch','--show-current'],cwd=N,text=True).strip()=='codex/engineering-notes'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
D=N/'Documentation/EngineeringNotes/benchmarks/2026-10-21-csv-validation-modes';D.mkdir(parents=True,exist_ok=True)
for p in R.glob('*.py'):shutil.copy2(p,D/p.name)
for name in ['ResourceProbe.swift','StreamProbe.swift','GrammarProbe.swift','SamplingMatched.swift','variants.json','repro.json','minimization.json','stage-profile.json','pilot.json','result-pilot.json','optional-pilot.json','explicit-pilot.json','final-null-measurement.json','final-null-summary.json','optional-null-retest.json','optional-null-retest.log','finish-status.json','grammar-result.json','gate-verdict.json','standardized-run.log','standardized-audit.log','null.log','eager.log','stream.log','reviews.md','matched-sample-before-receipt.json','matched-sample-after-receipt.json','matched-sample-before-build.json','matched-sample-after-build.json','standard-worker-build-result.json']:
 if (R/name).is_file():shutil.copy2(R/name,D/name)
for label in ['before','after']:
 raw=R/('matched-sample-'+label+'.txt')
 with gzip.open(D/(raw.name+'.gz'),'wb') as out:out.write(raw.read_bytes())
 (D/raw.name).unlink(missing_ok=True)
for p in [*R.glob('validation-modes-*-summary.json'),*R.glob('validation-modes-*-command.json')]:shutil.copy2(p,D/p.name)
for name in ['final-measurement','final-stream-measurement']:
 out=D/name;out.mkdir(exist_ok=True)
 for p in (R/name).glob('*.json*'):shutil.copy2(p,out/p.name)
for label in json.loads((R/'variants.json').read_text()):
 out=D/'build-receipts'/label;out.mkdir(parents=True,exist_ok=True)
 for name in ['build.json','module-signature.json','stream-build.json','StreamProbe.build.json','GrammarProbe.build.json']:
  if (R/'build'/label/name).is_file():shutil.copy2(R/'build'/label/name,out/name)
shutil.copy2(R/'standard-worker/SwiftSciBenchmarkWorker.build.json',D/'standard-worker.build.json')
with tarfile.open(D/'standardized-artifacts.tar.gz','w:gz') as archive:
 for p in sorted((R/'standardized').glob('*')):
  if p.is_file():archive.add(p,arcname=p.name)
with tarfile.open(D/'diagnostic-inputs-and-trials.tar.gz','w:gz') as archive:
 for p in sorted(R.glob('*.csv')):archive.add(p,arcname='inputs/'+p.name)
 for p in sorted(R.glob('date-*.json')):archive.add(p,arcname='inputs/'+p.name)
 for p in sorted(R.glob('nullable-*.json')):archive.add(p,arcname='inputs/'+p.name)
 for label in ['inline','local','result','optional','explicit']:
  p=Path(json.loads((R/'variants.json').read_text())[label]['path'])/'Sources/SwiftDataFrame/IO/CSVColumnConversion.swift';archive.add(p,arcname='trial-sources/'+label+'/CSVColumnConversion.swift')
for p in (R/'inputs').glob('*.json'):
 out=D/'input-contracts';out.mkdir(exist_ok=True);shutil.copy2(p,out/p.name)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()
patch=subprocess.check_output(['git','diff','297ebd36ef979cf1a5dfafa3f419c052165f2d1e...HEAD'],cwd=S)
with gzip.open(D/'source-change.patch.gz','wb') as f:f.write(patch)
reports={name:json.loads((R/name/'summary.json').read_text()) for name in ['final-measurement','final-stream-measurement']}
tables={}
for name,report in reports.items():
 table=['| Input and mode | Original CPU ms | Prior prototype CPU ms | New CPU ms | CPU vs prior | CPU vs original | Peak RSS MiB, original → new | Elapsed ms, original → new |','|---|---:|---:|---:|---:|---:|---:|---:|']
 for a in report['medians']:
  if a['engine']!='production':continue
  refs={r['engine']:r for r in report['medians'] if r['case']==a['case'] and r.get('mode')==a.get('mode')};b=refs['indexed'];c=refs['before'];peak='process_peak_held_bytes' if name=='final-measurement' else 'peak_after_bytes'
  table.append(f"| {a['case']} {a.get('mode','known')} | {b['total_cpu_ns']/1e6:.3f} | {c['total_cpu_ns']/1e6:.3f} | {a['total_cpu_ns']/1e6:.3f} | {(a['total_cpu_ns']/c['total_cpu_ns']-1)*100:+.1f}% | {(a['total_cpu_ns']/b['total_cpu_ns']-1)*100:+.1f}% | {b[peak]/2**20:.2f} → {a[peak]/2**20:.2f} | {b['total_ns']/1e6:.3f} → {a['total_ns']/1e6:.3f} |")
 tables[name]='\n'.join(table)
null=json.loads((R/'final-null-summary.json').read_text())['medians'];nt=['| Null fraction and mode | Original CPU ms | Prior CPU ms | New CPU ms | New vs prior |','|---|---:|---:|---:|---:|']
for a in null:
 if a['engine']!='production':continue
 refs={d['engine']:d for d in null if d['null_percent']==a['null_percent'] and d['mode']==a['mode']};b=refs['original'];c=refs['before'];nt.append(f"| {a['null_percent']}% {a['mode']} | {b['total_cpu_ns']/1e6:.3f} | {c['total_cpu_ns']/1e6:.3f} | {a['total_cpu_ns']/1e6:.3f} | {(a['total_cpu_ns']/c['total_cpu_ns']-1)*100:+.1f}% |")
neg=json.loads((R/'optional-null-retest.json').read_text())['records'];m={e:st.median(d['result']['samples'][0]['total_cpu_ns'] for d in neg if d['engine']==e and d['null_percent']==90 and d['mode']=='infer') for e in ['before','optional']};penalty=(m['optional']/m['before']-1)*100
for label in ['validation-modes-release','validation-modes-debug','validation-modes-asan']:
 x=json.loads((R/(label+'-summary.json')).read_text());assert x['passedTests']==382 and x['failedTests']==0 and x['skippedTests']==0
assert len(list((R/'standardized').glob('*.response.json')))==190
verdict=json.loads((R/'gate-verdict.json').read_text());assert not verdict['new_cpu_regressions_above_review_limit']
text=f'''# CSV validation modes and the Date conversion regression

The local change recovers the Date conversion regression while preserving the bounded eager reader's memory savings. It does not finish the whole CSV prototype. Wider eager input and some numeric streaming cases still use more CPU than the original reader.

The candidate is `{head}` on `codex/csv-validation-modes`, based on `297ebd36ef979cf1a5dfafa3f419c052165f2d1e`. That prior prototype is the [count-only and fallback experiment](../2026-10-21-csv-cpu-discovery/README.md). The original control remains `dba26e1562503e1594194250d914327830d8f58d`. All changes remain local.

## Why two decoding contracts

An explicit schema maps both missing and invalid fields to nil. Inference must distinguish them because an invalid token rejects a candidate. The previous shared loop transported that distinction for every field, including explicit schemas.

The new loop chooses the validation contract once per batch. Inference keeps the existing classified result. Explicit schemas request an optional value. Most decoders derive that optional from their classified result. Date returns the parser's optional directly, avoiding an additional generic result tag. Neither Date parsing nor numeric arithmetic changes.

The change adds 31 lines and removes 3 in one private implementation file. It adds no public API, deployment requirement, cache, allocation policy, worker pool, or core-affinity rule. Native optional output storage and existing joined workers remain unchanged.

## Evidence and rejected trials

The frozen-binary reproduction was red for a two-column date stream and wider eager Beijing input. Reductions to one Date column retained the regression. Boundary measurements showed single-column conversion at about 5.36 ms of process CPU versus 4.06 ms originally, while framing was slightly cheaper. This ruled against framing as the primary cause of that Date regression.

Sampling showed extra `CSVDecodedValue` tag routines in the prior explicit-Date path. A matched final sample uses the same null policy and input bytes on both heads. Those routines no longer appear in its new explicit-Date samples. Sampling supports the diagnosis; the paired whole-operation measurements below establish the benefit. Sample counts are not elapsed-time ratios or energy measurements.

Forced inlining and moving the builder into a local variable did not give consistent gains. Separating the value and invalid flag into another generic result structure also did not help. Removing classified results for every decoder improved Date work but made 90%-missing inferred numeric input {penalty:.1f}% more CPU-expensive in the retained retest. That trial was rejected. The final mode split keeps the classified inference path and avoids that repeated-null-classification penalty.

Two early null pilots reused an output filename. Their superseded raw records are unavailable. The optional-only alternative was rerun into a distinct retained record and reproduced the regression. The final production null comparison is retained separately. No final acceptance statement depends on the overwritten records. The retained controllers now use distinct destinations and refuse to overwrite prior measurements. Executed controller snapshots preserve the commands that produced the evidence.

## Final eager comparison

{tables['final-measurement']}

## Final streaming comparison

{tables['final-stream-measurement']}

Date-only streaming is now about 4% below the original reader's CPU work, and the two-column date stream is about level with it. The full explicit-date eager read is about 13% below the original's CPU work and retains peak RSS near 422 MiB instead of 720 MiB. Its elapsed time remains substantially higher than the original. The table keeps that cost visible.

The wider eager Beijing case remains about 13% above the original's CPU work. Power-data streaming also remains above it. No weighted average or Date-specific win clears those remaining blockers.

## Null-heavy comparison

{chr(10).join(nt)}

These controls contain 100000 rows with native Int64 and Double columns and deterministic 0%, 50%, and 90% null distributions. They check inferred and explicit schemas without changing selected values, types, null positions, or row order between implementations. The new implementation has no CPU regression above the 10% review limit versus its parent across the final eager, streaming, and null controls. Several inherited costs remain above the original reader.

## Validation and measurement boundaries

All 382 SwiftDataFrame tests pass in Release, Debug, and Address Sanitizer, with no failures or skips. Test-source and implementation hashes match the final head. The parser differential still matches all 30720 deterministic raw-byte fixtures. No parser source changed in this commit.

The standard production-default `tabular-smoke` run passes all 190 SwiftSci and pandas samples, and its certificate audit passes. This validates the declared tabular cases. It does not establish full numerical certification or cover every MLX-dependent module. The independent [standards and specification reviews](reviews.md) found no actionable defects.

Final resource evidence contains 162 eager workers, 108 streaming workers, and 90 null-control workers, plus 18 streaming correctness preflights. The three implementations run in six balanced-order rounds. Native types, values, null positions, and output order are checked. Validation runs outside measured CPU and elapsed intervals, with peak memory captured before validation. No builds or tests from this task run concurrently with these accepted comparisons. AC power and native CPU parallelism remain the policy. Input pages are warm, and no outliers are trimmed.

CPU is process user plus system time. RSS includes resident mappings and allocator behavior. Neither is an energy reading or an allocation count. No GPU, NPU, cache-capacity, or SRAM-efficiency conclusion follows from these CPU experiments.

## Reproduction and next step

Plans and raw worker records accompany the tables. Build receipts preserve commands, source hashes, binary hashes, and dependency identities. The raw standard suite is in `standardized-artifacts.tar.gz`. Diagnostic inputs and trial source files are in `diagnostic-inputs-and-trials.tar.gz`. The retained original and parent modules remain under `/private/tmp`, with the parent source restored at `/private/tmp/swiftsci-csv-count-only-control-20261021`. Scripts use local paths and require equivalent restored checkouts before reuse. Trial reconstruction uses the restored parent source. Final validation uses the candidate head. Choose a fresh output directory for another run.

Keep the focused validation-mode commit. Do not promote the broader bounded reader to the default or open its implementation PR yet. Next isolate numeric and String conversion on the wider reference data, separating per-cell work from per-batch scheduling. Preserve the Date recovery, original-token fallback, and peak-memory reduction while testing that next change.

This record belongs to `codex/engineering-notes` and must stay out of implementation PRs.
'''
(D/'README.md').write_text(text)
files={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in D.rglob('*') if p.is_file() and p.name!='artifact-sha256.json'};(D/'artifact-sha256.json').write_text(json.dumps(files,indent=2)+'\n');print(D)
