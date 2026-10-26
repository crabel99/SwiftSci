"""Summarize measured outputs without changing reference or task-quality contracts."""
from pathlib import Path
import argparse, json, statistics, sys
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--results',type=Path,required=True);a=p.parse_args()
sys.path.insert(0,str(a.source/'Benchmarks/CoreMLInference'))
from run import assessment, reference_accuracy_met
records=json.loads((a.results/'results.json').read_text())
(a.results/'assessment.json').write_text(json.dumps(assessment(records),indent=2)+'\n')
lines=['# Representative Core ML inference', '', 'These are development benchmarks on frozen repository splits. Training, model compilation, source-batch construction and reference calculations are outside the Swift inference timer. Loading is recorded separately and may use Core ML caches. Prediction includes input packing, execution and owned output extraction. Python controls separately include fitted scaling. No application acceptance threshold is established.', '', '| Dataset | Rows | Mode | Load ms | First ms | Warm median ms | Warm p95 ms | Max absolute error | Strict reference | Peak RSS MiB |', '|---|---:|---|---:|---:|---:|---:|---:|---|---:|']
for r in sorted(records,key=lambda r:(r['workload'],r['rows'],r['mode'])):
 times=sorted(s['elapsed_ns']/1e6 for s in r['warmPredictions'])
 # Nearest-rank p95. Preserve samples for alternative summaries.
 import math
 p95=times[math.ceil(.95*len(times))-1]
 error=max(s['maximum_absolute_error'] for s in [r['firstPrediction'],*r['warmPredictions']])
 lines.append(f"| {r['workload']} | {r['rows']} | {r['mode']} | {1000*r['loadSeconds']:.3f} | {r['firstPrediction']['elapsed_ns']/1e6:.3f} | {statistics.median(times):.3f} | {p95:.3f} | {error:.6g} | {'pass' if reference_accuracy_met(r) else 'exceeds'} | {r['processPeakRSSBytes']/1048576:.1f} |")
lines+=['','Task quality compares actual held-out predictions, not the numerical tolerance above. CPU, GPU and Neural Engine names in this table mean allowed compute units. Actual placement requires separate inspected trace events.','']
for kind in ['wdbc','wine']:
 meta=json.loads((a.results/f'fixtures/{kind}-training.json').read_text())
 lines += [f'## {kind} held-out quality','',f"Training-only scaling, frozen Float32-shared weights, {meta['iterations']} optimizer iterations. Warnings: {meta['training_warnings']!r}.", '', '```json',json.dumps(dict(independent=meta['quality'],measured={r['mode']:r.get('task_quality') for r in records if r['workload']==kind and 'task_quality' in r}),indent=2),'```','']
(a.results/'REPORT.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(cases=len(records),strict_pass=sum(reference_accuracy_met(r) for r in records),strict_exceedances=sum(not reference_accuracy_met(r) for r in records))))
