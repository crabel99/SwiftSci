from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile

r = Path(__file__).resolve().parent
s = r / 'source'
base = '200d3935cc43396658a315bf4d5f745b6c7b496c'
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=s, text=True).strip()
test = s / 'scripts/tests/test_export_coverage.py'
workflow = subprocess.check_output(['git', 'show', base + ':.github/workflows/ci.yml'], cwd=s)
sha = lambda data: hashlib.sha256(data).hexdigest()
assert subprocess.check_output(['git', 'show', head + ':scripts/tests/test_export_coverage.py'], cwd=s) == test.read_bytes()
out = r / 'red-reproducible'
out.mkdir(exist_ok=False)
with tempfile.TemporaryDirectory(prefix='upstream-export-control-') as directory:
    control = Path(directory)
    (control / '.github/workflows').mkdir(parents=True)
    (control / '.github/workflows/ci.yml').write_bytes(workflow)
    (control / 'scripts/tests').mkdir(parents=True)
    shutil.copyfile(test, control / 'scripts/tests/test_export_coverage.py')
    command = [sys.executable, '-m', 'unittest', 'discover', '-s', 'scripts/tests', '-p', 'test_export_coverage.py', '-v']
    with (out / 'tests.log').open('w') as log:
        result = subprocess.run(command, cwd=control, stdout=log, stderr=subprocess.STDOUT)
text = (out / 'tests.log').read_text()
assert result.returncode == 1 and 'Ran 8 tests' in text and 'FAILED (failures=8)' in text
report = dict(source=head, predecessor=base, command=command, exit_code=result.returncode, test_sha256=sha(test.read_bytes()), predecessor_workflow_sha256=sha(workflow), controller_sha256=sha(Path(__file__).read_bytes()), log_sha256=sha((out / 'tests.log').read_bytes()), tests=8, failures=8, scope='Exact final regression test bytes and untouched upstream export workflow in a minimal independent control repository. Real Apple LLVM binaries; no final-source mutation.')
(out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
