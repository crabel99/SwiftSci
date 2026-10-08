"""Compare scoped import policies under the same whole-request reservation limits."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess

from contracts import require, read_json, write_json
from runner import verify_uninstrumented, metal_build_record


def capacities_for(policy, rows, columns, retained_oracle=False):
    page = os.sysconf('SC_PAGE_SIZE')
    payload = rows * columns * 4
    allocation = (payload + page - 1) // page * page
    capacities = {'raw_and_transformed': rows * columns * 16, 'packed_allocation': allocation,
            'logical_copy': allocation if policy == 'logical' and payload % page else 0,
            'outputs_and_readback': rows * 24, 'scaler_scratch_and_metadata': 64 * 1024,
            'backend_allowance': 8 * 1024**2}
    if retained_oracle: capacities['analytic_oracle'] = rows * 8
    return capacities


def validate_burst(record, policy, rows, columns, limit_mib, requests, retained_oracle=False):
    require((record['policy'], record['rows'], record['columns'], record['limit_bytes'], record['request_count']) ==
            (policy, rows, columns, limit_mib * 1024**2, requests), 'Worker identity mismatch')
    require(record['estimate_capacities'] == capacities_for(policy, rows, columns, retained_oracle), 'Capacity model differs')
    estimate = record['estimate_bytes']
    require(estimate == sum(record['estimate_capacities'].values()) and estimate > 0, 'Invalid estimate')
    require(0 < record['peak_reserved_bytes'] <= record['limit_bytes'], 'Admission limit exceeded')
    require(record['peak_reserved_bytes'] == estimate * record['peak_admitted_requests'], 'Admission accounting differs')
    require(1 <= record['peak_admitted_requests'] <= requests, 'Invalid concurrency')
    require(record['reserved_after'] == record['queued_after'] == 0, 'Admission did not drain')
    results = record['requests']
    require([r['id'] for r in results] == list(range(requests)), 'Incomplete or duplicate requests')
    for result in results:
        require(0 <= result['maxError'] <= 1e-4, 'Analytic oracle failed')
        for name in ['queueMS', 'generateMS', 'transformMS', 'predictMS', 'consumeMS', 'serviceMS']:
            require(result[name] >= 0, 'Invalid timing')
    require(record['elapsed_ms'] > 0, 'Invalid elapsed time')
    return tuple(r['outputSHA256'] for r in results)


def validate(record, policy, rows, columns, limit_mib, requests):
    hashes = validate_burst(record, policy, rows, columns, limit_mib, requests)
    require(record['after_close']['mlx_active_bytes'] == 0, 'MLX owners remain')
    require(record['after_cache_clear']['mlx_cache_bytes'] == 0, 'MLX cache remains')
    return hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rounds', type=int, default=5)
    parser.add_argument('--requests', type=int, default=8)
    parser.add_argument('--rows', type=int, nargs='+', default=[65535, 65536])
    parser.add_argument('--columns', type=int, nargs='+', default=[64, 65])
    parser.add_argument('--limits-mib', type=int, nargs='+', default=[128, 192, 256])
    args = parser.parse_args()
    if not 1 <= args.rounds <= 20 or not 1 <= args.requests <= 16:
        parser.error('rounds must be 1...20 and requests must be 1...16')
    for name, values, lower, upper in [('rows', args.rows, 1, 65536), ('columns', args.columns, 1, 128),
                                       ('limits-mib', args.limits_mib, 32, 512)]:
        if not values or len(set(values)) != len(values) or any(not lower <= v <= upper for v in values):
            parser.error(f'{name} must contain unique values in {lower}...{upper}')
    for columns in args.columns:
        for rows in args.rows:
            for limit in args.limits_mib:
                for policy in ['logical', 'padded']:
                    required = sum(capacities_for(policy, rows, columns).values())
                    if required > limit * 1024**2:
                        parser.error(f'{policy} {rows}x{columns} requires {required} reserved bytes, exceeds {limit} MiB')
    worker = args.worker.resolve(strict=True)
    verify_uninstrumented(worker)
    root = Path(__file__).resolve().parents[2]
    args.output.mkdir(parents=True, exist_ok=False)
    sources = list((root/'Sources').rglob('*.swift')) + list((root/'Benchmarks/RetainedGPUTrial').glob('*.swift'))
    sources += [root/'Package.swift', root/'Package.resolved', Path(__file__).resolve()]
    metal = metal_build_record(worker)
    metal['expected_build_settings'] = metal.pop('build_settings')
    write_json(args.output/'provenance.json', {
        'binary_sha256': hashlib.sha256(worker.read_bytes()).hexdigest(),
        'source_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'hardware': subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string', 'hw.memsize'], text=True),
        'os': subprocess.check_output(['sw_vers'], text=True), 'metal': metal,
        'contract': 'Burst of independent seeded requests; fit scaler and CPU OLS once, share one GPU model actor; acquire before input creation, release after complete validation and output destruction',
        'timing': 'Wall time includes admission, fixture generation, transformation, prediction, oracle and hash consumption; no network or storage I/O; per-request prediction includes waiting for the shared actor',
        'memory': 'Explicit raw/transformed, packed, copy, output and scratch capacities plus fixed 8 MiB backend allowance; this is estimated admission, not an RSS cap. Shared model and allocator caches are outside reservations.',
        'columns': args.columns, 'rows': args.rows, 'limits_mib': args.limits_mib,
        'requests': args.requests, 'rounds': args.rounds, 'coverage_instrumentation': False,
    })
    records = []
    for columns in args.columns:
        for rows in args.rows:
            reference = None
            for limit in args.limits_mib:
                for iteration in range(args.rounds):
                    for policy in (['logical', 'padded'] if iteration % 2 == 0 else ['padded', 'logical']):
                        require(int(subprocess.check_output(['sysctl','-n','kern.memorystatus_vm_pressure_level'],text=True)) == 1,
                                'Elevated memory pressure; no worker started')
                        process = subprocess.run([str(worker), 'budget-workflow', policy, str(rows), str(columns), str(limit), str(args.requests)],
                                                 capture_output=True, text=True, timeout=120)
                        stem = f'{columns}-{rows}-{limit}-{iteration}-{policy}'
                        (args.output/(stem+'.stdout')).write_text(process.stdout)
                        (args.output/(stem+'.stderr')).write_text(process.stderr)
                        process.check_returncode()
                        record = read_json(args.output/(stem+'.stdout'))
                        hashes = validate(record, policy, rows, columns, limit, args.requests)
                        if reference is None: reference = hashes
                        require(hashes == reference, 'Predictions differ across policies or budgets')
                        record['round'] = iteration
                        records.append(record)
                        write_json(args.output/'samples.json', records)
                print(f'Passed {columns} columns, {rows} rows, {limit} MiB', flush=True)
    summary = []
    for columns in args.columns:
        for rows in args.rows:
            for limit in args.limits_mib:
                for policy in ['logical','padded']:
                    group = [r for r in records if (r['columns'],r['rows'],r['limit_bytes'],r['policy']) == (columns,rows,limit*1024**2,policy)]
                    request_rows = [q for r in group for q in r['requests']]
                    summary.append({'columns':columns,'rows':rows,'limit_mib':limit,'policy':policy,'samples':len(group),
                                    'estimate_mib':group[0]['estimate_bytes']/1024**2,
                                    'admitted_range':[min(r['peak_admitted_requests'] for r in group),max(r['peak_admitted_requests'] for r in group)],
                                    'elapsed_ms':statistics.median(r['elapsed_ms'] for r in group),
                                    'elapsed_range_ms':[min(r['elapsed_ms'] for r in group),max(r['elapsed_ms'] for r in group)],
                                    'peak_rss_mib':statistics.median(r['measured']['peak_rss_bytes'] for r in group)/1024**2,
                                    'queue_median_ms':statistics.median(r['queueMS'] for r in request_rows),
                                    'service_median_ms':statistics.median(r['serviceMS'] for r in request_rows)})
    write_json(args.output/'summary.json', summary)
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    main()
