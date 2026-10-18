#!/usr/bin/env python3
"""Check eligibility of the current four-engine operation baseline, not promotion."""
import argparse
import json
from pathlib import Path
import sys


def check(repo, path):
    sys.path.insert(0, str(repo / 'Benchmarks/Tools'))
    from contracts import identity, read_json, require
    from csv_contract import schema_for
    from reporting import audit, comparison, validate_worker
    run = read_json(path)
    cases = run['plan']['cases']
    required = {'medium-csv-read', 'medium-sort', 'large-csv-read', 'large-sort'}
    require(len(cases) == 4 and {c['case']['id'] for c in cases} == required,
            'The four registered medium/large CSV and sort cases are required')
    by_id = {c['case']['id']: c for c in cases}
    for case in cases:
        workload = case['workload']
        require(workload['operation'] in ('csv-read', 'sort'), 'Unsupported operation scope')
        if workload['operation'] == 'csv-read':
            require(workload['id'] == 'csv-read-v2', 'CSV v1 is unmatched; reject its performance ranking')
            require(workload.get('csv_schema') == schema_for(case['dataset']['kind']),
                    'CSV schema is missing or differs from the required native types')
    require(set(run['plan']['engines']) == {'swiftsci', 'pandas', 'polars', 'duckdb'},
            'Four-engine baseline coverage is required')
    require(run['plan'].get('execution', {}).get('mode') == 'production-default',
            'Native production execution policy is required')
    profile = run['plan']['profile']
    require(profile['batches'] >= 5 and profile['warmups'] >= 2 and profile['samples'] >= 5,
            'Insufficient baseline repetitions')
    require(run['power_start']['source'] == 'AC' and run['power_end']['source'] == 'AC',
            'AC power is required')
    audit(run, path.parent)
    comparison(run, run)
    source = run['plan']['source']
    require(source['tree_sha256'] == identity(source['files']), 'Source map fingerprint differs')
    receipts = 0
    for event in run['events']:
        token = f"{event['case_id']}-{event['engine']}-{event['batch']}"
        request = read_json(path.parent / f'{token}.request.json')
        response = read_json(path.parent / f'{token}.response.json')
        require(response == event['result'], 'Saved response differs from the audited run')
        workload = by_id[event['case_id']]['workload']
        require(request['operation'] == workload['operation'], 'Request operation differs')
        validate_worker(response, request)
        if request['operation'] == 'csv-read':
            require(request['csv_schema'] == schema_for(request['dataset_kind']),
                    'Request schema differs from native types')
            receipts += 1
    return dict(status='passed', scope='matched public CSV and sort operations only',
                contract_hash=run['plan']['contract_hash'], source_fingerprint=source['tree_sha256'],
                worker_executions=len(run['events']), csv_schema_receipts=receipts,
                measured_samples=sum(len(e['result']['samples']) for e in run['events']),
                complete_workflow_qualified=False, memory_tradeoff_qualified=False,
                energy_qualified=False, promotion_qualified=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check(args.repo.resolve(), args.run.resolve())
    except (ValueError, KeyError, OSError, ImportError) as error:
        print(json.dumps(dict(status='rejected', reason=str(error)), indent=2))
        raise SystemExit(1)
    print(json.dumps(result, indent=2))
