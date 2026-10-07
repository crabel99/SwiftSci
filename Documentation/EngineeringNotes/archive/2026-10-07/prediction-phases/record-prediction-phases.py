from pathlib import Path
import gzip,json,statistics,hashlib,subprocess,os
repo=Path('/Users/crabel/Documents/src/SwiftSci');out=Path('/Users/crabel/local-ai/spl/swiftsci/prediction-phases-20261007')
c=json.loads((out/'commit.json').read_text());s=json.loads((out/'prediction/summary.json').read_text());lat=json.loads((out/'latency/summary.json').read_text());old=json.loads((out.parent/'small-imputed-latency-20261007/phases/summary.json').read_text());prov=json.loads((out/'prediction/provenance.json').read_text())
rows=[];summaries=[]
keys=['actor_wait','validation','device_allocation','packing','import','graph','completion','readback','scope_cleanup','actor_body','awaited_prediction']
for key in keys:
 values=[]
 for slots in [1,2]:
  a=[b for b in s if b['slots']==slots and b['decomposed']]
  values.append(statistics.median(b['phases'][key]['mean_us'] for b in a))
 rows.append(f'| {key} | {values[0]:.3f} | {values[1]:.3f} |')
 summaries.append({'phase':key,'one_slot_us':values[0],'two_slots_us':values[1]})
public={slots:statistics.median(b['phases']['awaited_prediction']['mean_us'] for b in s if b['slots']==slots and not b['decomposed']) for slots in [1,2]}
comparisons=[]
for route in ['preprocessing','direct','pipeline']:
 for slots in [1,2]:
  for owned in [False,True]:
   a=[b for b in lat if b['route']==route and b['slots']==slots and b['owned']==owned]
   b=[b for b in old if b['route']==route and b['slots']==slots and b['owned']==owned]
   comparisons.append({'route':route,'slots':slots,'owned':owned,'before_us':statistics.median(r['phases']['validation']['mean_us'] for r in b),'after_us':statistics.median(r['phases']['validation']['mean_us'] for r in a)})
validation={'commit':c['commit'],'parent':c['base'],'production_changes':False,'focused_release_tests_passed':2,'controller_tests_passed':25,'smoke_workers':16,'smoke_requests':2080,'prediction_workers':4,'prediction_requests':49152,'latency_workers':12,'latency_requests':294912,'complete_public_outputs_match':True,'historical_output_hashes_match':True,'pipeline_request_schema_preserved':True,'maximum_absolute_error':max(b['max_error'] for b in s),'request_reservations_drained':True,'gpu_owners_returned_to_baseline':True,'final_gpu_active_and_cache_zero':True,'workers_remaining':0,'phase_summary':summaries,'validation_comparison':comparisons,'decision':'Keep production dispatch and import policy unchanged. Packing/import are minor for 64x3 inputs. Next separate device lookup from allocation and trial reuse of the Metal device handle before adding storage pooling.'}
(out/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
report=f'''# GPU prediction phases and benchmark hash encoding

Date: 2026-10-07

## Finding and decision

For 64-row, 3-column GPU predictions, packing and MLX import together account for about 1% of the diagnostic actor's body duration. Host submission and GPU completion account for about 65%, and Metal device/buffer setup about 22%. These are medians of per-block shares. Further packing optimization is unlikely to materially change this small-input case.

With two admitted requests, actor waiting grows from about 0.08 to 176 microseconds, while the actor body stays near 181 microseconds. The second request waits for the serialized model execution. More admitted requests increase individual latency here without removing fixed execution costs. This is not a claim that all models or batch sizes behave the same way.

The public API control measures about {public[1]:.1f} microseconds with one slot and {public[2]:.1f} with two. The separately timed diagnostic actor measures about 181.6 and 358.5 microseconds including waits and resumption. Explicit evaluation, clocks, dictionary updates and the mirror implementation perturb execution. Their difference must not be interpreted as a production regression or a precise price for instrumentation.

Keep the current production dispatch and logical-extent import policy. The next targeted experiment should separate device lookup from buffer allocation, then compare a reused Metal device handle. Do not add buffer pooling, an ownership size threshold or a CPU/GPU crossover rule based on this small-input diagnostic alone.

## Scope

Implementation commit `{c['commit']}` follows `{c['base']}` on `codex/retained-memory-accounting-trial`. It changes benchmark code only. The primary checkout stays at `6e10f5833961d6813cc65b0491fe622c83c55a5d`; nothing was pushed.

`pipeline-service` and `imputed-latency` now retain the 32 raw SHA-256 bytes per request and format hexadecimal text after the measured window. Every prediction is still checked numerically and fully hashed. The pipeline JSON fields and hexadecimal digest values are unchanged. The latency workflow also preserves its historical aggregate format, which hashes concatenated hexadecimal request digests.

The new prediction-phase diagnostic hashes concatenated raw request digests instead. Its aggregate hashes compare public and decomposed routes within this diagnostic. They are not interchangeable with latency-workflow aggregate hashes. Both controllers record source and binary fingerprints.

## Experiment

The diagnostic constructs missing and shifted held-out observations and consumes them through the existing training-only imputation and minmax preparation. Each request has 64 rows and 3 columns. Identical request IDs alternate between the public GPU model and a benchmark-local actor. Alternate pairs reverse route order. Each process runs six pairs of 1,024 requests per route. Two fresh processes run each slot count, reversing slot order in the second round.

The actor calls production `PreparedFloatPacking.initialize` and `ScopedGPURead.withBuffer`, and uses the same Float weights, bias, matmul and add operations as the public model. It preserves logical-extent import and its synchronous ownership scope. These 768-byte inputs use the existing MLX copying import path. All outputs are evaluated and converted to owned Double arrays before the borrowed input scope closes.

This is a diagnostic mirror, not instrumentation within the production model. Actor wait includes executor scheduling from dispatch to actor entry. Completion includes host graph evaluation/submission and GPU synchronization; it is not pure GPU kernel time. Readback converts the completed Float output to Double. Scope cleanup includes the final scoped synchronization, owner release and autorelease-pool drainage. Concurrent request intervals overlap and must not be summed as elapsed wall time.

## Phase measurements

Durations are microseconds. Each cell is the median of 12 per-block mean durations. The actor-body and awaited rows contain the other phases; they are not additional work. Timing gaps include clock and dictionary bookkeeping.

| Host-clock phase | One slot, µs | Two slots, µs |
| --- | ---: | ---: |
{chr(10).join(rows)}

The observed actor-body block means range from 170.5 to 312.3 microseconds with one slot and 179.0 to 196.6 with two. Ordinary host activity remains a source of variability. This report does not claim a fixed universal crossover or equivalence between the diagnostic and production execution schedules.

## Hash-formatting correction

The same latency workloads were repeated in 12 fresh workers, covering 294,912 requests. Every aggregate hash matches its prior record across route, ownership, slot count, pair and repetition. Six additional latency smoke workers also preserve their historical hashes. Eight pipeline smoke workers preserve request schemas and output hashes for standard scaling, minmax scaling, and imputation/minmax with both small and mixed large inputs.

The recorded validation phase fell from approximately 28 to 48 microseconds to 0.87 to 1.25 microseconds across the same control combinations. Raw hashing and numerical checks remain inside validation. Hexadecimal text conversion moves outside timing. These runs were not interleaved against the old binary, so this comparison is not a controlled claim about total service throughput. Public prediction timings also differ between recording sessions and must not be attributed solely to this benchmark correction.

Historical throughput measurements include the old text-formatting cost. Preserve their fingerprints and timing contract. New records exclude that cost and should be identified accordingly when comparing complete workflows.

## Verification and resource handling

The final Release build passes both focused public-workflow integration tests. Twenty-five controller tests pass, including malformed phase rejection, public-output mismatch, invalid memory samples and undrained ownership. The previous broad production suite belongs to the parent work and was not rerun for this benchmark-only change.

Sixteen final smoke workers complete 2,080 requests. Four phase workers complete 49,152 requests; twelve latency workers complete 294,912. Public and decomposed output bytes match for every request. The largest absolute error in the phase run is `{validation['maximum_absolute_error']:.17g}`, below the unchanged `1e-4` analytic bound.

Every block drains admission reservations and returns MLX active allocation to the two fitted models' baseline. Final model release and cache clearing return MLX active and cached allocations to zero. All workers exit. Phase-worker sampled RSS stays below 27 MiB. These bounded checks do not certify the absence of every possible CPU or GPU leak.

The controller owns each child process, enforces a 180-second deadline and checks normal memory pressure before launch. Admission and cache limits remain 256 MiB, with a 16 MiB conservative estimate per request. No cache clearing occurs between measured blocks. No unrelated application was stopped.

Behavioral review found no scope or ownership issue. Standards review suggested naming the historical hexadecimal aggregate payload; that change was accepted. Review also caught a potential overlap between actor-wait and body clocks. Wait now ends at the captured actor-entry instant, before the final rebuild and measurements. All phase-sum checks pass.

## Evidence

Host: Apple M4 Max, 128 GiB unified memory, macOS 27.0 build 26A428. Release arm64, coverage disabled, existing pinned dependencies, precise Float settings. No macOS 14 runtime was exercised.

Binary SHA-256: `{prov['binary_sha256']}`.

- [Prediction phase summary](../archive/2026-10-07/prediction-phases/prediction/summary.json)
- [Prediction source fingerprints](../archive/2026-10-07/prediction-phases/prediction/provenance.json)
- [Revised latency summary](../archive/2026-10-07/prediction-phases/latency/summary.json)
- [Validation and hash-formatting comparison](../archive/2026-10-07/prediction-phases/validation.json)
- [Previous small-request diagnosis](2026-10-07-small-imputed-latency.md)

Raw worker records and logs are losslessly compressed in the archive. Xcode result bundles remain in the local evidence directory.
'''
assert '\u2014' not in report
(out/'REPORT.md').write_text(report)
def git(*args,input=None,env=None):return subprocess.check_output(['git','-C',str(repo),*args],input=input,env=env).decode().strip()
base='122c0834998a1d26999bd4b3b595b2319b0f932f';branch='refs/heads/codex/engineering-notes'
assert git('rev-parse',branch)==base and git('rev-parse','codex/retained-memory-accounting-trial')==c['commit']
assert git('rev-parse','HEAD')=='6e10f5833961d6813cc65b0491fe622c83c55a5d'
index='Documentation/EngineeringNotes/README.md';readme=git('show',base+':'+index)+'\n';assert '## Start here\n\n' in readme
readme=readme.replace('## Start here\n\n','## Start here\n\n- [GPU prediction phases](benchmarks/2026-10-07-prediction-phases.md) separates small-input packing from device setup, completion and actor waiting, and records the benchmark hash-formatting correction.\n\n',1)
files={index:readme.encode(),'Documentation/EngineeringNotes/benchmarks/2026-10-07-prediction-phases.md':report.encode()}
prefix='Documentation/EngineeringNotes/archive/2026-10-07/prediction-phases/'
for directory in ['prediction','latency']:
 for p in sorted((out/directory).iterdir()):
  if not p.is_file():continue
  key=prefix+directory+'/'+p.name
  if p.suffix=='.json' and not p.name.endswith('-command.json') and p.name not in ['summary.json','provenance.json']:
   files[key+'.gz']=gzip.compress(p.read_bytes(),mtime=0)
  else:files[key]=p.read_bytes()
for p in sorted(out.iterdir()):
 if p.is_file() and p.suffix in ['.json','.log']:
  key=prefix+p.name
  if p.suffix=='.log' or p.name.startswith('smoke-') and not p.name.endswith('-command.json'):files[key+'.gz']=gzip.compress(p.read_bytes(),mtime=0)
  else:files[key]=p.read_bytes()
for name in ['check-prediction-phases.py','check-prediction-pipeline.py','run-prediction-phases-tests.py','commit-prediction-phases.py','record-prediction-phases.py']:files[prefix+name]=Path('/private/tmp',name).read_bytes()
env=dict(os.environ,GIT_INDEX_FILE=str(out/'notes.index'));git('read-tree',base,env=env)
for path,data in files.items():
 blob=git('hash-object','-w','--stdin',input=data);git('update-index','--add','--cacheinfo',f'100644,{blob},{path}',env=env)
git('diff','--cached','--check',base,env=env)
assert set(git('diff','--cached','--name-only',base,env=env).splitlines())==set(files)
n=git('commit-tree',git('write-tree',env=env),'-p',base,input=b'docs(memory): record prediction phase measurements and hash overhead\n');git('update-ref',branch,n,base)
(out/'notes-commit.json').write_text(json.dumps({'base':base,'commit':n,'files':len(files),'archive_bytes':sum(map(len,files.values()))},indent=2)+'\n')
print(n)
