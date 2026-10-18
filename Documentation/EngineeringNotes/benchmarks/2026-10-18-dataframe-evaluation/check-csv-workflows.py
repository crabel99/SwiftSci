#!/usr/bin/env python3
"""Audit matched streaming and wine workflow screening evidence."""
import argparse
import json
from pathlib import Path
import sys


def check(repo, streams, wine):
    sys.path.insert(0, str(repo / 'Benchmarks/Tools'))
    from contracts import identity, read_json, require
    from csv_contract import schema_for
    from reporting import audit, comparison, validate_worker
    results = []
    for path, engines, required in (
        (streams, {'swiftsci', 'pandas'}, {d+'-'+op for d in ('medium', 'mixed-medium')
             for op in ('csv-stream-read', 'csv-stream-filter', 'csv-stream-group')}),
        (wine, {'swiftsci', 'pandas', 'polars', 'duckdb'}, {'wine-red-pipeline'}),
    ):
        run = read_json(path)
        plan = run['plan']
        cases = {c['case']['id']: c for c in plan['cases']}
        require(len(plan['cases']) == len(required) and set(cases) == required,
                'Required workflow cases are missing or duplicated')
        require(set(plan['engines']) == engines, 'Workflow engine coverage differs')
        require(plan['execution']['mode'] == 'production-default', 'Native parallelism is required')
        p = plan['profile']
        require(p['batches'] >= 5 and p['warmups'] >= 2 and p['samples'] >= 5,
                'Insufficient screening repetitions')
        require(run['power_start']['source'] == run['power_end']['source'] == 'AC', 'AC is required')
        audit(run, path.parent)
        comparison(run, run)
        require(plan['source']['tree_sha256'] == identity(plan['source']['files']), 'Source map differs')
        for case in cases.values():
            w = case['workload']
            require(w['id'] == w['operation']+'-v2', 'Historical unmatched contract rejected')
            require(w.get('csv_schema') == schema_for(case['dataset']['kind']), 'Native types differ')
        for event in run['events']:
            token = f"{event['case_id']}-{event['engine']}-{event['batch']}"
            request = read_json(path.parent / (token+'.request.json'))
            response = read_json(path.parent / (token+'.response.json'))
            require(response == event['result'], 'Saved response differs from the event')
            require(request.get('csv_schema') == schema_for(request['dataset_kind']), 'Request types differ')
            validate_worker(response, request)
        results.append(dict(run=str(path), contract_hash=plan['contract_hash'],
            source_fingerprint=plan['source']['tree_sha256'], workers=len(run['events']),
            observed_schema_receipts=len(run['events']),
            samples=sum(len(e['result']['samples']) for e in run['events'])))
    require(len({r['source_fingerprint'] for r in results}) == 1, 'Workflow sources differ')
    return dict(status='passed', scope='Matched warm-cache CSV workflow screening', runs=results,
                input_types_observed_before_warmups=True, complete_outputs_validated=True,
                application_scale_coverage_complete=False, candidate_improvement_demonstrated=False,
                memory_tradeoff_qualified=False, energy_qualified=False, promotion_qualified=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--streams', type=Path, required=True)
    parser.add_argument('--wine', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check(args.repo.resolve(), args.streams.resolve(), args.wine.resolve())
    except (ValueError, KeyError, OSError, ImportError) as error:
        print(json.dumps(dict(status='rejected', reason=str(error)), indent=2))
        raise SystemExit(1)
    print(json.dumps(result, indent=2))
