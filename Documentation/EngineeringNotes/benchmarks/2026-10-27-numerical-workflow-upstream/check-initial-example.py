from pathlib import Path
import hashlib
import json
import os
import subprocess

r = Path(__file__).resolve().parent
s = r / 'source'
out = r / 'initial-example'
out.mkdir(exist_ok=False)
env = dict(os.environ)
for name in ['TOOLCHAINS', 'XCODE_XCCONFIG_FILE']:
    env.pop(name, None)
env.update(PATH='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin', SDKROOT='/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX27.0.sdk', MACOSX_DEPLOYMENT_TARGET='14.0', LLVM_PROFILE_FILE=str(out / 'profile-%p.profraw'))
command = ['swift', 'run', '-c', 'debug', 'ScientificWorkflow', '--output', str(out / 'results')]
files = ['Package.swift', 'Examples/NumericalWorkflow/ScientificWorkflow.swift', 'Examples/NumericalWorkflow/Data/sample.csv', 'Examples/NumericalWorkflow/verify.py']
before = {name: hashlib.sha256((s / name).read_bytes()).hexdigest() for name in files}
with (out / 'build-and-run.log').open('w') as log:
    result = subprocess.run(command, cwd=s, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=1800)
receipt = dict(scope='Initial uncommitted example check, not final-head qualification', command=command, exit_code=result.returncode, commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=s, text=True).strip(), source_sha256=before, initial_git_status=subprocess.check_output(['git', 'status', '--porcelain'], cwd=s, text=True))
(out / 'result.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
raise SystemExit(result.returncode)
