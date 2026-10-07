"""Compare two production pipeline binaries with balanced order and exact outputs."""
import argparse
import hashlib
import os
from pathlib import Path
import statistics
import subprocess

from compare_gpu_pipeline_service import IMPUTER_CASES, validate
from contracts import require, read_json, write_json
from profile_gpu_residency import owned_worker
from runner import verify_uninstrumented


def compare_records(baseline, candidate, storage, case):
    schedule, rows, columns, requests = IMPUTER_CASES[case]
    before = validate(baseline,storage,schedule,rows,columns,requests,'imputer-minmax')
    after = validate(candidate,storage,schedule,rows,columns,requests,'imputer-minmax')
    require(before == after, 'Complete predictions differ between binaries')
    require(baseline['parameters_sha256'] == candidate['parameters_sha256'], 'Fitted parameters differ')
    return {
        'throughput_change_percent':100*(candidate['requests_per_second']/baseline['requests_per_second']-1),
        'service_median_change_percent':100*(statistics.median(r['serviceMS'] for r in candidate['requests']) /
                                           statistics.median(r['serviceMS'] for r in baseline['requests'])-1),
        'baseline_rss_mib':baseline['measured']['rss_bytes']/1024**2,
        'candidate_rss_mib':candidate['measured']['rss_bytes']/1024**2,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--baseline-provenance',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    workers = {'baseline':args.baseline.resolve(strict=True),'candidate':args.candidate.resolve(strict=True)}
    parent = read_json(args.baseline_provenance)
    digests = {name:hashlib.sha256(p.read_bytes()).hexdigest() for name,p in workers.items()}
    require(digests['baseline'] == parent['binary_sha256'], 'Baseline binary differs from preserved provenance')
    require(digests['baseline'] != digests['candidate'], 'Comparison requires distinct binaries')
    for worker in workers.values():verify_uninstrumented(worker)
    args.output.mkdir(parents=True,exist_ok=False)
    root = Path(__file__).resolve().parents[2]
    sources = list((root/'Sources').rglob('*.swift')) + list((root/'Benchmarks/RetainedGPUTrial').glob('*.swift'))
    sources += [root/'Package.swift',root/'Package.resolved']
    sources += [root/'Benchmarks/Tools'/name for name in ['compare_gpu_device_reuse.py','compare_gpu_pipeline_service.py',
        'compare_gpu_budget_workflow.py','profile_gpu_residency.py','contracts.py','runner.py']]
    write_json(args.output/'provenance.json',{
        'baseline':parent,'candidate_binary_sha256':digests['candidate'],
        'candidate_source_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'hardware':subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string','hw.memsize'],text=True),
        'os':subprocess.check_output(['sw_vers'],text=True),
        'cases':IMPUTER_CASES,'rounds':3,'scaler':'imputer-minmax',
        'contract':'Unmodified pipeline-service worker in separate fresh processes; 3 rounds, 4 sizes, both input ownership modes, alternating binary order and reversed case order; full output and fitted-parameter equality; standard lifecycle validation.',
        'timing':'Public pipeline, no prediction phase clocks. Includes admission, fixtures, preprocessing, awaited GPU prediction, numerical validation, raw SHA, four window drains and memory samples. Excludes model fitting, warmup, hexadecimal/JSON encoding and final cleanup. Normal host activity remains possible.',
        'limits':'Two request slots, 256 MiB admission/cache, 2 GiB sample bound, 180-second owned child deadline, normal memory-pressure gate. No inter-window cache clear.'})
    env = dict(os.environ);env.pop('SWIFTSCI_RESIDENCY_DIR',None)
    summaries=[];pairs=[];reference={};parameters={}
    cases = list(IMPUTER_CASES)
    for iteration in range(3):
        for case_index,case in enumerate(cases if iteration % 2 == 0 else list(reversed(cases))):
            schedule,rows,columns,requests = IMPUTER_CASES[case]
            for storage_index,storage in enumerate(['copy','owned'] if iteration % 2 == 0 else ['owned','copy']):
                records={}
                order=['baseline','candidate'] if (iteration+case_index+storage_index) % 2 == 0 else ['candidate','baseline']
                for name in order:
                    require(int(subprocess.check_output(['sysctl','-n','kern.memorystatus_vm_pressure_level'])) == 1,'Elevated memory pressure; no worker started')
                    stem=f'{iteration}-{case}-{storage}-{name}'
                    command=[str(workers[name]),'pipeline-service',storage,schedule,str(rows),str(columns),str(requests),'imputer-minmax']
                    write_json(args.output/(stem+'-command.json'),command)
                    with (args.output/(stem+'.json')).open('w') as stdout,(args.output/(stem+'.stderr')).open('w') as stderr:
                        with owned_worker(command,stdout=stdout,stderr=stderr,env=env) as p:
                            require(p.wait(timeout=180) == 0,f'Worker failed: {stem}')
                    r=read_json(args.output/(stem+'.json'))
                    hashes=validate(r,storage,schedule,rows,columns,requests,'imputer-minmax')
                    require(case not in reference or hashes == reference[case],'Output differs across ownership or rounds')
                    require(case not in parameters or r['parameters_sha256'] == parameters[case],'Fitted parameters differ across runs')
                    reference[case]=hashes;parameters[case]=r['parameters_sha256'];records[name]=r
                    summaries.append({'round':iteration,'case':case,'storage':storage,'binary':name,
                        'requests_per_second':r['requests_per_second'],'elapsed_ms':r['elapsed_ms'],
                        'service_median_ms':statistics.median(x['serviceMS'] for x in r['requests']),
                        'measured_rss_mib':r['measured']['rss_bytes']/1024**2,'peak_rss_mib':r['measured']['peak_rss_bytes']/1024**2})
                    write_json(args.output/'summary.json',summaries)
                    print('Passed',stem,flush=True)
                pairs.append({'round':iteration,'case':case,'storage':storage,**compare_records(records['baseline'],records['candidate'],storage,case)})
                write_json(args.output/'paired.json',pairs)
    print('Passed 48 production pipeline workers',flush=True)


if __name__ == '__main__':
    main()
