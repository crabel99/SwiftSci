"""Inspect opt-in request-worker checkpoints; always resume or terminate the child."""
import argparse
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import signal
import subprocess
import time

from contracts import require, read_json, write_json
from compare_gpu_budget_workflow import validate
from runner import verify_uninstrumented


@contextmanager
def owned_worker(command, **kwargs):
    def terminated(signum, frame):
        raise SystemExit(128 + signum)

    previous = signal.signal(signal.SIGTERM, terminated)
    process = None
    try:
        process = subprocess.Popen(command, start_new_session=True, **kwargs)
        yield process
    finally:
        try:
            if process is not None and process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=10)
        finally:
            signal.signal(signal.SIGTERM, previous)


def wait_stopped(process, marker):
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        require(process.poll() is None, 'Worker exited before checkpoint')
        if marker.exists():
            state = subprocess.check_output(['ps', '-o', 'stat=', '-p', str(process.pid)], text=True)
            if 'T' in state:
                require(read_json(marker)['pid'] == process.pid, 'Checkpoint PID mismatch')
                return
        time.sleep(0.05)
    raise TimeoutError(f'Worker did not stop at {marker.name}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--policy', choices=['logical', 'padded'], default='logical')
    parser.add_argument('--inspect', choices=['native', 'none'], default='native')
    parser.add_argument('--requests', type=int, choices=[8,16], default=16)
    args = parser.parse_args()
    worker = args.worker.resolve(strict=True)
    verify_uninstrumented(worker)
    require(int(subprocess.check_output(['sysctl','-n','kern.memorystatus_vm_pressure_level'],text=True)) == 1,
            'Elevated memory pressure; no worker started')
    args.output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[2]
    sources = list((root/'Sources').rglob('*.swift')) + list((root/'Benchmarks/RetainedGPUTrial').glob('*.swift'))
    sources += [root/'Package.swift', root/'Package.resolved', Path(__file__).resolve()]
    write_json(args.output/'provenance.json', {
        'binary_sha256': hashlib.sha256(worker.read_bytes()).hexdigest(),
        'source_sha256': {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'command': [str(worker),'budget-workflow',args.policy,'65535','65','256',str(args.requests)],
        'environment_override': {'SWIFTSCI_RESIDENCY_DIR': str(args.output.resolve())},
        'profiler': args.inspect + '; no malloc stack logging',
        'timing': 'Diagnostic only. Profiler pauses and allocator perturbation invalidate comparison with throughput timings.',
    })
    env = dict(os.environ, SWIFTSCI_RESIDENCY_DIR=str(args.output.resolve()))
    with (args.output/'worker.stdout').open('w') as stdout, (args.output/'worker.stderr').open('w') as stderr:
        with owned_worker([str(worker),'budget-workflow',args.policy,'65535','65','256',str(args.requests)],
                                   stdout=stdout,stderr=stderr,env=env) as process:
            tools = {}
            for stage in ['before-burst','after-cache-clear','after-pressure-relief']:
                wait_stopped(process,args.output/(stage+'.json'))
                statuses = {}
                inspectors = [('heap',['/usr/bin/heap','-s','-z','--noContent']),
                                      ('vmmap',['/usr/bin/vmmap','-summary','-wide']),
                                      ('leaks',['/usr/bin/leaks','--noContent','--nostacks'])]
                for name, command in (inspectors if args.inspect == 'native' else []):
                    with (args.output/f'{stage}-{name}.txt').open('w') as log:
                        result = subprocess.run(command+[str(process.pid)],stdout=log,stderr=subprocess.STDOUT,timeout=60)
                    statuses[name] = result.returncode
                tools[stage] = statuses
                write_json(args.output/'tool-status.json',tools)
                print(stage,statuses,flush=True)
                os.kill(process.pid,signal.SIGCONT)
            require(process.wait(timeout=120) == 0, 'Worker failed after final checkpoint')
    record = read_json(args.output/'worker.stdout')
    validate(record,args.policy,65535,65,256,args.requests)
    write_json(args.output/'validated-result.json',record)
    print('All request and cleanup checks passed',flush=True)


if __name__ == '__main__':
    main()
