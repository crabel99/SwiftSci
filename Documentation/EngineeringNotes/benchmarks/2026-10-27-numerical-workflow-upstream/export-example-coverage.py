from pathlib import Path
import hashlib, json, subprocess

r = Path(__file__).resolve().parent
s = r / 'source'
out = r / 'example-coverage'
out.mkdir(exist_ok=False)
controls = json.loads((r / 'example-native-debug/result.json').read_text())
assert controls['status'] == 'passed'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
profiles = sorted((r / 'example-native-debug/profiles').glob('*.profraw'))
assert profiles
profile = out / 'example.profdata'
binary = Path(controls['binary'])
assert sha(binary) == controls['binary_sha256']
source = s / 'Examples/NumericalWorkflow/ScientificWorkflow.swift'
commands = [
    ('merge', ['xcrun', 'llvm-profdata', 'merge', '-sparse', *map(str, profiles), '-o', str(profile)]),
    ('export', ['xcrun', 'llvm-cov', 'export', '-format=lcov', '-instr-profile=' + str(profile), str(binary)])
]
steps = []
for name, command in commands:
    stdout = out / ('coverage.lcov' if name == 'export' else 'merge.stdout')
    stderr = out / (name + '.log')
    with stdout.open('w') as output, stderr.open('w') as log:
        result = subprocess.run(command, cwd=s, stdout=output, stderr=log)
    steps.append(dict(name=name, command=command, exit_code=result.returncode, stdout_sha256=sha(stdout), stderr_sha256=sha(stderr)))
    assert result.returncode == 0
records = [block.strip() + '\nend_of_record\n' for block in (out / 'coverage.lcov').read_text().split('end_of_record') if any(line.startswith('SF:') and line.endswith('Examples/NumericalWorkflow/ScientificWorkflow.swift') for line in block.splitlines())]
assert len(records) == 1
(out / 'example.lcov').write_text(records[0])
lines = records[0].splitlines()
assert sum(line.startswith('SF:') for line in lines) == 1
assert any(line.startswith('SF:') and line.endswith('Examples/NumericalWorkflow/ScientificWorkflow.swift') for line in lines)
found = sum(int(line[3:]) for line in lines if line.startswith('LF:'))
hit = sum(int(line[3:]) for line in lines if line.startswith('LH:'))
assert found > 0 and hit > 0
receipt = dict(status='passed', source=controls['source'], scope='Local native Debug CLI execution coverage, separate from hosted safe-suite coverage and Codecov', selected_record_sha256=sha(out / 'example.lcov'), source_sha256=sha(source), binary_sha256=sha(binary), controls_sha256=sha(r / 'example-native-debug/result.json'), profile_sha256=sha(profile), profiles={str(p): sha(p) for p in profiles}, executable_lines=found, executed_lines=hit, line_percent=100*hit/found, steps=steps, controller_sha256=sha(Path(__file__)))
(out / 'result.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(dict(status='passed', executed=hit, executable=found, percent=100*hit/found)))
