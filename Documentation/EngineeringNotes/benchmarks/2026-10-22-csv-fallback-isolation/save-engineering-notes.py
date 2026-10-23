from pathlib import Path
import json,hashlib,subprocess,shutil,tarfile,gzip,re
R=Path(__file__).resolve().parent;N=Path('/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018');S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');P=Path('/private/tmp/swiftsci-csv-prefix-selection-20261022');D=N/'Documentation/EngineeringNotes/benchmarks/2026-10-22-csv-fallback-isolation'
assert subprocess.check_output(['git','branch','--show-current'],cwd=N,text=True).strip()=='codex/engineering-notes';assert not subprocess.check_output(['git','status','--porcelain'],cwd=N)
D.mkdir(exist_ok=False)
for p in R.iterdir():
 if p.is_file() and p.suffix in ['.py','.swift','.json','.md']:shutil.copy2(p,D/p.name)
 if p.is_file() and p.suffix=='.patch':(D/(p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
worker_index=[]
for stage in sorted(R.iterdir()):
 if not stage.is_dir() or not (stage/'workers.jsonl').exists():continue
 target=D/stage.name;target.mkdir()
 for p in stage.iterdir():
  if not p.is_file():continue
  if p.name=='workers.jsonl':
   raw=p.read_bytes();(target/(p.name+'.gz')).write_bytes(gzip.compress(raw,mtime=0));worker_index.append(dict(stage=stage.name,path=stage.name+'/'+p.name+'.gz',raw_sha256=hashlib.sha256(raw).hexdigest(),records=len(raw.splitlines())))
  elif p.suffix=='.json':shutil.copy2(p,target/p.name)
for stage in ['metadata-unicode','standardized']:
 shutil.copytree(R/stage,D/stage)
shutil.copy2(R/'fallback-code/summary.json',D/'fallback-code-summary.json')
(D/'worker-index.json').write_text(json.dumps(worker_index,indent=2)+'\n')
with tarfile.open(D/'experiments.tar.gz','w:gz') as archive:
 for folder in ['variants','metadata-boundary-inputs','fallback-code']:archive.add(R/folder,arcname=folder)
 archive.add(S/'Sources/SwiftDataFrame',arcname='source-snapshots/metadata/Sources/SwiftDataFrame')
 archive.add(P/'variants/cleanup/Sources/SwiftDataFrame',arcname='source-snapshots/cleanup/Sources/SwiftDataFrame')
 for p in R.glob('*.log'):archive.add(p,arcname='logs/'+p.name)
 for label in ['cleanup','production','preflight','no-preparation','metadata','diagnostic-cleanup','diagnostic-selected','diagnostic-preflight']:
  for p in (R/'build'/label).glob('*.json'):archive.add(p,arcname='build/'+label+'/'+p.name)
 archive.add(R/'standard-worker/SwiftSciBenchmarkWorker.build.json',arcname='standard-worker/SwiftSciBenchmarkWorker.build.json')
state=json.loads((R/'decision.json').read_text());refs=json.loads((R/'reference-comparisons.json').read_text());phase=json.loads((R/'phases/summary.json').read_text());get=lambda case,e:next(a['cpu_per_iteration_ns']/1000 for a in phase if a['case']==case and a['action']=='prefix' and a['engine']==e)
old=get('long-3392','diagnostic-selected');new=get('long-3392','diagnostic-preflight');admitted_old=get('long-3457','diagnostic-selected');admitted_new=get('long-3457','diagnostic-preflight')
selected=[a for a in refs if a['case'] in ['energy-default','Aotizhongxin-default']];table=['| Reference and scope | Policy | Parent CPU ms | Metadata CPU ms | CPU change | Peak RSS before / after MiB |','|---|---|---:|---:|---:|---:|']
for a in selected:table.append(f"| {a['case']}, {a['scope']} | {a['policy']} | {a['cpu_before_ms']:.3f} | {a['cpu_after_ms']:.3f} | {a['cpu_change_percent']:+.1f}% | {a['peak_before_mib']:.2f} / {a['peak_after_mib']:.2f} |")
peak=max(a['peak_after_mib']-a['peak_before_mib'] for a in refs)
text=f'''# CSV preparation costs and benchmark calibration

Commit `5d1f89a961106104757f2d8d0b8faba79487d100` makes oversized null-token rejection cheaper and passes functional verification. The complete CSV branch retains gains on real reference reads. It remains local and experimental because calibrated small-input CPU warnings are unresolved. The benchmark also flags an identical-binary comparison, so a passing output check alone cannot qualify these timings.

## What changed

The earlier selected decoder can inspect almost all token bytes before discovering that preparation exceeds its row budget. The new constructor first checks native UTF-8 storage and stored byte lengths. Foreign storage stays on hashed lookup, without forced conversion. Only an admitted token set gets an ASCII byte scan and prefix masks.

Admission budgets two token traversals plus the byte scan within the selected row count. Subtraction avoids integer overflow. After admission, the inner byte loop needs no remaining-budget check. Empty sets, tiny sets, non-ASCII tokens, saturated masks, canonical String equality, parsing, ownership, and output representation retain their existing behavior.

The change adds no cache, row buffer, worker limit, public option, or per-row strategy switch. The source worktree contains only the constructor change and focused tests. Diagnostic entry points exist only in archived snapshots. The UTF-16 NSString fixture rejects safely without requiring a particular storage representation from future runtimes.

The parent implementation is `167d9a4e6f8cb923342dea3236721c8722015bf3`. The child remains on `codex/csv-prepared-string-membership`; prior commits remain available. No branch was pushed and no PR was opened. [The patch](metadata-fix.patch.gz) preserves the exact commit, and [the decision](decision.json) keeps promotion blocked.

## Reproduce before attributing a regression

The minimized loop uses two previously recurring streamed inputs and the matching serial or parallel policy. Forty-eight independently validated workers complete each run. Two of four initial native-hash runs cross the unchanged CPU review threshold. The verdict is not stable enough to attribute the difference to implementation alone.

Four ranked hypotheses guide the probes: runtime variation on short reads, String hash randomization, failed preparation work, and changed generated fallback code. The [hypotheses and predictions](hypotheses.json) were recorded before the corresponding probes.

Two labels then invoke the exact same executable with matched argv, options, bytes, and scheduling. This A/A control produces a CPU warning in three of four small-sample runs. The CPU observations are real. The inference that a code change caused them would be false.

Diagnostic fixed hashing reduces warnings. A separate check verifies identical String hash fingerprints across six fixed-hash workers and differing fingerprints across native workers. These runs investigate a mechanism and never qualify production performance. The interleaved study balances native and diagnostic modes instead of relying only on consecutive stages. It retains 2,400 workers and no review flags. It does not erase the earlier flags.

One early diagnostic CLI verdict inspected only the last implementation when four labels were present. Its per-implementation flag files were correct. The verdict now checks all flags; [the independent audit](audited-verdicts.json) preserves the discrepancy. Later qualification uses the flag files and separate quality gates.

## Preparation is cheaper, but is not the entire read

Six workers per cell run 10,000 constructor or factory calls. Prefix probes invoke the actual private constructor through a non-inlined diagnostic entry point and preserve opaque ownership. Factory probes also include plan creation, attempt allocation, boxing, and release. These costs are diagnostic phases, not additive fractions of a complete CSV read.

For 64 long ASCII tokens and 3,392 selected rows, both constructors reject preparation. The earlier prefix probe uses {old:.4f} microseconds per call, while metadata preflight uses {new:.4f} microseconds. That is about {old/new:.1f} times less CPU in this isolated probe, not a full-read speedup.

At the new admitted boundary of 3,457 rows, the earlier probe uses {admitted_old:.4f} microseconds and preflight uses {admitted_new:.4f} microseconds. Moving admission outside the byte loop also reduces admitted scan cost on that case. Default short-token admitted preparation remains close in absolute cost.

The 540 phase workers cover both budget boundaries, short and long tokens, and a separately validated hash-lookup phase. Native hash-only costs vary substantially across workers despite identical source logic. Fixed-hash diagnostics are more repeatable. These observations support investigating hash setup and runtime variation; they do not prove a particular bucket, scheduler, cache, or silicon mechanism. See [phase results](phases.md) and the [hash-control proof](hash-control-proof.json).

## Generated-code checks

The actual committed source hashes match the earlier preflight snapshot. Every `__TEXT` section of the two optimized ResourceProbe binaries is byte-identical. [This proof](actual-source-code-proof.json) checks runtime-code identity; it does not substitute for the committed head's tests.

Static inspection covers ten append and dispatch functions in cleanup, first selection, no-preparation, and metadata binaries. Eight inspected typed append functions retain their instruction counts and indirect-call counts. The flat and compact dispatch functions grow by 368 and 371 instructions when the new decoder case exists. The no-preparation snapshot retains that growth. No loss of the inspected specializations or new indirect calls is observed.

Instruction counts are not executed instructions. Code growth alone does not establish an instruction-cache cause for the timing differences. The [static summary](fallback-code-summary.json), inspection script, and archived assembly preserve that boundary.

## Actual-head verification

The exact committed head passes all 394 DataFrame tests in Release, Debug, and Address Sanitizer, with no failures or skips. The updated test file remains 57 lines with small typed expressions. Tests cover exact admission, saturated masks, bridged NSString values, ownership, Unicode equivalence, invalid UTF-8, and eager/streamed boundaries.

Grammar comparison passes all 30,720 cases with the existing digest. Unicode validation checks 3,336,243 String cells per scheduling policy. A separate 480-worker check covers 120 independent boundary contracts, eager and streamed reads, and both policies. Those single-observation boundary workers establish correctness only.

The actual-head uninstrumented production-default `tabular-smoke` run creates 190 SwiftSci and pandas responses and passes its audit. That is the profile's regression-policy result, not full numerical certification. The standard worker receipt records commit `5d1f89a961106104757f2d8d0b8faba79487d100` and its source-tree fingerprint.

## Broad reference results

These comparisons use the frozen parent `c906c3fbbb0baf1357438a7079921a6448e0c9e5`, before the cleanup and selected-decoder work. They show the complete branch's effect, not the metadata refinement alone. Each median uses eight fresh workers per implementation and matching policy.

CPU is process user-plus-system time for public read and output release. Independent native-value validation is outside timing. Bytes, schemas, null tokens, native types, null positions, order, and read scope match within each pair. Parallel compares with parallel and serial with serial. Elapsed time remains separate in [the complete table](acceptance.md).

'''+ '\n'.join(table)+f'''

The four broad matrices contain 2,432 validated workers and no CPU or memory review flags. The largest median peak-RSS increase is {peak:.2f} MiB. RSS is a process high-water mark, not an allocation count. No FLOP, energy, SRAM, cache, or contention claim follows.

The default-token figures do not apply to the household fixture's original two-token configuration, which already uses its specialized decoder. The [width and numeric-null](mode-controls.md), [text-null](text-controls.md), and [long-key](long-key-controls.md) results remain separate.

## Why promotion remains blocked

The prospective native-hash panel fixes 26 scope/policy combinations before timing. It covers the two earlier recurring cases and neighboring rows around the new long-token admission boundary at zero and high null injection. Each label gets 120 independent workers per case, for 9,360 workers. No fixed-hash result enters acceptance.

The panel retains three CPU review flags. One is the identical-binary control. Two belong to metadata preflight, and one of those overlaps the failed A/A case. In the remaining 3,392-row parallel stream case, candidate CPU median increases 26.9%, and the mean of worker medians increases 21.7%. That case remains unresolved.

A separate two-sided quality gate checks identical-binary deviations in either direction and fails on one case. Every original directional flag remains. No observation was trimmed, threshold loosened, or prior failure replaced by a later passing run. The [calibrated table](metadata-calibration.md), [resource flags](metadata-calibration/review-flags.json), and [quality gate](metadata-calibration/quality-gate.json) expose the result.

The isolated constructor improvement is established. It has not been shown to explain every whole-read CPU difference. The next experiment must pair the public readers within one process using the same native null-token Set. Identical-binary and namespace/code-generation controls must accompany that comparison. Keep native hashing and scheduling, and use the recurring parallel-stream case before redesigning the fallback loop or tuning a cutoff.

## Reproducibility

All builds, tests, and grammar checks finish before their associated timing stages. Power is AC. Worker order rotates and reverses. Input and output hashes, source hashes, binary hashes, commands, and scope are retained. Unrelated host activity remains uncontrolled.

The record contains 16,908 worker responses across diagnostic, phase, correctness, and actual-head resource stages. This count is not a count of distinct datasets or numerical certifications. Constructor responses validate admission and retained lifetime. Hash phases and full reads validate native outputs. The 480 correctness-only workers are included in the total; Unicode workers, standard responses, and small control pilots are separate.

- [Actual-head stage receipts](metadata-qualification-status.json) and [qualification result](metadata-qualification-result.json)
- [Prospective panel](metadata-calibration-panel.json) and [controller](metadata-calibration.py)
- [Phase controller](phases.py) and [measurement-quality check](measurement-quality.py)
- [Worker inventory and uncompressed hashes](worker-index.json)
- [Snapshots, generated inputs, build receipts, assembly, and logs](experiments.tar.gz)
- [Artifact hashes](artifact-sha256.json)
- [Previous selection study](../2026-10-22-csv-prefix-selection/README.md)

Worker JSONL files are stored as exact gzip streams in their stage folders. Decompression restores their recorded raw hashes and original controller filenames. Controllers preserve original paths, which may be adapted while retaining input, source, and binary identities. Shared reference datasets remain with their existing owner.
'''
(D/'README.md').write_text(text)
manifest={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(D.rglob('*')) if p.is_file() and p.name!='artifact-sha256.json'};(D/'artifact-sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
for p in D.rglob('*.md'):
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' not in link and not link.startswith('#'):assert (p.parent/link.split('#')[0]).exists(),(p,link)
assert all(hashlib.sha256((D/p).read_bytes()).hexdigest()==h for p,h in manifest.items())
for w in worker_index:assert hashlib.sha256(gzip.decompress((D/w['path']).read_bytes())).hexdigest()==w['raw_sha256']
print(D);print(len(manifest),'files;',round(sum(p.stat().st_size for p in D.rglob('*') if p.is_file())/2**20,2),'MiB; hashes and links verified')
