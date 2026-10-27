from pathlib import Path
import contextlib, hashlib, json, subprocess, sys, unittest
r = Path(__file__).resolve().parent
s = r / 'source'
tag = sys.argv[1]
out = r / ('reporting-' + tag)
out.mkdir(exist_ok=False)
paths = ['.github/workflows/ci.yml', 'scripts/verify_doc_coverage.py', 'scripts/tests/test_verify_doc_coverage.py']
fingerprints = lambda: {name: hashlib.sha256((s / name).read_bytes()).hexdigest() for name in paths}
before = fingerprints()
suite = unittest.defaultTestLoader.discover(str(s / 'scripts/tests'), pattern='test_*.py')
with (out / 'tests.log').open('w') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
command = [sys.executable, 'scripts/verify_doc_coverage.py']
with (out / 'scan.log').open('w') as log:
    scan = subprocess.run(command, cwd=s, stdout=log, stderr=subprocess.STDOUT)
assert before == fingerprints()
report = dict(tag=tag, head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=s, text=True).strip(),
    files=before, tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped),
    status='passed' if result.wasSuccessful() and scan.returncode == 0 else 'failed', scan_command=command, scan_exit_code=scan.returncode,
    logs={name: hashlib.sha256((out / name).read_bytes()).hexdigest() for name in ['tests.log', 'scan.log']},
    runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
raise SystemExit(0 if report['status'] == 'passed' else 1)
