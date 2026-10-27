from pathlib import Path
import hashlib, json, os, subprocess, time

r = Path(__file__).resolve().parent
s = r / 'source'
out = r / 'documented-example'
out.mkdir(exist_ok=False)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
git = lambda *a: subprocess.check_output(['git', *a], cwd=s, text=True).strip()
assert git('status', '--porcelain') == ''
files = {n: sha(s / n) for n in git('ls-files').splitlines()}
env = dict(os.environ)
for key in ['TOOLCHAINS', 'XCODE_XCCONFIG_FILE']:
    env.pop(key, None)
env.update(PATH='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin', SDKROOT='/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX27.0.sdk', MACOSX_DEPLOYMENT_TARGET='14.0', LLVM_PROFILE_FILE=str(out / 'profile-%p.profraw'))
report = dict(source=git('rev-parse', 'HEAD'), source_tree=git('rev-parse', 'HEAD^{tree}'), initial_git_status='', source_sha256=files, controller_sha256=sha(Path(__file__)), steps=[])
commands = [
    ('build', ['xcodebuild', '-scheme', 'ScientificWorkflow', '-configuration', 'Release', '-destination', 'platform=macOS,arch=arm64', '-derivedDataPath', str(r / 'derived'), '-clonedSourcePackagesDirPath', str(r / 'native-packages'), '-onlyUsePackageVersionsFromResolvedFile', 'MTL_FAST_MATH=NO', 'MTL_MATH_MODE=SAFE', 'MTL_MATH_FP32_FUNCTIONS=PRECISE', 'build']),
    ('run', [str(r / 'derived/Build/Products/Release/ScientificWorkflow'), '--output', str(out / 'results')]),
    ('verify', ['python3', 'Examples/NumericalWorkflow/verify.py', str(out / 'results')])
]
for name, command in commands:
    start = time.time()
    with (out / (name + '.log')).open('w') as log:
        result = subprocess.run(command, cwd=s, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=1800)
    report['steps'].append(dict(name=name, command=command, exit_code=result.returncode, seconds=time.time()-start, log_sha256=sha(out / (name + '.log'))))
    (out / 'result.json').write_text(json.dumps(report, indent=2)+'\n')
    assert result.returncode == 0, name
assert git('status', '--porcelain') == '' and files == {n: sha(s / n) for n in files}
binary = r / 'derived/Build/Products/Release/ScientificWorkflow'
report.update(status='passed', binary=str(binary.resolve()), binary_sha256=sha(binary), outputs={name: sha(out / 'results' / name) for name in ['report.json', 'predictions.csv']})
(out / 'result.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(dict(status='passed', source=report['source'], binary=report['binary'])))
