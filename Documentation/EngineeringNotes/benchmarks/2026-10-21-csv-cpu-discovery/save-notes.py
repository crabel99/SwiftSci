from pathlib import Path
import gzip, hashlib, json, shutil, subprocess
R=Path(__file__).resolve().parent
S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021')
N=Path('/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018')
assert subprocess.check_output(['git','branch','--show-current'],cwd=N,text=True).strip()=='codex/engineering-notes'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
D=N/'Documentation/EngineeringNotes/benchmarks/2026-10-21-csv-cpu-discovery';D.mkdir(parents=True,exist_ok=True)
for name in ['ResourceProbe.swift','StreamProbe.swift','GrammarProbe.swift','build.py','variants.json','reproduce.py','minimize.py','minimization.json','stage-profile.json','stage-profile-sink.json','grammar-differential.json','gate-verdict.json','count-tests.py','count-only.py','output-mode.py','prune-candidates.py','rejection-tests.py','run-comparison.py','run-output-pilot.py','run-final.py','run-final-stream.py','verify.py','build-standard-worker.py','link-aux.py','save-notes.py','summarize.py','instrument.py','profile.py','instrument-sink.py','profile-sink.py','standard-worker-build-result.json']:
 if (R/name).is_file():shutil.copy2(R/name,D/name)
for name in ['repro-original','count-only-measurement','output-mode-pilot','final-measurement','final-stream-measurement','final-stream-preflight']:
 src=R/name;dst=D/name;dst.mkdir(exist_ok=True)
 for p in src.glob('*'):
  if p.is_file() and p.suffix in {'.json','.jsonl'}:shutil.copy2(p,dst/p.name)
for p in R.glob('*-summary.json'):shutil.copy2(p,D/p.name)
for p in R.glob('*-command.json'):shutil.copy2(p,D/p.name)
for p in R.glob('*.patch'):
 with gzip.open(D/(p.name+'.gz'),'wb') as f:f.write(p.read_bytes())
for label in ['indexed','counted','count-only','sink-trial','sink-final-snapshot','output-mode-pilot','profile','profile-sink']:
 src=R/'build'/label;dst=D/'build-receipts'/label;dst.mkdir(parents=True,exist_ok=True)
 for name in ['build.json','module-signature.json']:
  if (src/name).is_file():shutil.copy2(src/name,dst/name)
for label in ['indexed','counted','count-only']:
 dst=D/'build-receipts'/label
 for p in (R/'aux'/label).glob('*.build.json'):shutil.copy2(p,dst/p.name)
for p in (R/'inputs').glob('*.json'):
 dst=D/'input-contracts';dst.mkdir(exist_ok=True);shutil.copy2(p,dst/p.name)
for name in ['standardized-run.log','standardized-audit.log']:
 shutil.copy2(R/name,D/name)
shutil.copy2(R/'standard-worker/SwiftSciBenchmarkWorker.build.json',D/'standard-worker.build.json')
for p in (R/'standardized').rglob('*'):
 if p.is_file() and p.suffix in {'.json','.jsonl','.csv','.f64'}:
  target=D/'standardized'/p.relative_to(R/'standardized');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()
summary=json.loads((R/'final-measurement/summary.json').read_text());rows=summary['medians']
table=['| Input and contract | Original CPU ms | Previous prototype CPU ms | New CPU ms | New vs original | Peak RSS MiB, original → new | Elapsed ms, original → new |','|---|---:|---:|---:|---:|---:|---:|']
for a in rows:
 if a['engine']!='count-only':continue
 refs={r['engine']:r for r in rows if (r['case'],r['mode'])==(a['case'],a['mode'])};b=refs['indexed'];c=refs['counted']
 table.append(f"| {a['case']} {a['mode']} | {b['total_cpu_ns']/1e6:.3f} | {c['total_cpu_ns']/1e6:.3f} | {a['total_cpu_ns']/1e6:.3f} | {(a['total_cpu_ns']/b['total_cpu_ns']-1)*100:+.1f}% | {b['process_peak_held_bytes']/2**20:.2f} → {a['process_peak_held_bytes']/2**20:.2f} | {b['total_ns']/1e6:.3f} → {a['total_ns']/1e6:.3f} |")
stream=json.loads((R/'final-stream-measurement/summary.json').read_text());streamtable=['| Input | Original CPU ms | Previous CPU ms | New CPU ms | New vs previous | New vs original |','|---|---:|---:|---:|---:|---:|']
for a in stream['medians']:
 if a['engine']!='count-only':continue
 refs={r['engine']:r for r in stream['medians'] if r['case']==a['case']};b=refs['indexed'];c=refs['counted']
 streamtable.append(f"| {a['case']} | {b['total_cpu_ns']/1e6:.3f} | {c['total_cpu_ns']/1e6:.3f} | {a['total_cpu_ns']/1e6:.3f} | {(a['total_cpu_ns']/c['total_cpu_ns']-1)*100:+.1f}% | {(a['total_cpu_ns']/b['total_cpu_ns']-1)*100:+.1f}% |")
tests=[]
for label in ['final-pruned-release','final-pruned-debug','final-pruned-asan']:
 a=json.loads((R/(label+'-summary.json')).read_text());assert a['failedTests']==0 and a['skippedTests']==0 and a['passedTests']==382
 tests.append(f"- {label}: {a['passedTests']}/{a['totalTestCount']} passed, no failures or skips.")
text=f'''# CSV count-only discovery and rejected-token pruning

The local prototype removes most of the late-type fallback penalty and keeps the earlier large-file memory reduction. It still fails the gate for replacing the default reader. Beijing eager CPU is 17.5% above the original reader, and the broader branch has streaming CPU regressions that predate this change. Do not hide those costs in an average.

## Source and implementation

The final local head is `{head}` on `codex/csv-count-only-scan`. It builds on `33bd8ce78588d8027443e421ea918b9c4a704ab9`, the [exact-sizing prototype](../2026-10-21-csv-eager-batches/README.md). The original control is `dba26e1562503e1594194250d914327830d8f58d`. Each measurement plan records exact source and binary identities. Nothing was pushed or submitted.

The count-only specialization uses the existing framing state machine. Its compile-time output mode removes field and row-coordinate storage from counting. Normal indexing keeps local arrays. This avoids a second quote parser and the per-field sink mutation that regressed the first trial.

An inferred conversion now retains the offset of its first rejecting original token. Before a replay, the plan tests that token against later eligible candidates through the existing decoders. A token such as `true` already disproves Double, so replaying the entire prefix as Double cannot help. A surviving candidate still validates every original row. The plan never admits a type excluded by the original sample.

Offsets refer to the retained source. The eager reader rebases each batch's rejecting offset once. Indexed streaming uses the same pruning within its public chunk. The rejection record retains no source pointer, converted numeric text, or column-wide field index.

Public API, optional column storage, deployment target, ordered first-1000-row eligibility, explicit override invalid-to-null behavior, and streaming chunk-local inference remain unchanged. JSON retains its own caller. Record batches remain 16384 rows. That row bound is not a hard byte or memory limit.

## Diagnosis and rejected alternatives

The frozen-binary reproduction exited nonzero with late Boolean CPU 18.0% above the original. The Beijing input was 10.6% above it. Four smaller Boolean fixtures reproduced the trend around the internal eager batch boundary.

Process CPU profiling separated counting, framing, conversion, setup, and finalization. Beijing counting cost about 1.3 ms. Late Boolean framing ran 21 times because integer, Double, and Boolean each attempted seven batches. Setup and finalization were small, so builder destruction was not the main explanation.

The first generic sink trial passed correctness but increased ordinary framing cost. Its 162-worker measurement is retained in `count-only-measurement`. It is a rejected design. The compile-time output-mode pilot is in `output-mode-pilot`. It reduced large-file work modestly but did not resolve fallback. The final measurement includes rejected-token pruning.

The initial count-test compile failure came from a throwing expression inside a test macro. The corrected test binds the typed result before its assertion. It was a test construction repair, not a parser defect. No diagnostic overlay is present in production source.

## Final eager comparison

{chr(10).join(table)}

There are {summary['workers']} validated fresh workers, six balanced-order rounds for nine configurations and three frozen binaries. The full input contracts, raw workers, and plans are retained. The final candidate lowers late Boolean CPU 12.2% and late text CPU 41.0% relative to the previous prototype. Relative to the original, those changes are +2.3% and -37.7% respectively.

The power references retain a peak near 422 MiB instead of 720 MiB, about 41% lower. Their elapsed times are still about twice the original. The memory improvement is real, but it does not erase the CPU or latency costs elsewhere.

## Streaming regression check

{chr(10).join(streamtable)}

The streaming comparison has {stream['workers']} validated workers plus 15 exact-output preflight workers. Each timed pass consumes and releases public 10000-row chunks immediately. A separate untimed pass checks all native types, values, null positions, and output order. Both passes use identical selected records and schemas across the three binaries.

The current change is within 4.2% CPU of the previous prototype on these five inputs. The earlier shared-conversion prototype was already slower than the original streaming reader. The final branch is 10.1% to 23.9% above the original on these inputs. This is an additional blocker for promoting the whole branch. Similar peak RSS does not compensate for added CPU work in streaming.

## Validation

{chr(10).join(tests)}

All three frozen parser implementations agree on 30720 deterministic raw-byte fixtures, including custom delimiter and quote overlaps, ragged rows, quoted newlines, escaped quotes, and permissive EOF cases. Count-contract tests compare counting with discovery and cover limits, cancellation, and long quoted records.

Fallback tests protect original-sample eligibility, original lexical text, earlier contradictions in a surviving candidate, unaffected completed columns, null values, and a rejecting token beyond the first batch. The new test files have 64 and 61 source lines. Large fixtures use generated repeated records rather than large literals.

The standard `tabular-smoke` run passes all 190 SwiftSci and pandas samples in production-default mode, and its certificate audit passes. This covers declared tabular workloads and the SwiftDataFrame test target. It does not establish full numerical certification or validate every MLX-dependent library module.

Two independent reviewers found no actionable standards or specification defects. The final small cleanup derives `rejected` from the recorded field instead of maintaining duplicate state. The final source also adds the cross-batch offset test.

## Measurement boundaries

Both resource comparisons use CPU backends with native parallelism, identical input bytes and schema contracts, AC power checks, warm input pages, and balanced process order. No builds or tests from this task run during accepted resource timings. Every timing worker validates its output. Validation is outside measured CPU and elapsed time, and memory is captured before validation. No outliers are trimmed.

CPU means process user plus system time. RSS includes resident mappings and allocator behavior. Neither metric is an allocation count or energy measurement. Native optional result storage is unchanged. No SRAM, SLC, processor-affinity, or hardware energy claim follows from these results.

Build receipts retain commands, source hashes, binary hashes, and dependency identities. Scratch binaries and full local test bundles remain in `{R}`. The reproduction scripts contain local worktree and input paths. Restore equivalent paths or adjust them before rerunning elsewhere. Reference dataset provenance remains with the [prepared-date evaluation](../2026-10-21-csv-prepared-dates/README.md).

## Decision and next gate

Keep the local commits and the measured memory improvement. Do not open a PR to replace the default reader yet. The next investigation must isolate ordinary per-cell conversion and per-batch scheduling against the original implementation, including streaming. Wide numeric and repeated-date reference data are required controls. Promote a change only if it lowers CPU work without losing bounded discovery, native values, null behavior, or the measured memory benefit.

This record belongs to `codex/engineering-notes`. Implementation PRs must not include it or the benchmark artifacts.
'''
(D/'README.md').write_text(text)
(D/'reviews.md').write_text('''# Independent review results

Standards review found no actionable findings against the previous exact-sizing prototype. The private output specialization preserves target boundaries. Original-token offsets remain internal. Borrowed memory stays scoped to joined workers, and tests use small typed expressions.

Specification review found no actionable findings. Counting shares the existing grammar, including delimiter precedence, quoted and ragged records, EOF behavior, limits, and cancellation. Rejected offsets are rebased into the original retained source. Pruning only eliminates originally eligible types. Surviving candidates still replay all rows. Overrides do not enter fallback, missing fields stay distinct from invalid values, and streaming inference remains chunk-local.

The final cleanup removes a redundant rejection switch, and the added regression test covers the offset of a rejection beyond the first eager batch. Release, Debug, and Address Sanitizer validation cover that final head.
''')
files={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in D.rglob('*') if p.is_file() and p.name!='artifact-sha256.json'}
(D/'artifact-sha256.json').write_text(json.dumps(files,indent=2)+'\n');print(D)
