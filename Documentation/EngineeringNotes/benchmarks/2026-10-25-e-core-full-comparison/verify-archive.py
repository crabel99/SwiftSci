"""Verify preserved receipts without original paths, native libraries, or measured executables.

Usage: python verify-archive.py experiment.tar.gz
The verifier contains reviewed pure calculations copied from the frozen source.
It never executes source code read from an archive.
No probe, native library, worker, or external-engine package executes.
"""
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
import tarfile


ROOT = Path("archived-source")

POLICY = 'e-core-application-v1'

FIELDS = ('user_ticks','system_ticks','p_user_ticks','p_system_ticks','instructions',
          'p_instructions','cycles','p_cycles','flags','timebase_numer','timebase_denom')

def interval(before, after):
    if before['pid'] != after['pid']:
        raise ValueError('Core snapshot PID mismatch')
    scale = (before['timebase_numer'],before['timebase_denom'])
    if (any(type(n) is not int or n <= 0 for n in scale)
            or scale != (after['timebase_numer'],after['timebase_denom'])):
        raise ValueError('Invalid Mach timebase')
    counts = {}
    for key in FIELDS[:8]:
        a,b = before[key],after[key]
        if type(a) is not int or type(b) is not int or a < 0 or b < a:
            raise ValueError('Invalid or backward core counter: '+key)
        counts[key] = b-a
    for total,p in [('user_ticks','p_user_ticks'),('system_ticks','p_system_ticks'),
                    ('instructions','p_instructions'),('cycles','p_cycles')]:
        if counts[p] > counts[total]:
            raise ValueError('P counter exceeds total: '+p)
    if counts['user_ticks'] <= 0 or counts['instructions'] <= 0 or counts['cycles'] <= 0:
        raise ValueError('Missing positive core-accounting work')
    if counts['p_user_ticks']:
        raise ValueError('Application CPU time ran on P cores')
    ticks = dict(user_e=counts['user_ticks'],user_p=counts['p_user_ticks'],
                 kernel_e=counts['system_ticks']-counts['p_system_ticks'],kernel_p=counts['p_system_ticks'])
    return dict(pid=before['pid'],deltas=counts,
        time_ns={key:value*scale[0]/scale[1] for key,value in ticks.items()})

def audit_receipt(value, worker_pids):
    worker_pids = list(worker_pids)
    if (len(worker_pids) != len(set(worker_pids))
            or [w['pid'] for w in value['before']] != worker_pids
            or [w['pid'] for w in value['after']] != worker_pids):
        raise ValueError('Missing or mismatched worker core snapshot')
    for snapshot in value['before']+value['after']:
        if any(type(snapshot.get(k)) is not int or snapshot[k] != 0
               for k in ['running_before','running_after']):
            raise ValueError('Worker was not quiescent at the counter boundary')
    workers = [interval(a,b) for a,b in zip(value['before'],value['after'])]
    controller = interval(value['controller_before'],value['controller_after'])
    if controller['pid'] in {w['pid'] for w in workers}:
        raise ValueError('Controller is also recorded as a worker')
    return dict(policy=POLICY,workers=workers,controller=controller,
        time_ns={key:sum(w['time_ns'][key] for w in workers)+controller['time_ns'][key]
                 for key in controller['time_ns']})

def percentile(values, fraction):
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)]

def summarize(jobs, elapsed_ns, samples, queued_jobs):
    if len(jobs) != len(queued_jobs) or {x['id'] for x in jobs} != {x['id'] for x in queued_jobs}:
        raise ValueError('Incomplete or duplicate work set')
    expected = {x['id']: x for x in queued_jobs}
    for job in jobs:
        task = expected[job['id']]
        if job['workflow'] != task['workflow'] or job['input'] != task['input']:
            raise ValueError('Worker completed the wrong task')
        for key in ('cpu_ns', 'wall_ns', 'response_ns', 'queue_ns'):
            if not math.isfinite(job[key]) or job[key] < 0:
                raise ValueError('Invalid timing')
        if job['response_ns'] < job['queue_ns'] or job['response_ns'] > elapsed_ns:
            raise ValueError('Response falls outside the batch')
    result = dict(completed=len(jobs), elapsed_ns=elapsed_ns,
                  completed_per_minute=len(jobs) * 60e9 / elapsed_ns,
                  operation_cpu_ns=sum(x['cpu_ns'] for x in jobs),
                  sampled_peak_rss_bytes=max(x[1] for x in samples),
                  sample_count=len(samples), per_case={})
    for case in sorted({x['input'] + '/' + x['workflow'] for x in jobs}):
        group = [x for x in jobs if x['input'] + '/' + x['workflow'] == case]
        result['per_case'][case] = dict(count=len(group),
            p50_response_ns=percentile([x['response_ns'] for x in group], .5),
            p95_response_ns=percentile([x['response_ns'] for x in group], .95),
            p95_queue_ns=percentile([x['queue_ns'] for x in group], .95),
            p95_service_ns=percentile([x['response_ns']-x['queue_ns'] for x in group], .95))
    return result

def jobs_for(cases, copies, rotation):
    jobs = [dict(case, id=i*len(cases)+case['id']) for i in range(copies) for case in cases]
    offset = rotation % len(jobs)
    return jobs[offset:]+jobs[:offset]

def control_flags(medians, limits, callers):
    flags = []
    for label in (name for name in medians if not name.endswith('_twin')):
        left, right = medians[label], medians[label+'_twin']
        for metric, limit in (('charged_cpu_ns', limits['twin_cpu_deviation']),
                              ('elapsed_ns', limits['twin_wall_deviation'])):
            ratio = right[metric]/left[metric]
            if abs(ratio-1) > limit:
                flags.append(dict(label=label, metric=metric, ratio=ratio))
        low, high = sorted((left['sampled_peak_rss_bytes'],right['sampled_peak_rss_bytes']))
        if high > low*limits['twin_peak_relative'] + callers[label]*limits['twin_peak_slack_per_caller_bytes']:
            flags.append(dict(label=label, metric='sampled_peak_rss_bytes', low=low, high=high))
    return flags

LIMITS = dict(twin_cpu_deviation=.10,twin_wall_deviation=.10,
              twin_peak_relative=1.05,twin_peak_slack_per_caller_bytes=8*2**20)

def conditions(swift, python, include_pandas_arrow=False):
    worker = ROOT/'Benchmarks/CPUThroughput/external_worker.py'
    return {
        'swiftsci_optional':dict(engine='swiftsci',command=[str(swift)],mode='optional'),
        'swiftsci_compact':dict(engine='swiftsci',command=[str(swift)],mode='compact'),
        **{engine:dict(engine=engine,command=[str(python),str(worker)],mode=engine)
           for engine in ('pandas','polars','duckdb') + (('pandas_arrow',) if include_pandas_arrow else ())},
    }

def validate_plan(plan, validate_calibration):
    if plan.get('core_policy') is not None:
        validate_calibration(plan['core_policy'])
    modes = {name:c['mode'] for name,c in conditions('/swift','/python',
        plan.get('include_pandas_arrow',False)).items()}
    if {name:c['mode'] for name,c in plan['conditions'].items()} != modes:
        raise ValueError('Comparison must retain every declared reader condition')
    labels=list(modes)+[name+'_twin' for name in modes]
    orders=[labels[i:]+labels[:i] for i in range(2 if plan['smoke'] else len(labels))]
    if plan['orders']!=orders or plan['quality_policy']!=LIMITS:
        raise ValueError('Comparison ordering or controls changed')
    if (plan['callers']!=4 or plan['copies_per_case']!=(2 if plan['smoke'] else 16)
            or plan['rss_limit_bytes']!=8*2**30):
        raise ValueError('Caller, work, or memory budget changed')
    cases=plan['cases'];inputs={c['input'] for c in cases}
    if len(cases)!=4 or len(inputs)!=2:
        raise ValueError('Two reference datasets and four workflows are required')
    if any({c['workflow'] for c in cases if c['input']==name}!={'read','sort-matrix'} for name in inputs):
        raise ValueError('Every dataset requires both complete workflows')

def require(value, message):
    if not value:
        raise ValueError(message)


def main(path):
    with tarfile.open(path, 'r:gz') as archive:
        members = archive.getmembers()
        require(all(m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in members), 'Unsafe archive member')
        require(len({m.name for m in members}) == len(members), 'Duplicate archive member')
        files = {m.name: archive.extractfile(m).read() for m in members}
    inventory = json.loads(files.pop('inventory.json'))
    require(set(inventory) == set(files), 'Archive inventory differs')
    for name, data in files.items():
        require(inventory[name] == dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest()), 'Archive bytes differ: '+name)
    def load(name):
        return json.loads(files[name])
    root = 'full/panel/'
    plan = load(root+'plan.json')
    source_prefix = 'full-measured-sources/'
    for name, sha in plan['source_hashes'].items():
        require(hashlib.sha256(files[source_prefix+name]).hexdigest() == sha, 'Controller source hash differs')
    for name, sha in plan['swift_build']['sources'].items():
        require(hashlib.sha256(files[source_prefix+name]).hexdigest() == sha, 'Swift source hash differs')
    calibration=plan['core_policy']
    require(load('full/core-controls/calibration.json')==calibration, 'Calibration receipt differs from plan')
    def calibration_check(value):
        require(value['policy']==POLICY, 'Wrong core policy')
        require(value['source_sha256']==hashlib.sha256(files[source_prefix+'Benchmarks/CPUThroughput/core_counters.c']).hexdigest(), 'Counter source differs')
        for key in ('p_user_ticks','p_instructions','p_cycles','timebase_numer','timebase_denom'):
            require(type(value['probe'].get(key)) is int and value['probe'][key]>0, 'Positive P calibration absent')
        for name, key in [('core-counters.dylib','library_sha256'),('core-counter-probe','probe_binary_sha256')]:
            require(hashlib.sha256(files['full/core-controls/'+name]).hexdigest()==value[key], 'Calibration binary hash differs')
    validate_plan(plan,calibration_check)
    require(not plan['smoke'] and len(plan['orders'])==12, 'Not the full fixed panel')
    require(root+'end.json' in files and root+'failure.json' not in files, 'Panel did not complete')
    expected_bytes=files[root+'expected.json']
    require(hashlib.sha256(expected_bytes).hexdigest()==plan['expected_sha256'], 'Expected contract changed')
    expected=json.loads(expected_bytes)
    records=load(root+'records.json')
    wanted={(i,label) for i,order in enumerate(plan['orders']) for label in order}
    require(len(records)==144 and {(r['round'],r['label']) for r in records}==wanted, 'Missing or duplicate queue')
    ready=load(root+'preflight/ready.json');post=load(root+'postflight/ready.json')
    jobs=0;workers=0
    for row in records:
        raw=load(root+f"r{row['round']}-{row['label']}/result.json")
        summary=raw['summary'];require(summary==row['summary'], 'Queue summary differs')
        require(len(raw['before'])==len(raw['after'])==len(raw['runtime'])==4, 'Caller count differs')
        tasks=jobs_for(plan['cases'],16,row['round'])
        calculated=summarize(raw['jobs'],summary['elapsed_ns'],raw['memory_samples'],tasks)
        require(all(summary[k]==v for k,v in calculated.items()), 'Raw job summary differs')
        require(summary['sampled_peak_rss_bytes']<=plan['rss_limit_bytes'], 'Sampled RSS ceiling exceeded')
        samples=raw['memory_samples']
        require(len(samples)>=2 and all(isinstance(x,list) and len(x)==2 and all(type(v) is int and v>=0 for v in x) for x in samples), 'Invalid memory sample shape')
        require(all(b[0]>=a[0] for a,b in zip(samples,samples[1:])), 'Invalid memory sample order')
        require(summary['max_sample_gap_ns']==max(b[0]-a[0] for a,b in zip(samples,samples[1:])), 'Memory sample gap differs')
        for field, phase in [('initial_rss_bytes','before'),('retained_rss_bytes','after')]:
            require(summary[field]==sum(x['rss_bytes'] for x in raw[phase]), 'RSS boundary total differs')
        cpu=sum(b['cpu_ns']-a['cpu_ns'] for a,b in zip(raw['before'],raw['after']))
        require(cpu>=0 and cpu==summary['worker_cpu_ns'] and cpu+summary['controller_cpu_ns']==summary['charged_cpu_ns'], 'CPU totals differ')
        resident=summary['sampled_resident_byte_seconds']
        require(math.isfinite(resident) and 0<=resident<=summary['sampled_peak_rss_bytes']*summary['elapsed_ns']/1e9, 'Resident integral outside bounds')
        name=row['label'].removesuffix('_twin');config=plan['conditions'][name]
        for runtime in raw['runtime']:
            require(runtime.get('ready'), 'Worker not ready')
            require(all(runtime.get(k)==ready[name].get(k)==post[name].get(k) for k in ('engine','versions','execution')), 'Runtime identity differs')
            if config['engine']!='swiftsci':require(runtime['engine']==config['engine'], 'Wrong engine')
        require(all(j['storage']==config['mode'] for j in raw['jobs']), 'Wrong storage mode')
        core=audit_receipt(raw['core_usage'],[r['pid'] for r in raw['runtime']])
        require(core['controller']['pid']==plan['controller_pid'] and core['time_ns']==summary['core_time_ns'], 'Core receipt differs')
        workers+=len(core['workers']);jobs+=len(raw['jobs'])
    checks=0
    for phase in ('preflight','postflight'):
        rows=load(root+phase+'/checks.json')
        wanted_checks={(n,c['input'],c['workflow']) for n in plan['conditions'] for c in plan['cases']}
        require(len(rows)==24 and {(x['label'],x['input'],x['workflow']) for x in rows}==wanted_checks, 'Missing native-output check')
        require(all(x['check']==expected[x['input']+'/'+x['workflow']] for x in rows), 'Output hash differs')
        checks+=len(rows)
    metrics=('charged_cpu_ns','elapsed_ns','sampled_peak_rss_bytes')
    medians={label:{key:statistics.median(r['summary'][key] for r in records if r['label']==label) for key in metrics} for label in plan['orders'][0]}
    flags=control_flags(medians,plan['quality_policy'],{label:4 for label in medians})
    require(flags==load(root+'audit.json')['flags'], 'Frozen control decision differs')
    require((jobs,workers,checks)==(9216,576,48), 'Full totals differ')
    validation=load('full-validation.json')
    require(validation['passed'] and validation['source_binding_passed'] and validation['before']==validation['after'] and validation['before']['commit']==plan['source_head'], 'Post-run validation source binding differs')
    require([(x['exit_code'],x['tests'],x['skipped']) for x in validation['commands']]==[(0,255,4),(0,4,0)], 'Post-run validation results differ')
    for name,sha in (plan['source_hashes'] | plan['swift_build']['sources']).items():
        require(validation['before']['source_hashes'][name]==sha, 'Validated source differs from measured source')
    external=load('external-artifacts.json')
    require(len(external)==2, 'Wrong external artifact count')
    for item,role,path,sha in zip(external,['Swift worker','Python interpreter'],
          [plan['conditions']['swiftsci_optional']['command'][0],plan['conditions']['pandas']['command'][0]],
          [plan['swift_build']['binary_sha256'],plan['python_sha256']]):
        require(item['role']==role and item['path']==path and item['sha256']==sha and type(item['bytes']) is int and item['bytes']>0 and item['status']=='recorded, bytes not archived', 'External artifact identity differs')
    before=load('full-input-metadata-inflight.json');after=load('full-input-metadata-final.json')
    require(before['files']==after['files'] and all(x['ctime_before_launch'] for x in before['files']), 'Input metadata differs')
    return dict(archive_members_verified=len(files),recomputable_receipt_fields_passed=True,resident_integral="bounds_only",queues=144,jobs=jobs,full_output_checks=checks,
        core_intervals_passed=True,worker_intervals=workers,controller_intervals=144,calibration_hashes_passed=True,post_run_source_binding_passed=True,
        controls_passed=not flags,performance_qualified=not flags,flags=flags,
        external_binary_bytes_unavailable=external,
        limits=['Queue intervals only. Startup and full-output checks have no core receipts.',
                'Recorded calibration stdout cannot be independently authenticated as output of the preserved executable.',
                'Resident byte-seconds remain a recorded statistic with range checks. Exact recomputation lacks the saved monotonic batch start/end.',
                'Input bytes are identified by SHA256 but are not archived. Earlier test logs lack source binding; separate post-run validation includes it.'])


if __name__=='__main__':
    print(json.dumps(main(Path(sys.argv[1])),indent=2,allow_nan=False))
