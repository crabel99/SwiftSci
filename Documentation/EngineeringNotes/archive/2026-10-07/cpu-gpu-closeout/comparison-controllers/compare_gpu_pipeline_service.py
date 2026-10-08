"""Compare retained and consumed inputs through the public regression pipeline."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import statistics
import subprocess

from compare_gpu_budget_workflow import capacities_for
from contracts import read_json, require, write_json
from profile_gpu_residency import owned_worker
from runner import verify_uninstrumented

CASES = {
    'small': ('fixed', 64, 3, 32768),
    'medium': ('fixed', 4096, 17, 16384),
    'large': ('fixed', 65535, 65, 512),
    'mixed': ('mixed', 65536, 65, 1024),
}


IMPUTER_CASES = {
    'small': ('fixed', 64, 3, 16384),
    'medium': ('fixed', 4096, 17, 8192),
    'large': ('fixed', 65535, 65, 128),
    'mixed': ('mixed', 65536, 65, 256),
}


def validate_snapshot(memory):
    for key in ['rss_bytes', 'peak_rss_bytes', 'physical_footprint_bytes', 'malloc_in_use_bytes', 'malloc_allocated_bytes']:
        require(math.isfinite(memory[key]) and 0 <= memory[key] < 2 * 1024**3, 'Invalid or excessive memory')
    require(memory['peak_rss_bytes'] >= memory['rss_bytes'], 'Peak below residency')


def validate(record, storage, schedule, rows, columns, requests, scaler="standard", verify_source=False):
    require(scaler in ["standard", "minmax", "imputer-minmax"] and record["scaler"] == scaler, "Scaler identity differs")
    require(record['source_verification_enabled'] == verify_source, 'Source verification mode differs')
    require(record['source_checks'] == (requests if verify_source and storage == 'copy' else 0), 'Source checks incomplete')
    sizes = [rows] if schedule == 'fixed' else [8191, 65535, 16383, 65536]
    require((record['mode'], record['storage'], record['schedule'], record['row_schedule'],
             record['columns'], record['request_count']) ==
            ('pipeline-service', storage, schedule, sizes, columns, requests), 'Workload identity differs')
    limit = 256 * 1024**2
    require(record['max_concurrent'] == 2 and record['limit_bytes'] == record['cache_limit_bytes'] == limit,
            'Admission or cache policy differs')
    capacities = [capacities_for('logical', n, columns, retained_oracle=True) for n in sizes]
    require(record['estimate_capacities'] == capacities, 'Capacity accounting differs')
    peak = record['peak_reserved_bytes']
    require(0 < peak <= min(limit, 2 * max(sum(c.values()) for c in capacities)), 'Invalid reservation peak')
    require(record['reserved_after'] == record['queued_after'] == 0, 'Reservations did not drain')
    results = record['requests']
    require([r['id'] for r in results] == list(range(requests)), 'Incomplete or duplicated requests')
    for item in results:
        require(item['rows'] == sizes[item['id'] % len(sizes)], 'Request shape differs')
        require(math.isfinite(item['maxError']) and 0 <= item['maxError'] <= 1e-4, 'Analytic oracle failed')
        require(re.fullmatch('[0-9a-f]{64}', item['outputSHA256']) is not None, 'Invalid output hash')
        require(all(math.isfinite(item[k]) and item[k] >= 0 for k in ['queueMS', 'serviceMS']), 'Invalid request timing')
    elapsed = record['elapsed_ms']
    require(math.isfinite(elapsed) and elapsed > 0, 'Invalid elapsed time')
    require(math.isclose(record['requests_per_second'], requests * 1000 / elapsed, rel_tol=1e-12), 'Rate differs')
    before, measured, closed = [record[k] for k in ['before', 'measured', 'closed']]
    require(before['pid'] == measured['pid'] == closed['pid'], 'Worker PID changed')
    require(before['mlx_active_bytes'] > 0 and before['mlx_cache_bytes'] == 0, 'Invalid warm baseline')
    require(measured['mlx_active_bytes'] == before['mlx_active_bytes'], 'Request MLX owners remain')
    require(0 <= measured['mlx_cache_bytes'] <= limit, 'GPU cache exceeds configured limit')
    require(closed['mlx_active_bytes'] == closed['mlx_cache_bytes'] == 0, 'Final model cleanup failed')
    for memory in [before, measured, closed]:
        validate_snapshot(memory)
    if scaler == 'imputer-minmax':
        require(re.fullmatch('[0-9a-f]{64}', record['parameters_sha256']) is not None, 'Invalid parameter hash')
        windows = record['windows']
        count = min(4, requests)
        require(len(windows) == count, 'Missing lifecycle windows')
        previous_peak = before['peak_rss_bytes']
        for i, state in enumerate(windows):
            require(state['completed_requests'] == (i + 1) * requests // count, 'Window progress differs')
            require(state['pid'] == before['pid'], 'Window PID differs')
            require(state['reserved_bytes'] == state['queued_count'] == 0, 'Window reservations remain')
            require(state['mlx_active_bytes'] == before['mlx_active_bytes'], 'Window MLX owners remain')
            require(0 <= state['mlx_cache_bytes'] <= limit, 'Window cache exceeds limit')
            validate_snapshot(state)
            require(state['peak_rss_bytes'] >= max(previous_peak, state['rss_bytes']), 'Invalid window peak')
            previous_peak = state['peak_rss_bytes']
        require(closed['peak_rss_bytes'] >= measured['peak_rss_bytes'] >= previous_peak, 'Final peak decreased')
    return tuple(item['outputSHA256'] for item in results)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rounds', type=int, default=3)
    parser.add_argument('--scaler', choices=['standard', 'minmax', 'imputer-minmax'], default='standard')
    parser.add_argument('--cases', choices=CASES, nargs='+', default=list(CASES))
    args = parser.parse_args()
    if not 1 <= args.rounds <= 10 or len(set(args.cases)) != len(args.cases):
        parser.error('Use 1...10 rounds and unique cases')
    cases = IMPUTER_CASES if args.scaler == 'imputer-minmax' else CASES
    worker = args.worker.resolve(strict=True)
    verify_uninstrumented(worker)
    root = Path(__file__).resolve().parents[2]
    args.output.mkdir(parents=True, exist_ok=False)
    sources = list((root/'Sources').rglob('*.swift')) + list((root/'Benchmarks/RetainedGPUTrial').glob('*.swift'))
    sources += [root/'Package.swift', root/'Package.resolved']
    sources += [root/'Benchmarks/Tools'/name for name in ['compare_gpu_pipeline_service.py',
        'compare_gpu_budget_workflow.py', 'profile_gpu_residency.py', 'contracts.py', 'runner.py']]
    write_json(args.output/'provenance.json', {
        'binary_sha256': hashlib.sha256(worker.read_bytes()).hexdigest(),
        'source_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'hardware': subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string','hw.memsize'],text=True),
        'os': subprocess.check_output(['sw_vers'],text=True), 'cases': {k:cases[k] for k in args.cases}, 'rounds':args.rounds,
        'scaler': args.scaler,
        'contract': (
            'Training-only imputation and scaling before the finite regression boundary; CPU model fit then GPU held-out prediction; four drained windows retain model and cache; two request slots per window; 256 MiB admission and cache limits; no cache clear between windows'
            if args.scaler == 'imputer-minmax' else
            'Public RegressionPipeline with nested Pipeline and the selected fitted scaler; two continuously refilled request slots; 256 MiB conservative reservations; 256 MiB MLX cache limit; no idle or cache clear inside measurement'),
        'timing': 'For imputer-minmax, includes four window drains and memory samples. Includes admission, fixture generation, validation, preprocessing, GPU prediction, analytic oracle and complete output hashing. Excludes fitting, warmup, JSON output and final cleanup. No network or disk ingestion.',
        'memory': 'Per-process samples and lifetime high-water marks. Shared model, allocator caches and retained small request-metric records are outside per-request reservations. Reservation limit is not an RSS cap.',
    })
    reference, parameters, summary = {}, {}, []
    env = dict(os.environ)
    env.pop('SWIFTSCI_RESIDENCY_DIR', None)
    for iteration in range(args.rounds):
        for case in (args.cases if iteration % 2 == 0 else list(reversed(args.cases))):
            schedule, rows, columns, requests = cases[case]
            for storage in (['copy', 'owned'] if iteration % 2 == 0 else ['owned', 'copy']):
                require(int(subprocess.check_output(['sysctl','-n','kern.memorystatus_vm_pressure_level'],text=True)) == 1,
                        'Elevated memory pressure; no worker started')
                stem = f'{iteration}-{case}-{storage}'
                command = [str(worker), 'pipeline-service', storage, schedule, str(rows), str(columns), str(requests), args.scaler]
                write_json(args.output/(stem+'-command.json'), command)
                with (args.output/(stem+'.json')).open('w') as stdout, (args.output/(stem+'.stderr')).open('w') as stderr:
                    with owned_worker(command,stdout=stdout,stderr=stderr,env=env) as process:
                        require(process.wait(timeout=180) == 0, f'Worker failed: {stem}')
                record = read_json(args.output/(stem+'.json'))
                hashes = validate(record, storage, schedule, rows, columns, requests, args.scaler)
                require(case not in reference or reference[case] == hashes, 'Predictions differ across ownership or rounds')
                reference[case] = hashes
                if args.scaler == 'imputer-minmax':
                    digest = record['parameters_sha256']
                    require(case not in parameters or parameters[case] == digest, 'Fitted parameters differ')
                    parameters[case] = digest
                summary.append({'round':iteration,'case':case,'storage':storage,'elapsed_ms':record['elapsed_ms'],
                    'requests_per_second':record['requests_per_second'],
                    'service_median_ms':statistics.median(r['serviceMS'] for r in record['requests']),
                    'measured_rss_mib':record['measured']['rss_bytes']/1024**2,
                    'peak_rss_mib':record['measured']['peak_rss_bytes']/1024**2,
                    'closed_rss_mib':record['closed']['rss_bytes']/1024**2})
                write_json(args.output/'summary.json',summary)
                print('Passed',stem,flush=True)
    print(f'Passed {len(summary)} workers',flush=True)


if __name__ == '__main__':
    main()
