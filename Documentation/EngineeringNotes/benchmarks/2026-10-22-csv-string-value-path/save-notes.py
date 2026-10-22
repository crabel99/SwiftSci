from pathlib import Path
import difflib,gzip,hashlib,json,re,shutil,subprocess,tarfile
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');N=Path('/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018');P=Path('/private/tmp/swiftsci-csv-local-builder-20261022')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads((R/'source-state.json').read_text());assert source['head']=='c906c3fbbb0baf1357438a7079921a6448e0c9e5'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()==source['head']
assert all(h(S/p)==sha for p,sha in source['sources'].items())
assert not subprocess.check_output(['git','status','--porcelain'],cwd=N)
assert subprocess.check_output(['git','branch','--show-current'],cwd=N,text=True).strip()=='codex/engineering-notes'
for name,count in [('reproduction',320),('screening',832)]:
 rows=[json.loads(line) for line in (R/name/'workers.jsonl').read_text().splitlines()]
 assert len(rows)==count and all(r['validated'] for r in rows)
assembly=json.loads((R/'assembly/summary.json').read_text());assert assembly[0]['sections']==assembly[1]['sections']
D=N/'Documentation/EngineeringNotes/benchmarks/2026-10-22-csv-string-value-path';D.mkdir(exist_ok=False)
for p in [*R.glob('*.py'),*R.glob('*.swift'),*R.glob('*.json')]:shutil.copy2(p,D/p.name)
for group in ['reproduction','screening','assembly']:
 out=D/group;out.mkdir()
 for p in (R/group).iterdir():
  if not p.is_file():continue
  if p.suffix in ['.jsonl','.txt']:
   with gzip.open(out/(p.name+'.gz'),'wb') as f:f.write(p.read_bytes())
   assert gzip.decompress((out/(p.name+'.gz')).read_bytes())==p.read_bytes()
  else:shutil.copy2(p,out/p.name)
roots={e:R/'build'/e for e in ['control','hashed-optional','both-optional']}
roots.update(production=P/'build/production',baseline=Path('/private/tmp/swiftsci-csv-number-loop-20261022/build/production'))
for label,root in roots.items():
 out=D/'build-receipts'/label;out.mkdir(parents=True)
 for name in ['build.json','module-signature.json','StreamProbe.build.json']:
  if (root/name).is_file():shutil.copy2(root/name,out/name)
 for p in root.glob('*.log'):
  with gzip.open(out/(p.name+'.gz'),'wb') as f:f.write(p.read_bytes())
patches=R/'trial-patches';patches.mkdir(exist_ok=True)
base=R/'variants/control/Sources/SwiftDataFrame/IO/CSVColumnConversion.swift'
for variant in ['hashed-optional','both-optional']:
 file=R/'variants'/variant/'Sources/SwiftDataFrame/IO/CSVColumnConversion.swift'
 (patches/(variant+'.patch')).write_text(''.join(difflib.unified_diff(base.read_text().splitlines(keepends=True),file.read_text().splitlines(keepends=True),fromfile='a/Sources/SwiftDataFrame/IO/CSVColumnConversion.swift',tofile='b/Sources/SwiftDataFrame/IO/CSVColumnConversion.swift')))
plans=[json.loads((R/group/'plan.json').read_text()) for group in ['reproduction','screening']]
contracts={}
for plan in plans:
 for case in plan['cases']:
  path=Path(case[2] if len(case)==3 and case[0] in ['eager','stream'] else case[1]);contracts[path.name]=path
with tarfile.open(D/'experiments.tar.gz','w:gz') as t:
 t.add(R/'variants',arcname='variants');t.add(patches,arcname='trial-patches')
 for name,path in sorted(contracts.items()):
  t.add(path,arcname='input-contracts/'+name);inp=json.loads(path.read_text());data=Path(inp['path'])
  assert h(data)==inp.get('source_sha256',inp.get('sha256'))
  if '/text-inputs/' in str(data) or '/long-key-inputs/' in str(data):t.add(data,arcname='generated-inputs/'+data.name)
head=source['head'];flags=json.loads((R/'screening/review-flags.json').read_text());assert len(flags)==2
lines=['# CSV String optional-return experiment','','Keep `codex/csv-local-batch-builder` at `'+head+'` unchanged. Neither optional-return trial provides a consistent resource improvement. No source branch, production commit, push, or PR was created for this experiment.','','This follows the [worker-local builder experiment](../2026-10-22-csv-local-batch-builder/README.md). Its initial small-file default-token flag remains part of that record. This follow-up does not remove or waive it.','','## Hypotheses','','1. If classified-result conversion costs CPU on the String path, an explicit optional-return decoder reduces that cost.','2. If the optimizer already removes the conversion, the direct return provides no useful instruction change.','3. If setup dominates short reads, small timing differences do not persist across matched repetitions.','','## Reproduction','','The initial repeat uses frozen Array baseline `680ac74b96ab6c6968d83a9511ebdce69d30093b` and current builder head `'+head+'`. Five cases run under both column policies, with 16 observations per implementation and policy. All 320 workers validate complete native output. There are no CPU or memory review flags. The previously reported large parallel default-token penalty is not reproduced.','','| Input | Policy | Baseline CPU ms | Current CPU ms | CPU change |','|---|---|---:|---:|---:|']
repro=json.loads((R/'reproduction/summary.json').read_text())
for a in repro:
 if a['engine'] not in ['parallel','serial']:continue
 b=next(b for b in repro if b['engine']=='parent-'+a['engine'] and b['case']==a['case']);x=a['medians']['total_cpu_ns'];y=b['medians']['total_cpu_ns'];lines.append(f"| {a['case']} | {a['engine']} | {y/1e6:.3f} | {x/1e6:.3f} | {(x/y-1)*100:+.1f}% |")
lines+=['','## Trials and methods','','The screening matrix compares four executables. `production` is the frozen binary from the preceding builder study. `control` rebuilds exactly the same sources in a new snapshot. `hashed-optional` gives only `CSVStringDecoder` an explicit `decodeValue` method. `both-optional` also changes `CSVSmallStringDecoder`. Each classified `decode` method wraps that optional result, so each field is still parsed once.','','All variants retain the same null tokens, native String equality, parser, capacity, workers, and public API. No raw-byte null classifier or new lookup threshold is added. The proposed simplification removes a source-level result conversion rather than adding another parsing layer.','','Thirteen input/scope combinations run with explicit parallel and serial conversion. Each implementation receives eight observations in rotated and reversed order. All 832 workers validate full native values, types, null positions, and row and column order. Streaming uses a separate complete untimed read for validation. Inputs include default, one-token, two-token, 17-token and 2,048-token sets, long keys, mixed columns, all-String columns, air quality, and household data.','','Every implementation receives the same `argv[0]` within its scope. Input bytes are warmed, power is AC, and the existing production worker environment preserves native scheduling and hash randomization. All build and link processes finish before screening starts. Assembly inspection starts only after screening completes. No build, test, or profiler overlaps accepted timing. Host activity outside this task remains uncontrolled.','','CPU means process user-plus-system time during the complete read. Peak RSS includes the entire worker and is not an allocation count. Elapsed time is recorded separately. These measurements do not establish energy, FLOPs, cache behavior, or hardware contention.','','## Generated code','','The unchanged-source control and hashed-only trial have identical bytes in every Mach-O `__TEXT` section, including instructions and constants. Their instruction section is 1,011,924 bytes with SHA-256 `4093ef42f2c7aea8bf95ad3b0abd69d03301285736d2e929b65b67cf41c871c0`. The explicit hashed optional method therefore does not remove emitted instructions on this compiler. Hypothesis 1 is rejected for that trial.','','The two-decoder trial changes code placement and emits a separate compact-record small-String append function. Its instruction section is 1,012,012 bytes. Static size and instruction-entry counts do not measure executed work. No repeatable performance benefit follows from that layout change in this screen.','','## Results and decision','','The household reference results are below. See [all 104 implementation/policy medians](screening-results.md) for complete CPU, elapsed, and peak-RSS measurements.','','| Scope | Policy | Production CPU ms | Unchanged rebuild CPU ms | Hashed optional CPU ms | Both optional CPU ms |','|---|---|---:|---:|---:|---:|']
screen=json.loads((R/'screening/summary.json').read_text())
for scope in ['eager','stream']:
 for policy in ['parallel','serial']:
  vals={e:next(x for x in screen if x['scope']==scope and x['case']=='energy' and x['policy']==policy and x['engine']==e)['medians']['total_cpu_ns']/1e6 for e in ['production','control','hashed-optional','both-optional']}
  lines.append('| '+scope+' | '+policy+' | '+' | '.join(f'{vals[e]:.3f}' for e in ['production','control','hashed-optional','both-optional'])+' |')
lines+=['','Small-case differences reverse across cases and policies. Two CPU review flags remain in the screen: serial 17-token all-String input is 11.7% higher for the unchanged rebuild and 21.8% higher for hashed-only, each against the frozen production binary. The unchanged rebuild and hashed-only trial have identical instruction and constant sections. These flags do not establish that optional return caused the cost. They show why timing alone cannot justify this change.','','Neither trial has a consistent CPU benefit or a demonstrated memory benefit. The largest median peak-RSS increase against production is below 0.73 MiB. That is not proof of identical allocation behavior. Keep all flags and measurements, reject both optional-return trials, and retain the existing builder head.','','No new production tests, sanitizer run, grammar qualification, or standardized benchmark run is claimed. They would qualify a selected implementation, and this screen selects none. The prior builder test results remain attached to their original head and report.','','## Next investigation','','Investigate the cost of hashed membership and String construction separately on actual reference inputs before proposing another representation. Preserve native String equality, Unicode normalization behavior, invalid-UTF-8 repair, and escaped-field semantics. The evidence here rules out source-level result conversion as a useful hashed-path optimization. It does not prove a physical cache or scheduling mechanism.','','## Evidence','','- [Source state and hashes](source-state.json)','- [Reproduction plan](reproduction/plan.json), [medians](reproduction/summary.json), and [flags](reproduction/review-flags.json)','- [Screening plan](screening/plan.json), [medians](screening/summary.json), and [flags](screening/review-flags.json)','- [Complete resource table](screening-results.md)','- [Assembly hashes and counts](assembly/summary.json)','- [Preserved source variants, patches, and input contracts](experiments.tar.gz)','- [Artifact hashes](artifact-sha256.json)','','`build.py`, `link-variants.py`, `screen.py`, `reproduce.py`, and `inspect-code.py` retain executable procedures. `experiments.tar.gz` preserves all three module snapshots and both trial patches. Reference CSV bytes remain with their existing dataset owner; contracts retain their byte hashes and full expected native output. Generated text inputs are included. Recreate the recorded paths or adapt paths while preserving hashes, schemas, policies, and validation.','']
(D/'README.md').write_text('\n'.join(lines))
table=['# Complete decoder screening results','','Each median uses eight fresh-process observations. Native output validation passes for every observation. Review flags remain in the [study record](README.md).','','| Scope | Case | Policy | Implementation | CPU ms | Elapsed ms | Peak RSS MiB |','|---|---|---|---|---:|---:|---:|']
for a in screen:
 x=a['medians'];memory='peak_after_bytes' if a['scope']=='stream' else 'process_peak_held_bytes';table.append(f"| {a['scope']} | {a['case']} | {a['policy']} | {a['engine']} | {x['total_cpu_ns']/1e6:.3f} | {x['total_ns']/1e6:.3f} | {x[memory]/2**20:.2f} |")
(D/'screening-results.md').write_text('\n'.join(table)+'\n')
files={str(p.relative_to(D)):h(p) for p in D.rglob('*') if p.is_file() and p.name!='artifact-sha256.json'};(D/'artifact-sha256.json').write_text(json.dumps(files,indent=2)+'\n')
for p in D.rglob('*.md'):
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):assert (p.parent/target).exists(),(p,target)
assert all(h(D/p)==sha for p,sha in files.items())
index=N/'Documentation/EngineeringNotes/README.md';text=index.read_text();anchor='## Start here\n\n';assert text.count(anchor)==1
text=text.replace(anchor,anchor+'- [CSV String optional-return trial](benchmarks/2026-10-22-csv-string-value-path/README.md) rules out redundant result conversion with identical generated instructions, retains 1,152 validated observations, and rejects both trials without a source change.\n\n');index.write_text(text)
print(D,len(files),'verified artifacts')
