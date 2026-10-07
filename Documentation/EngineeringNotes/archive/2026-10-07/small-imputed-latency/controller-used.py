"""Diagnose small-request latency with alternating ownership in one process."""
import argparse
import hashlib
import math
import os
from pathlib import Path
import re
import subprocess

from contracts import require, read_json, write_json
from profile_gpu_residency import owned_worker
from runner import verify_uninstrumented


def validate(record, route, slots, requests, pairs):
    require((record['mode'],record['route'],record['slots'],record['requests_per_block'],record['pairs']) ==
            ('imputed-latency',route,slots,requests,pairs), 'Workload differs')
    require(route in ['preprocessing','direct','pipeline'] and slots in [1,2], 'Invalid control')
    baseline,closed = record['baseline'],record['closed']
    active = baseline['mlx_active_bytes']
    require((active == 0 if route == 'preprocessing' else active > 0) and baseline['mlx_cache_bytes'] == 0,
            'Invalid fitted baseline')
    require(closed['mlx_active_bytes'] == closed['mlx_cache_bytes'] == 0, 'Model cleanup failed')
    blocks = record['blocks']
    expected = [(i,mode) for i in range(pairs) for mode in ([False,True] if i % 2 == 0 else [True,False])]
    require([(b['pair'],b['owned']) for b in blocks] == expected, 'Blocks missing or out of order')
    hashes = {}
    for block in blocks:
        require(block['requests'] == requests, 'Request count differs')
        require(block['reserved_after'] == block['queued_after'] == 0, 'Admission did not drain')
        require(math.isfinite(block['elapsed_ms']) and block['elapsed_ms'] > 0, 'Invalid elapsed time')
        require(math.isfinite(block['requests_per_second']) and
                math.isclose(block['requests_per_second'], requests*1000/block['elapsed_ms'], rel_tol=1e-12), 'Invalid rate')
        require(math.isfinite(block['max_error']) and 0 <= block['max_error'] <= 1e-4, 'Oracle failed')
        digest = block['output_sha256']
        require(re.fullmatch('[0-9a-f]{64}',digest) is not None, 'Invalid output hash')
        pair = block['pair']
        require(pair not in hashes or hashes[pair] == digest, 'Ownership outputs differ')
        hashes[pair] = digest
        require(set(block['phases']) == {'fixture','preprocessing','prediction','validation','total'}, 'Missing phase')
        for phase in block['phases'].values():
            require(set(phase) == {'mean_us','median_us','p95_us'}, 'Missing timing statistic')
            require(all(math.isfinite(x) and x >= 0 for x in phase.values()) and phase['p95_us'] >= phase['median_us'],
                    'Invalid phase timing')
        require(sum(block['phases'][k]['mean_us'] for k in ['fixture','preprocessing','prediction','validation'])
                <= block['phases']['total']['mean_us'] + 1e-6, 'Phase times exceed total')
        require(block['memory']['mlx_active_bytes'] == active, 'Request GPU owners remain')
        require(0 <= block['memory']['mlx_cache_bytes'] <= 256*1024**2, 'GPU cache exceeds limit')
    previous_peak = 0
    for memory in [baseline,*[b['memory'] for b in blocks],closed]:
        require(memory['pid'] == baseline['pid'], 'PID changed')
        for key in ['rss_bytes','peak_rss_bytes','physical_footprint_bytes','malloc_in_use_bytes','malloc_allocated_bytes']:
            require(math.isfinite(memory[key]) and 0 <= memory[key] < 512*1024**2, 'Invalid memory sample')
        require(memory['peak_rss_bytes'] >= max(previous_peak,memory['rss_bytes']), 'Invalid peak')
        previous_peak = memory['peak_rss_bytes']
    return hashes


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    worker=args.worker.resolve(strict=True)
    verify_uninstrumented(worker)
    args.output.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[2]
    sources=list((root/'Sources').rglob('*.swift'))+list((root/'Benchmarks/RetainedGPUTrial').glob('*.swift'))
    sources += [root/'Package.swift',root/'Package.resolved',Path(__file__).resolve(),root/'Benchmarks/Tools/profile_gpu_residency.py']
    write_json(args.output/'provenance.json',{
        'binary_sha256':hashlib.sha256(worker.read_bytes()).hexdigest(),
        'source_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'hardware':subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string','hw.memsize'],text=True),
        'os':subprocess.check_output(['sw_vers'],text=True),
        'contract':'64 rows, 3 columns; training-only imputation and minmax; alternating copy/consume in one process; 6 pairs of 2048 requests per mode, 1 or 2 admitted slots; full-output equality and lifecycle checks',
        'timing':'Diagnostic clock probes include measurement overhead. Prediction covers actor waits, validation, Float packing/import, GPU execution and readback; not pure device kernel time. Preprocessing-only control predicts with a scalar CPU formula using fitted weights.',
        'limits':'256 MiB admission/cache limit, 16 MiB estimated per request, 180 second worker deadline, memory-pressure gate; no cache clear between paired blocks.'})
    cases=[(route,slots) for route in ['preprocessing','direct','pipeline'] for slots in [1,2]]
    references={};summary=[]
    env=dict(os.environ);env.pop('SWIFTSCI_RESIDENCY_DIR',None)
    for iteration in range(2):
        for route,slots in (cases if iteration == 0 else list(reversed(cases))):
            require(int(subprocess.check_output(['sysctl','-n','kern.memorystatus_vm_pressure_level'])) == 1,
                    'Elevated memory pressure')
            stem=f'{iteration}-{route}-{slots}'
            command=[str(worker),'imputed-latency',route,str(slots),'2048','6']
            write_json(args.output/(stem+'-command.json'),command)
            with (args.output/(stem+'.json')).open('w') as stdout,(args.output/(stem+'.stderr')).open('w') as stderr:
                with owned_worker(command,stdout=stdout,stderr=stderr,env=env) as p:
                    require(p.wait(timeout=180)==0,f'Worker failed: {stem}')
            record=read_json(args.output/(stem+'.json'))
            hashes=validate(record,route,slots,2048,6)
            key='cpu' if route=='preprocessing' else 'gpu'
            require(key not in references or hashes==references[key], 'Control outputs differ')
            references[key]=hashes
            for block in record['blocks']:
                summary.append({'round':iteration,'route':route,'slots':slots,**block})
            write_json(args.output/'summary.json',summary)
            print('Passed',stem,flush=True)
    print('Passed 12 diagnostic workers',flush=True)


if __name__=='__main__':
    main()
