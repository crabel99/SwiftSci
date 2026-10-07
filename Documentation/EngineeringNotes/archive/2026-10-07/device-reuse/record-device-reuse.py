from pathlib import Path
import gzip,json,statistics,subprocess,os
repo=Path('/Users/crabel/Documents/src/SwiftSci');out=Path('/Users/crabel/local-ai/spl/swiftsci/device-reuse-20261007')
c=json.loads((out/'commit.json').read_text());s=json.loads((out/'comparison/summary.json').read_text());prov=json.loads((out/'comparison/provenance.json').read_text())
phases=['device_lookup','buffer_allocation','packing','import','completion','scope_cleanup','actor_wait','actor_body','awaited_prediction']
table=[];paired=[]
for phase in phases:
 cells=[]
 for slots in [1,2]:
  for route in ['lookup','retained']:
   cells.append(statistics.median(b['phases'][phase]['mean_us'] for b in s if b['slots']==slots and b['route']==route))
 table.append('| '+phase+' | '+' | '.join(f'{x:.3f}' for x in cells)+' |')
for slots in [1,2]:
 for iteration in range(2):
  for cycle in range(6):
   d={b['route']:b for b in s if b['slots']==slots and b['round']==iteration and b['cycle']==cycle}
   paired.append({'slots':slots,'round':iteration,'cycle':cycle,
     'awaited_change_percent':100*(d['retained']['phases']['awaited_prediction']['mean_us']/d['lookup']['phases']['awaited_prediction']['mean_us']-1),
     'body_change_percent':100*(d['retained']['phases']['actor_body']['mean_us']/d['lookup']['phases']['actor_body']['mean_us']-1),
     'throughput_change_percent':100*(d['lookup']['elapsed_ms']/d['retained']['elapsed_ms']-1)})
comparison=[]
for slots in [1,2]:
 vals=[b for b in paired if b['slots']==slots]
 def describe(key):
  a=[b[key] for b in vals];return f'{statistics.median(a):+.1f}% ({min(a):+.1f}% to {max(a):+.1f}%)'
 comparison.append(f"| {slots} | {describe('awaited_change_percent')} | {describe('throughput_change_percent')} |")
validation={'commit':c['commit'],'parent':c['base'],'production_changes':False,'focused_release_tests_passed':2,'controller_tests_passed':27,'smoke_workers':2,'smoke_requests':768,'comparison_workers':4,'comparison_requests':73728,'complete_public_outputs_match':True,'historical_output_hashes_match':True,'maximum_absolute_error':max(b['max_error'] for b in s),'gpu_owners_returned_to_baseline':True,'final_gpu_active_and_cache_zero':True,'reservations_drained':True,'workers_remaining':0,'paired_results':paired,'decision':'Advance a minimal retained-device candidate for production-path qualification across small, medium and large workloads. Do not add a buffer pool or change CPU/GPU dispatch thresholds.'}
(out/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
report=f'''# Retained Metal device experiment

Date: 2026-10-07

## Finding

Default-device lookup dominates the device/buffer setup phase in this small-input diagnostic. Repeated `MTLCreateSystemDefaultDevice()` calls take about 51 to 52 microseconds, while a fresh 768-byte Metal buffer takes about 3 microseconds. Selecting the actor's retained device handle takes about 0.03 microseconds. This measures the lookup call's cost; it does not establish which internal Metal operation accounts for that time.

The same diagnostic actor runs both device choices. Retaining the handle reduces paired awaited prediction duration by a median 31.0% with one admitted slot and 27.1% with two. All 24 paired cycles favor the retained handle, with latency reductions between 17.8% and 45.6%. This is evidence for testing a narrow production change, not a claim that production service performance already improved by those percentages.

## Implementation and control

Commit `{c['commit']}` follows `{c['base']}` on `codex/retained-memory-accounting-trial`. It changes four benchmark files. Production source, packing strategy, logical-extent import and dispatch are unchanged. Nothing was pushed, and the primary checkout remains at `6e10f5833961d6813cc65b0491fe622c83c55a5d`.

The diagnostic actor retains one Metal device during setup for the entire experiment, including the per-request lookup control. Both controls therefore have the same actor, weights, bias and retained state. The sole request-path choice is obtaining the default device again or selecting that existing handle. Each route allocates and releases a fresh buffer on every request. This is device-handle reuse, not a storage pool.

The third route is the unchanged public GPU prediction API. All routes consume identical 64-row, 3-column fixtures after training-only imputation and minmax scaling. Complete prediction hashes must match across all routes and the preceding diagnostic's historical records. Independent analytic predictions must agree within the unchanged `1e-4` bound.

Each worker runs six cycles of 1,024 requests per route. The cycles cover all six permutations of public, lookup and retained route order. Two fresh processes run each slot count, reversing slot order in the second round. No cache clearing occurs between measured blocks. Every block drains work before memory sampling and the next route.

Output schema version 2 names each route and cycle, splits lookup and allocation times, and preserves aggregate digest construction. Historical schema version 1 records remain tied to their original controller commit. No historical record was rewritten.

## Timing results

Durations are microseconds. Each value is the median of 12 per-block mean durations. Actor-body and awaited durations contain the other phases; they are not additional work. Completion covers host submission and GPU waiting, not device kernel time. Concurrent request durations overlap and cannot be summed as elapsed wall time.

| Phase | One slot, lookup | One slot, retained | Two slots, lookup | Two slots, retained |
| --- | ---: | ---: | ---: | ---: |
{chr(10).join(table)}

The table below compares routes within the same cycle and process. It gives the median percentage change followed by the complete observed range. Lower duration is better; higher throughput is better. Throughput covers the whole diagnostic block, including fixture generation, preprocessing, numerical validation and raw hashing. It excludes hexadecimal result encoding after the block clock.

| Slots | Awaited duration change | Diagnostic block throughput change |
| --- | ---: | ---: |
{chr(10).join(comparison)}

Removing repeated lookup also shortens the work that another request waits behind at two slots. Buffer allocation, packing and import remain small. Completion timing varies, especially in the one-slot runs, so the total improvement should not be attributed entirely to the direct lookup interval. Ordinary host activity was allowed, and no unrelated applications were stopped.

These clocks instrument a benchmark mirror with explicit evaluation and synchronization, not the production method. Clock calls and diagnostic bookkeeping can affect optimization and scheduling. Public-route durations are recorded as a control, but the causal device comparison is lookup versus retained within the same diagnostic implementation.

## Validation and ownership

Two focused Release public-workflow integration tests pass. Twenty-seven controller tests pass, including schema, all-route coverage, later-cycle ordering, output mismatch, impossible timings and cleanup failures. Independent behavioral and standards reviews found no actionable issue.

Two smoke workers complete 768 requests. Four comparison workers complete 73,728 requests, with full prediction equality across routes, slot counts and the historical diagnostic. The maximum absolute analytic error is `{validation['maximum_absolute_error']:.17g}`.

Every measured block returns MLX active allocation to the fitted-model baseline and drains admission reservations. Final model and probe release, GPU synchronization and cache clearing leave MLX active and cached allocation at zero. All workers exit; sampled RSS stays below 27 MiB. These bounded checks do not prove that Metal or system framework caches retain no memory, or establish universal leak freedom.

The controller retains normal memory-pressure admission, a 180-second child deadline, explicit child-process ownership, a 256 MiB admission/cache limit and a conservative 16 MiB reservation per request. No buffer pooling or global device owner was introduced in production.

## Next production candidate

`ScopedGPURead` currently looks up the default device for each matrix allocation. The retained-input trial allocator also performs a lookup. The next change should provide one internal device owner for these allocation paths while preserving allocation-error behavior, buffer lifetimes, shape checks and stream synchronization. First inspect other device owners in the remaining modules to avoid introducing a competing owner.

Qualify that change through the actual public pipeline with phase clocks disabled, compare against a preserved baseline binary, and cover small, medium, large and mixed request sizes. Recheck numerical equality, source immutability, admission accounting and final cleanup. Do not use this experiment to select a CPU/GPU crossover or justify buffer pooling.

## Evidence

Host: Apple M4 Max, 128 GiB unified memory, macOS 27.0 build 26A428. Release arm64, coverage disabled, pinned dependencies and precise Float settings. No macOS 14 runtime was exercised.

Binary SHA-256: `{prov['binary_sha256']}`.

- [Comparison summary](../archive/2026-10-07/device-reuse/comparison/summary.json)
- [Source and binary fingerprints](../archive/2026-10-07/device-reuse/comparison/provenance.json)
- [Validation and paired results](../archive/2026-10-07/device-reuse/validation.json)
- [Previous prediction-phase experiment](2026-10-07-prediction-phases.md)

Worker records and logs are losslessly compressed in the archive. Xcode result bundles remain local.
'''
assert '\u2014' not in report
(out/'REPORT.md').write_text(report)
def git(*args,input=None,env=None):return subprocess.check_output(['git','-C',str(repo),*args],input=input,env=env).decode().strip()
base='c1205e3c5c868019bd7646c25bf1b0acea91f9e6';branch='refs/heads/codex/engineering-notes'
assert git('rev-parse',branch)==base and git('rev-parse','codex/retained-memory-accounting-trial')==c['commit']
assert git('rev-parse','HEAD')=='6e10f5833961d6813cc65b0491fe622c83c55a5d'
index='Documentation/EngineeringNotes/README.md';readme=git('show',base+':'+index)+'\n';assert '## Start here\n\n' in readme
readme=readme.replace('## Start here\n\n','## Start here\n\n- [Retained Metal device experiment](benchmarks/2026-10-07-device-reuse.md) isolates repeated device lookup, compares a retained handle with fresh per-request buffers, and defines the next production qualification.\n\n',1)
files={index:readme.encode(),'Documentation/EngineeringNotes/benchmarks/2026-10-07-device-reuse.md':report.encode()}
prefix='Documentation/EngineeringNotes/archive/2026-10-07/device-reuse/'
for p in sorted((out/'comparison').iterdir()):
 if not p.is_file():continue
 key=prefix+'comparison/'+p.name
 if p.suffix=='.json' and not p.name.endswith('-command.json') and p.name not in ['summary.json','provenance.json']:files[key+'.gz']=gzip.compress(p.read_bytes(),mtime=0)
 else:files[key]=p.read_bytes()
for p in sorted(out.iterdir()):
 if p.is_file() and p.suffix in ['.json','.log']:
  key=prefix+p.name
  if p.suffix=='.log' or p.name.startswith('smoke-') and not p.name.endswith('-command.json'):files[key+'.gz']=gzip.compress(p.read_bytes(),mtime=0)
  else:files[key]=p.read_bytes()
for name in ['smoke-device-reuse.py','run-device-reuse-tests.py','commit-device-reuse.py','record-device-reuse.py']:files[prefix+name]=Path('/private/tmp',name).read_bytes()
env=dict(os.environ,GIT_INDEX_FILE=str(out/'notes.index'));git('read-tree',base,env=env)
for path,data in files.items():
 blob=git('hash-object','-w','--stdin',input=data);git('update-index','--add','--cacheinfo',f'100644,{blob},{path}',env=env)
git('diff','--cached','--check',base,env=env)
assert set(git('diff','--cached','--name-only',base,env=env).splitlines())==set(files)
n=git('commit-tree',git('write-tree',env=env),'-p',base,input=b'docs(memory): record retained Metal device comparison\n');git('update-ref',branch,n,base)
(out/'notes-commit.json').write_text(json.dumps({'base':base,'commit':n,'files':len(files),'archive_bytes':sum(map(len,files.values()))},indent=2)+'\n')
print(n)
