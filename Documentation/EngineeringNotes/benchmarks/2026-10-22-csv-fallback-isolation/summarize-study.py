from pathlib import Path
import json,statistics as st,hashlib,subprocess
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021')
comparisons=[]
for label in ['acceptance','mode-controls','text-controls','long-key-controls']:
 data=json.loads((R/label/'summary.json').read_text());pairs=[]
 for a in data:
  if a['engine'] not in ['parallel','serial']:continue
  keys=[k for k in ['case','scope','mode'] if k in a];b=next(b for b in data if b['engine']=='parent-'+a['engine'] and all(b[k]==a[k] for k in keys));m='peak_after_bytes' if a.get('scope')=='stream' else 'process_peak_held_bytes'
  p=dict(stage=label,**{k:a[k] for k in keys},policy=a['engine'],cpu_before_ms=b['medians']['total_cpu_ns']/1e6,cpu_after_ms=a['medians']['total_cpu_ns']/1e6,cpu_change_percent=100*(a['medians']['total_cpu_ns']/b['medians']['total_cpu_ns']-1),elapsed_before_ms=b['medians']['total_ns']/1e6,elapsed_after_ms=a['medians']['total_ns']/1e6,peak_before_mib=b['medians'][m]/2**20,peak_after_mib=a['medians'][m]/2**20);pairs.append(p);comparisons.append(p)
 lines=['# '+label.replace('-',' ')+' results','','CPU is process user-plus-system time. Peak RSS is a process high-water mark, not allocations. Elapsed time is separate.','','| Scope and case | Policy | Parent CPU ms | Metadata CPU ms | CPU change | Elapsed before / after ms | Peak before / after MiB |','|---|---|---:|---:|---:|---:|---:|']
 for a in pairs:lines.append(f"| {a.get('scope','eager')} {a['case']} | {a['policy']} | {a['cpu_before_ms']:.3f} | {a['cpu_after_ms']:.3f} | {a['cpu_change_percent']:+.1f}% | {a['elapsed_before_ms']:.3f} / {a['elapsed_after_ms']:.3f} | {a['peak_before_mib']:.2f} / {a['peak_after_mib']:.2f} |")
 (R/(label+'.md')).write_text('\n'.join(lines)+'\n')
(R/'reference-comparisons.json').write_text(json.dumps(comparisons,indent=2)+'\n')
data=json.loads((R/'metadata-calibration/summary.json').read_text());lines=['# Calibrated native boundary results','','Each entry is a median of120 independent workers. Every worker performs two warmups and five timed reads. The secondary mean averages those worker medians; it is not a replacement acceptance rule. Historical10percentCPU and5percent+8MiBpeak review limits remain.','','| Scope and case | Policy | Label | CPU median ms | Mean of worker medians ms | CPU median change |','|---|---|---|---:|---:|---:|']
for a in data:
 b=next(b for b in data if b['engine']=='cleanup' and all(b[k]==a[k] for k in ['case','scope','policy']));delta=100*(a['medians']['total_cpu_ns']/b['medians']['total_cpu_ns']-1)
 lines.append(f"| {a['scope']} {a['case']} | {a['policy']} | {a['engine']} | {a['medians']['total_cpu_ns']/1e6:.3f} | {a['mean_cpu_ns']/1e6:.3f} | {delta:+.1f}% |")
(R/'metadata-calibration.md').write_text('\n'.join(lines)+'\n')
data=json.loads((R/'phases/summary.json').read_text());lines=['# Isolated preparation and hash phases','','Six independent workers per cell. Constructor and factory workers each perform10000 calls. Hash workers each perform100 output-array loops. Native String hashes and null positions validate. Diagnostic phases are not additive portions of public CSV read time. The cleanup prefix stub measures call overhead and does not construct a decoder.','','| Case | Phase | Hash mode | Snapshot | CPU per call microseconds |','|---|---|---|---|---:|']
for a in data:lines.append(f"| {a['case']} | {a['action']} | {a['hash_mode']} | {a['engine']} | {a['cpu_per_iteration_ns']/1000:.4f} |")
(R/'phases.md').write_text('\n'.join(lines)+'\n')
head=json.loads((R/'metadata-head.json').read_text())['commit'];assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()==head;assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
for label in ['metadata-release','metadata-debug','metadata-asan']:
 d=json.loads((R/(label+'-summary.json')).read_text());assert (d['passedTests'],d['failedTests'],d['skippedTests'])==(394,0,0)
 rec=json.loads((R/(label+'-command.json')).read_text());assert all(hashlib.sha256((S/p).read_bytes()).hexdigest()==h for p,h in rec['source_sha256'].items())
worker_counts={}
for d in sorted(R.iterdir()):
 p=d/'workers.jsonl'
 if not d.is_dir() or not p.exists():continue
 xs=[json.loads(l) for l in p.read_text().splitlines()];assert all(x['validated'] for x in xs);worker_counts[d.name]=len(xs)
assert sum(worker_counts.values())==16908
flags=json.loads((R/'metadata-qualification-result.json').read_text())['flags'];quality=json.loads((R/'metadata-calibration/quality-gate.json').read_text())
state=dict(commit=head,branch='codex/csv-prepared-string-membership',parent='167d9a4e6f8cb923342dea3236721c8722015bf3',comparison_parent='c906c3fbbb0baf1357438a7079921a6448e0c9e5',cleanup='f9a99ce54c77909bdd6f95fadd5fa3b5d15490f2',source_clean=True,semantic_tests={k:394 for k in ['Release','Debug','AddressSanitizer']},standard_responses=190,worker_counts=worker_counts,review_flags={k:len(v) for k,v in flags.items()},measurement_quality_passed=quality['passed'],promotion_allowed=False,decision='Metadata preflight is a locally committed, semantically verified preparation improvement. Broad reference matrices pass. Two calibrated candidate CPU flags and one identical-binary CPU flag remain; the two-sided quality gate fails. Historical flags stay; no thresholds relaxed and no production claim based on fixed hashing.',next_step='Pair public reads within one process using the same native null-token Set, with identical-binary and namespace/code-generation controls. Preserve native hashing and scheduling. Use the recurring3392-row parallel stream case to separate implementation cost from per-worker hash setup and runtime variation.')
assert len(list((R/'standardized').glob('*.response.json')))==190
assert json.loads((R/'standard-worker/SwiftSciBenchmarkWorker.build.json').read_text())['source']['commit']==head
(R/'decision.json').write_text(json.dumps(state,indent=2)+'\n');(R/'metadata-fix.patch').write_bytes(subprocess.check_output(['git','show','--format=fuller',head],cwd=S))
print('Source',head,'worker files',sum(worker_counts.values()),'promotion',state['promotion_allowed']);print('Maximum broad median RSS increase MiB',max(a['peak_after_mib']-a['peak_before_mib'] for a in comparisons))
