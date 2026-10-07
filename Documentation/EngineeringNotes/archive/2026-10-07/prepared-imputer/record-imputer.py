from pathlib import Path
import gzip,hashlib,json,os,statistics,subprocess
repo=Path('/Users/crabel/Documents/src/SwiftSci')
out=Path('/Users/crabel/local-ai/spl/swiftsci/prepared-imputer-20261007')
run=out/'comparison'
s=json.loads((run/'summary.json').read_text())
commit=json.loads((out/'commit.json').read_text())
provenance=json.loads((run/'provenance.json').read_text())
rows=[];pairs=[]
for case in ['small','medium','large']:
 d={p:sorted([x for x in s if x['case']==case and x['path']==p],key=lambda x:x['round']) for p in ['rows','copy','owned']}
 rates={p:statistics.median(x['requests_per_second'] for x in items) for p,items in d.items()}
 memory={p:statistics.median(x['rss_mib'] for x in items) for p,items in d.items()}
 ratios=[d['owned'][i]['requests_per_second']/d['rows'][i]['requests_per_second'] for i in range(3)]
 rows.append(f"| {case} | {rates['rows']:.1f} | {rates['copy']:.1f} | {rates['owned']:.1f} | {statistics.median(ratios):.2f}x | {memory['rows']:.1f} | {memory['copy']:.1f} | {memory['owned']:.1f} |")
 for reference in ['rows','copy']:
  for i in range(3):
   old,new=d[reference][i],d['owned'][i]
   pairs.append({'case':case,'reference':reference,'round':i,'throughput_ratio':new['requests_per_second']/old['requests_per_second'],'rss_reduction_percent':100*(1-new['rss_mib']/old['rss_mib'])})
validation={'implementation_commit':commit['commit'],'parent':commit['base'],'workers':27,'requests':304416,'selected_release_tests_passed':872,'selected_release_tests_failed':0,'optional_skips':2,'controller_tests_passed':12,'red_ownership_failures':3,'complete_output_hashes_match':True,'workers_remaining':0,'paired_results':pairs,'decision':'Keep native prepared imputation and consuming storage. Preserve the prepared regression finite-input boundary.','limitations':['Same-executable explicit row reference, not a separate parent binary','Three rounds on one actively used Apple M4 Max host','Measurement includes input allocation, missing marking, exact validation and hashing','CPU preprocessing only; no training-time or GPU inference performance claim','Selected nine-module Release test suite, not full-library or sanitizer certification']}
(out/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
report=f'''# Prepared imputer integration and CPU comparison

Date: 2026-10-07

## Decision and scope

Keep native prepared-column fitting and consuming transforms for `Imputer`. This removes row-array conversion from preprocessing pipelines containing an imputer and a native scaler. Unique columns reuse their buffers; shared columns detach only when replacement is needed. Clean columns remain shared. Swift copy-on-write protects retained batches, arrays and matrices.

Implementation commit: `{commit['commit']}` on `codex/retained-memory-accounting-trial`, following `{commit['base']}`. This increment remains local. The primary checkout was not switched. This report and measured evidence belong only to `codex/engineering-notes`.

Mean, median, most-frequent and constant strategies share the existing row implementation's statistic formulas. Arithmetic order, ties, all-missing fallback, empty input, failed-fit state, names and original row indices retain their existing behavior. The output clears missing flags, including when an explicitly chosen fill statistic is NaN.

## Integration boundary

The prepared `RegressionPipeline` validates finite inputs before running its transformers. This change preserves that policy. Callers must first fit a preprocessing `Pipeline` on training data, then use its fitted imputer and scaler to clean training and held-out batches before passing them to prepared regression. A constant NaN or a statistic involving infinities can still produce an input that regression rejects.

The public prepared regression documentation now explains this sequence. Moving imputation inside the regression boundary would be a separate API-policy decision and needs its own tests. The present measurements do not establish GPU inference or training performance.

## Validation

Three ownership assertions failed before implementation. Seven new test functions cover native nested dispatch, unique buffer reuse, shared clean columns, retained matrices, internal aliases, strategy edges, missing flags, provenance, failed refits, empty/error behavior and concurrent readers.

The final selected Release run passed 872 tests, with zero failures and two optional skips. It includes SwiftDataFrame, SwiftStats, SwiftPreprocessing, SwiftML, SwiftCluster, SwiftOptimize, SwiftExplain, SwiftNLP and benchmark support. This is not full-library or sanitizer certification. Optional tokenizer assets remain unavailable; the existing MNIST fixture early-return behavior also limits that test's evidence.

An earlier broad run failed a pointer-identity assertion because its literal array fixture could use static shared storage. The fixture now constructs dynamic arrays before asserting unique ownership. A focused rerun passed all seven tests, then the complete selected run passed. The production implementation did not change during that correction. Both earlier and final evidence are retained and labeled.

Twelve controller tests passed, covering output contracts, memory checks and worker cleanup. All 27 comparison workers completed 304,416 measured requests. Every output element matched an independent exact formula, and complete output hashes matched across paths and rounds. Consumed paths checked each column's buffer address. All worker processes exited. MLX active and cached allocations stayed at zero because this workload is CPU-only.

## Method

The public preprocessing pipeline contains `Imputer` with mean replacement, followed by `MinMaxScaler`. Fitting uses training-only data. Held-out fixtures include complete columns, numeric NaNs and entries marked missing. Expected transformed values are independently specified as an exact binary fraction or 0.5 for replaced entries.

The row reference explicitly materializes rows and invokes the existing row pipeline in the same executable. It represents the former whole-pipeline compatibility path, not a separate build of the parent commit. The copied prepared path retains its source through validation. The consumed path transfers ownership and verifies buffer reuse.

Three rounds ran serially in fresh processes; case and path order reversed in the middle round. Small is 64 rows by 3 columns with 32,768 requests per worker. Medium is 4,096 by 17 with 1,024 requests. Large is 65,535 by 65 with 32 requests. Timing includes fixture creation, missing marking, transformation, exact validation and hashing. It excludes fitting, warmup, JSON serialization and final cleanup.

Each worker has a 180-second deadline and a 2 GiB memory bound. The controller checks memory pressure before launch and owns child process groups through exit. There is no cache flush or allocator pressure relief. Ordinary activity on the user's computer was allowed.

## Results

Rates and RSS are medians of three fresh workers. The speed ratio is the median of within-round consumed/row ratios. RSS is sampled after requests and includes allocator retention; lifetime peak is recorded separately, and happened to match the reported RSS at these snapshots.

| Case | Rows requests/s | Copied columns requests/s | Consumed columns requests/s | Consumed/rows speed | Rows RSS MiB | Copied RSS MiB | Consumed RSS MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

Across the three rounds, consumed throughput was 5.05 to 5.24 times the row path for small inputs, 3.03 to 3.08 times for medium, and 2.34 to 2.39 times for large. Large consumed RSS was 93.0 to 95.1 MiB, compared with 267.7 to 289.5 MiB for rows, a 65% to 67% reduction.

Against copied prepared columns, consuming improved throughput by 7.1% to 9.8% for small, 2.2% to 3.4% for medium, and 1.7% to 6.3% for large. Large RSS fell another 41% to 49%. Small RSS stayed around 19 MiB for all paths. Avoiding row materialization accounts for most of the measured speed benefit; ownership transfer provides an additional memory benefit.

These observations support the implementation without introducing a size threshold. They do not establish a universal speedup, formal statistical equivalence, or a complete production baseline. No Python comparator was run for this increment.

## Reproduction and evidence

The host is Apple M4 Max with 128 GiB unified memory and macOS 27.0 build 26A428. The arm64 Release worker uses the existing pinned dependencies, coverage disabled, safe Metal math and precise FP32 settings. No macOS 14 runtime was exercised.

Worker SHA-256: `{provenance['binary_sha256']}`.

Run `Benchmarks/Tools/compare_imputer_pipeline.py` with `--worker`, a new `--output` directory and `--rounds 3`. Commands, all production source fingerprints, worker outputs and test summaries are preserved below. Logs are compressed without loss. Xcode result bundles remain in the local evidence directory.

- [Measured summary](../archive/2026-10-07/prepared-imputer/comparison/summary.json)
- [Source and binary fingerprints](../archive/2026-10-07/prepared-imputer/comparison/provenance.json)
- [Paired results and validation](../archive/2026-10-07/prepared-imputer/validation.json)
- [Final selected Release result](../archive/2026-10-07/prepared-imputer/verified-release-summary.json)
- [Implementation file fingerprints](../archive/2026-10-07/prepared-imputer/commit.json)
'''
assert '\u2014' not in report
(out/'REPORT.md').write_text(report)
def git(*args,input=None,env=None):
 return subprocess.check_output(['git','-C',str(repo),*args],input=input,env=env).decode().strip()
base='e5a42492bc024e6ba04c4989dbf397d1388f7e20'
branch='refs/heads/codex/engineering-notes'
assert git('rev-parse',branch)==base
assert git('rev-parse','codex/retained-memory-accounting-trial')==commit['commit']
assert git('rev-parse','HEAD')=='6e10f5833961d6813cc65b0491fe622c83c55a5d'
assert not git('status','--porcelain=v1','--untracked-files=no')
index='Documentation/EngineeringNotes/README.md'
readme=git('show',base+':'+index)+'\n'
assert '## Start here\n\n' in readme
readme=readme.replace('## Start here\n\n','## Start here\n\n- [Prepared imputer integration](benchmarks/2026-10-07-prepared-imputer-integration.md) records native column reuse, the regression finite-input boundary, 872 selected Release test passes and the CPU comparison.\n\n',1)
files={index:readme.encode(),'Documentation/EngineeringNotes/benchmarks/2026-10-07-prepared-imputer-integration.md':report.encode()}
prefix='Documentation/EngineeringNotes/archive/2026-10-07/prepared-imputer/'
for p in sorted(run.iterdir()):
 if p.is_file():files[prefix+'comparison/'+p.name]=p.read_bytes()
for p in sorted(out.iterdir()):
 if p.is_file() and p.suffix in ['.json','.log']:
  key=prefix+p.name
  if p.suffix=='.log':files[key+'.gz']=gzip.compress(p.read_bytes(),mtime=0)
  else:files[key]=p.read_bytes()
# Keep the report generator and commit verification reproducible, outside source branches.
for name in ['commit-imputer.py','record-imputer.py']:
 files[prefix+name]=Path('/private/tmp',name).read_bytes()
env=dict(os.environ,GIT_INDEX_FILE=str(out/'notes.index'))
git('read-tree',base,env=env)
for path,data in files.items():
 blob=git('hash-object','-w','--stdin',input=data)
 git('update-index','--add','--cacheinfo',f'100644,{blob},{path}',env=env)
git('diff','--cached','--check',base,env=env)
assert set(git('diff','--cached','--name-only',base,env=env).splitlines())==set(files)
c=git('commit-tree',git('write-tree',env=env),'-p',base,input=b'docs(memory): record prepared imputer integration and comparison\n')
git('update-ref',branch,c,base)
(out/'notes-commit.json').write_text(json.dumps({'base':base,'commit':c,'files':len(files),'archive_bytes':sum(map(len,files.values()))},indent=2)+'\n')
print(c)
print('\n'.join(rows))
print(f'Archived {len(files)} files, {sum(map(len,files.values()))} bytes')
