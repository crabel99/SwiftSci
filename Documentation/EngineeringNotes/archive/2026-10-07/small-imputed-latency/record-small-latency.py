from pathlib import Path
import gzip,json,statistics,hashlib,subprocess,os
repo=Path('/Users/crabel/Documents/src/SwiftSci');out=Path('/Users/crabel/local-ai/spl/swiftsci/small-imputed-latency-20261007');s=json.loads((out/'phases/summary.json').read_text());c=json.loads((out/'commit.json').read_text());prov=json.loads((out/'phases/provenance.json').read_text())
recheck=json.loads((out/'recheck/summary.json').read_text());recheck_prov=json.loads((out/'recheck/provenance.json').read_text())
old=json.loads(Path('/Users/crabel/local-ai/spl/swiftsci/imputed-regression-20261007/comparison-sustained/provenance.json').read_text())
assert recheck_prov['binary_sha256']==old['binary_sha256']
recheck_changes=[]
for i in range(3):
 d={r['storage']:r for r in recheck if r['round']==i}
 recheck_changes.append(100*(d['owned']['requests_per_second']/d['copy']['requests_per_second']-1))
rows=[];pairs=[]
for route in ['preprocessing','direct','pipeline']:
 for slots in [1,2]:
  a=[r for r in s if r['route']==route and r['slots']==slots]
  changes=[]
  for iteration in range(2):
   for pair in range(6):
    d={r['owned']:r for r in a if r['round']==iteration and r['pair']==pair}
    delta=100*(d[True]['requests_per_second']/d[False]['requests_per_second']-1)
    changes.append(delta);pairs.append({'route':route,'slots':slots,'round':iteration,'pair':pair,'throughput_change_percent':delta})
  phases={own:{phase:statistics.median(r['phases'][phase]['mean_us'] for r in a if r['owned']==own) for phase in ['preprocessing','prediction','validation']} for own in [False,True]}
  rows.append(f"| {route} | {slots} | {phases[False]['preprocessing']:.2f} / {phases[True]['preprocessing']:.2f} | {phases[False]['prediction']:.1f} / {phases[True]['prediction']:.1f} | {statistics.median(changes):+.1f}% | {min(changes):+.1f}% to {max(changes):+.1f}% |")
validation={'commit':c['commit'],'parent':c['base'],'production_changes':False,'focused_release_tests_passed':2,'controller_tests_passed':20,'smoke_workers':6,'diagnostic_workers':12,'diagnostic_requests':294912,'recheck_workers':6,'recheck_requests':98304,'recheck_throughput_changes_percent':recheck_changes,'maximum_absolute_error':max(r['max_error'] for r in s),'complete_outputs_match':True,'request_reservations_drained':True,'gpu_owners_returned_to_baseline':True,'final_gpu_active_and_cache_zero':True,'workers_remaining':0,'paired_results':pairs,'decision':'Keep explicit consuming ownership. Do not add a preprocessing threshold or infer a stable ownership regression. Investigate the awaited prediction boundary and benchmark validation overhead before tuning production dispatch.'}
(out/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
report=f'''# Small-request latency diagnosis

Date: 2026-10-07

## Finding and decision

The earlier 14.2% small-request throughput loss did not reproduce as a stable ownership penalty. An unchanged-binary rerun produced paired consumed-versus-retained changes of +64.0%, -1.0% and -2.7%. Same-process controls also varied in both directions. Keep explicit consuming ownership and the existing production behavior. These observations do not justify a preprocessing size threshold.

The phase probes localize most request time inside the awaited model prediction call. The combined preprocessing and ownership-check phase is about 0.4 to 1.2 microseconds in the aggregate table, and is lower for consumed inputs in every route and concurrency combination. GPU prediction-call durations are about 366 to 766 microseconds. That call includes actor waits, validation, Float packing/import, GPU execution and readback. This experiment does not identify an internal GPU cause or distinguish scheduling from allocation behavior within that call.

Output validation and hexadecimal hash formatting cost about 28 to 48 microseconds in the aggregate controls. That is benchmark work, and it dwarfs the preprocessing operation for these small inputs. It must remain visible when interpreting complete-workflow throughput.

## Implementation scope

Commit `{c['commit']}` follows `{c['base']}` on `codex/retained-memory-accounting-trial`. It adds a separate diagnostic worker, controller, contract tests and README instructions. The original throughput worker and all production sources are unchanged. Nothing was pushed; the primary checkout was not switched. Measurements and decisions remain on `codex/engineering-notes`.

The worker exposes three controls. `preprocessing` uses the same fitted preprocessing but checks predictions with a scalar CPU formula using fitted weights. It is not production CPU inference. `direct` calls the public GPU model; `pipeline` calls it through the public regression pipeline. Each control runs one and two admitted request slots.

Each process alternates retained and consumed blocks over six pairs of 2,048 requests per mode, reversing ownership order in alternate pairs. Both members of a pair use identical request IDs and data. A second fresh process repeats each control, with route order reversed. Each request has 64 rows and 3 columns, training-only imputation and scaling, missing entries and shifted held-out observations.

## Measurement interpretation

The diagnostic clocks split fixture generation with oracle construction, preprocessing with ownership checks, prediction, and output validation with hash formatting. The preprocessing phase intentionally measures the original benchmark helper, including address capture and the consumed-only buffer assertion. It bounds their combined cost and cannot isolate public transform cost from check cost.

Prediction timing measures the complete awaited API call. It is not device kernel time. Request durations overlap with two slots, so their sum does not equal elapsed wall time. Diagnostic clocks and paired block drains perturb execution, and these timings must not be pooled with throughput qualification results. No cache clearing occurs between blocks.

The table gives medians of per-block mean durations in microseconds. Each duration cell is retained / consumed. The throughput column is the median of 12 within-process paired ratios, with all observed ratios shown in the range.

| Control | Slots | Preprocessing plus checks, µs | Prediction call, µs | Paired throughput change | Paired range |
| --- | ---: | ---: | ---: | ---: | --- |
{chr(10).join(rows)}

GPU controls still vary when the regression wrapper is bypassed. This rules out treating the wrapper as the sole explanation for the variability; it does not measure a causal wrapper penalty. The submicrosecond preprocessing difference cannot explain the earlier tens-of-microseconds service gap in these observed runs. Direct-model and pipeline paired medians are close to zero compared with their ranges, but no formal equivalence or noninferiority claim is made.

## Validation, resource handling and review

The Release diagnostic built and two focused public-workflow integration tests passed. Twenty controller tests passed, including rejection of missing or mismatched outputs, malformed phase timings, nonfinite errors, undrained reservations and invalid memory samples. The prior 874 selected Release passes belong to the parent commit; the full suite was not rerun for this benchmark-only change.

Six smoke workers exercised every route and slot count. Twelve diagnostic workers completed 294,912 requests. Complete output hashes match across ownership modes; GPU hashes also match between direct and pipeline routes and between concurrency settings. The maximum absolute prediction error was `{validation['maximum_absolute_error']:.17g}`, below the unchanged `1e-4` bound.

Every paired block released its request reservations and returned MLX active allocations to the fitted-model baseline. Final model release and cache clearing returned active and cached MLX memory to zero. All workers exited. Admission and cache limits remained 256 MiB, request reservations were 16 MiB, and diagnostic memory samples stayed below 512 MiB. These are bounded-run checks, not universal CPU leak certification.

The first smoke attempt stopped at the memory-pressure gate before launching a worker. A read-only follow-up reported normal pressure, and the retry passed under the same gate. Ordinary host activity remained allowed. No process belonging to another application was stopped.

Standards review found no actionable violation. Behavioral review identified that the preprocessing clock includes ownership checks. The README and controller now state that combined scope explicitly; no claim of pure transform timing remains. Review also identified two omitted controller-dependency fingerprints. The final controller records `contracts.py` and `runner.py`. The exact controller used for these measurements is archived, with a supplemental manifest documenting the metadata-only correction. Workload and validation logic did not change after measurement.

## Next experiment

Separate the awaited prediction boundary into dispatch/validation, packing/import, GPU submission/completion and readback before changing a size threshold. Also separate hexadecimal result formatting from measured work while preserving complete output verification. That would remove a known benchmark cost without weakening correctness checks. The current results do not establish which internal prediction phase causes the variance, or where a CPU/GPU crossover belongs.

## Evidence

Host: Apple M4 Max, 128 GiB unified memory, macOS 27.0 build 26A428. Release arm64 diagnostic, coverage disabled, existing pinned dependencies. No macOS 14 runtime was exercised.

Diagnostic binary SHA-256: `{prov['binary_sha256']}`.

Unchanged throughput-recheck binary SHA-256: `{recheck_prov['binary_sha256']}`.

- [Diagnostic phase summary](../archive/2026-10-07/small-imputed-latency/phases/summary.json)
- [Measured source fingerprints](../archive/2026-10-07/small-imputed-latency/phases/provenance.json)
- [Unchanged throughput rerun](../archive/2026-10-07/small-imputed-latency/recheck/summary.json)
- [Validation and paired ratios](../archive/2026-10-07/small-imputed-latency/validation.json)
- [Provenance correction](../archive/2026-10-07/small-imputed-latency/provenance-supplement.json)
- [Previous complete workflow](2026-10-07-imputed-regression-integration.md)

Raw worker JSON and logs are losslessly compressed in the archive. Xcode result bundles remain in the local evidence directory.
'''
assert '\u2014' not in report
(out/'REPORT.md').write_text(report)
def git(*args,input=None,env=None):return subprocess.check_output(['git','-C',str(repo),*args],input=input,env=env).decode().strip()
base='289c7b7f34a08d829ad0a7e6f8f32dd12b212304';branch='refs/heads/codex/engineering-notes'
assert git('rev-parse',branch)==base and git('rev-parse','codex/retained-memory-accounting-trial')==c['commit']
assert git('rev-parse','HEAD')=='6e10f5833961d6813cc65b0491fe622c83c55a5d'
index='Documentation/EngineeringNotes/README.md';readme=git('show',base+':'+index)+'\n';assert '## Start here\n\n' in readme
readme=readme.replace('## Start here\n\n','## Start here\n\n- [Small-request latency diagnosis](benchmarks/2026-10-07-small-imputed-latency.md) separates preprocessing and validation overhead from the awaited prediction call, records variable ownership timing, and leaves production dispatch unchanged.\n\n',1)
files={index:readme.encode(),'Documentation/EngineeringNotes/benchmarks/2026-10-07-small-imputed-latency.md':report.encode()}
prefix='Documentation/EngineeringNotes/archive/2026-10-07/small-imputed-latency/'
for directory in ['recheck','phases']:
 for p in sorted((out/directory).iterdir()):
  if not p.is_file():continue
  key=prefix+directory+'/'+p.name
  if p.suffix=='.json' and not p.name.endswith('-command.json') and p.name not in ['summary.json','provenance.json']:
   files[key+'.gz']=gzip.compress(p.read_bytes(),mtime=0)
  else:files[key]=p.read_bytes()
for p in sorted(out.iterdir()):
 if p.is_file() and p.suffix in ['.json','.log','.py']:
  key=prefix+p.name
  if p.suffix=='.log':files[key+'.gz']=gzip.compress(p.read_bytes(),mtime=0)
  else:files[key]=p.read_bytes()
for name in ['smoke-imputed-latency.py','commit-small-latency.py','record-small-latency.py']:files[prefix+name]=Path('/private/tmp',name).read_bytes()
env=dict(os.environ,GIT_INDEX_FILE=str(out/'notes.index'));git('read-tree',base,env=env)
for path,data in files.items():
 blob=git('hash-object','-w','--stdin',input=data);git('update-index','--add','--cacheinfo',f'100644,{blob},{path}',env=env)
git('diff','--cached','--check',base,env=env)
assert set(git('diff','--cached','--name-only',base,env=env).splitlines())==set(files)
n=git('commit-tree',git('write-tree',env=env),'-p',base,input=b'docs(memory): record small-request latency diagnosis\n');git('update-ref',branch,n,base)
(out/'notes-commit.json').write_text(json.dumps({'base':base,'commit':n,'files':len(files),'archive_bytes':sum(map(len,files.values()))},indent=2)+'\n')
print(n);print('\n'.join(rows))
