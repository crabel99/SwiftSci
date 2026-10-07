"""Measure memory between repeated request bursts with one persistent GPU model."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess

from compare_gpu_budget_workflow import validate_burst
from contracts import read_json, require, write_json
from profile_gpu_residency import owned_worker
from runner import verify_uninstrumented


SCHEDULES = {'fixed': [65535], 'mixed': [8191, 65535, 16383, 65536]}
METRICS = ['rss_bytes', 'physical_footprint_bytes', 'malloc_in_use_bytes', 'malloc_allocated_bytes']


def validate(records, policy, schedule, bursts, requests, idle_ms, storage="copy"):
    require(len(records) == bursts + 2, 'Incomplete series')
    start, closed = records[0], records[-1]
    require(start['kind'] == 'start' and closed['kind'] == 'closed', 'Missing lifecycle records')
    require((start['policy'], start['schedule'], start['burst_count'], start['request_count'], start['idle_ms']) ==
            (policy, schedule, bursts, requests, idle_ms), 'Series identity mismatch')
    require(start['row_schedule'] == SCHEDULES[schedule] and start['columns'] == 65 and
            start['limit_bytes'] == 256 * 1024**2 and start['max_concurrent'] == 2, 'Workload differs')
    require(start.get('storage', 'copy') == storage, 'Storage policy differs')
    retained_oracle = start.get('retained_oracle', False)
    require(storage != 'owned' or retained_oracle, 'Owned trial needs retained oracle accounting')
    baseline = start['before']['mlx_active_bytes']
    require(baseline > 0 and start['before']['mlx_cache_bytes'] == 0, 'Invalid fitted-model baseline')
    pid = start['before']['pid']
    hashes = {}
    for index, record in enumerate(records[1:-1]):
        require(record['kind'] == 'burst' and record['index'] == index, 'Burst sequence differs')
        rows = SCHEDULES[schedule][index % len(SCHEDULES[schedule])]
        outputs = validate_burst(record, policy, rows, 65, 256, requests, retained_oracle)
        require(record['peak_admitted_requests'] <= 2, 'Worker slot limit exceeded')
        require(all(r.get('reusedInputColumns', 0) == (65 if storage == 'owned' else 0)
                    for r in record['requests']), 'Input storage reuse differs')
        if rows in hashes:
            require(hashes[rows] == outputs, 'Predictions changed between bursts')
        hashes[rows] = outputs
        for name in ['after_burst', 'after_cache_clear', 'after_idle']:
            memory = record[name]
            require(memory['pid'] == pid, 'Worker PID changed')
            require(memory['mlx_active_bytes'] == baseline, 'Request MLX owners remain')
            require(all(memory[k] >= 0 for k in METRICS), 'Invalid memory measurement')
        for name in ['after_cache_clear', 'after_idle']:
            require(record[name]['mlx_cache_bytes'] == 0, 'MLX cache remains')
        require(record['after_idle']['rss_bytes'] < 2 * 1024**3 and
                record['after_idle']['physical_footprint_bytes'] < 2 * 1024**3 and
                record['after_idle']['malloc_in_use_bytes'] < 64 * 1024**2, 'Diagnostic safety ceiling exceeded')
    require(closed['memory']['pid'] == pid, 'Worker PID changed at close')
    require(closed['memory']['mlx_active_bytes'] == closed['memory']['mlx_cache_bytes'] == 0,
            'Model cleanup failed')
    return hashes


def summarize(records):
    samples = records[1:-1]
    # Four-burst windows contain a complete mixed-size cycle in the same order.
    return {metric: {
        'first_cycle_mean_mib': statistics.mean(r['after_idle'][metric] for r in samples[:4]) / 1024**2,
        'last_cycle_mean_mib': statistics.mean(r['after_idle'][metric] for r in samples[-4:]) / 1024**2,
        'cycle_mean_growth_mib': (statistics.mean(r['after_idle'][metric] for r in samples[-4:]) -
                                  statistics.mean(r['after_idle'][metric] for r in samples[:4])) / 1024**2 if len(samples) >= 8 else None,
        'last_cycle_range_mib': [min(r['after_idle'][metric] for r in samples[-4:]) / 1024**2,
                                 max(r['after_idle'][metric] for r in samples[-4:]) / 1024**2],
        'idle_change_median_mib': statistics.median(r['after_idle'][metric] - r['after_cache_clear'][metric]
                                                   for r in samples) / 1024**2,
    } for metric in METRICS}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--storage', choices=['copy','owned'], nargs='+', default=['copy'])
    parser.add_argument('--rounds', type=int, default=3)
    parser.add_argument('--bursts', type=int, default=12)
    parser.add_argument('--requests', type=int, default=8)
    parser.add_argument('--idle-ms', type=int, default=1000)
    args = parser.parse_args()
    if not (1 <= args.rounds <= 10 and 4 <= args.bursts <= 32 and args.bursts % 4 == 0 and
            2 <= args.requests <= 16 and 0 <= args.idle_ms <= 2000):
        parser.error('Use rounds 1...10, bursts 4...32 divisible by four, requests 2...16, idle-ms 0...2000')
    if len(set(args.storage)) != len(args.storage):
        parser.error('storage values must be unique')
    worker = args.worker.resolve(strict=True)
    verify_uninstrumented(worker)
    args.output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[2]
    sources = list((root/'Sources').rglob('*.swift')) + list((root/'Benchmarks/RetainedGPUTrial').glob('*.swift'))
    sources += [root/'Package.swift', root/'Package.resolved']
    sources += [root/'Benchmarks/Tools'/name for name in ['compare_gpu_memory_reuse.py', 'compare_gpu_budget_workflow.py',
                                                        'profile_gpu_residency.py', 'contracts.py', 'runner.py']]
    write_json(args.output/'provenance.json', {
        'binary_sha256': hashlib.sha256(worker.read_bytes()).hexdigest(),
        'source_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'hardware': subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string','hw.memsize'],text=True),
        'os': subprocess.check_output(['sw_vers'],text=True),
        'storage': args.storage, 'rounds': args.rounds, 'bursts': args.bursts, 'requests': args.requests, 'idle_ms': args.idle_ms,
        'contract': 'One fitted model, fixed two-worker slot cap and 256 MiB reservations; all outputs consumed, request storage released, GPU synchronized and cache cleared per burst; no native inspection or pressure relief',
        'timing': 'Diagnostic workload; serialization, cache clearing and idle time between bursts are excluded from elapsed_ms. Do not compare with uninterrupted service throughput.',
    })
    reference = {}
    summary = []
    env = dict(os.environ)
    env.pop('SWIFTSCI_RESIDENCY_DIR', None)
    for iteration in range(args.rounds):
        for schedule in SCHEDULES:
            for policy in (['logical','padded'] if iteration % 2 == 0 else ['padded','logical']):
                for storage in (args.storage if iteration % 2 == 0 else list(reversed(args.storage))):
                    require(int(subprocess.check_output(['sysctl','-n','kern.memorystatus_vm_pressure_level'],text=True)) == 1,
                            'Elevated memory pressure; no worker started')
                    stem = f'{iteration}-{schedule}-{policy}-{storage}'
                    command = [str(worker),'reuse-workflow',policy,schedule,str(args.bursts),str(args.requests),str(args.idle_ms),storage]
                    write_json(args.output/(stem+'-command.json'),command)
                    with (args.output/(stem+'.jsonl')).open('w') as stdout, (args.output/(stem+'.stderr')).open('w') as stderr:
                        with owned_worker(command, stdout=stdout, stderr=stderr, env=env) as process:
                            require(process.wait(timeout=180) == 0, 'Repeated-burst worker failed')
                    records = [json.loads(line) for line in (args.output/(stem+'.jsonl')).read_text().splitlines()]
                    hashes = validate(records,policy,schedule,args.bursts,args.requests,args.idle_ms,storage)
                    for rows, outputs in hashes.items():
                        if rows in reference: require(reference[rows] == outputs, 'Predictions differ across policies or workers')
                        reference[rows] = outputs
                    summary.append({'round': iteration, 'storage': storage, 'policy': policy, 'schedule': schedule, 'metrics': summarize(records)})
                    write_json(args.output/'summary.json',summary)
                    print('Passed',stem,flush=True)
    print(f'Passed {len(summary)} workers, {len(summary)*args.bursts*args.requests} requests',flush=True)


if __name__ == '__main__':
    main()
