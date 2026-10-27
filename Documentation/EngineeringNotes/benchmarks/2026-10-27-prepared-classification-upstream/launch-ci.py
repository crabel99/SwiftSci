from pathlib import Path
import os, sys
r = Path(__file__).resolve().parent
python = Path('/private/tmp/swiftsci-prepared-pca-20261026/local-ci/python/cpython-3.13.17-macos-aarch64-none/bin/python3')
env = dict(os.environ)
for key in ['TOOLCHAINS', 'XCODE_XCCONFIG_FILE']:
    env.pop(key, None)
env.update(PATH='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin:' + str(python.parent) + ':/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin', SDKROOT='/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX27.0.sdk', MACOSX_DEPLOYMENT_TARGET='14.0')
job = sys.argv[1]
assert (r / 'cache-preparation.json').is_file()
if job == 'native':
    command = [str(python), str(r / 'run-native-matrix.py')]
elif job == 'compatibility':
    command = [str(python), str(r / 'check-swift633.py')]
elif job == 'security-swift':
    command = [str(python), str(r / 'check-swift-codeql-replay.py'), '--output', str(r / 'ci-security-swift633')]
else:
    assert job in ['main', 'benchmarks', 'security-python']
    output = {'main': 'ci-main', 'benchmarks': 'ci-bench', 'security-python': 'ci-security-python'}[job]
    controller = 'benchmark-ci-runner.py' if job == 'benchmarks' else 'full-ci-runner.py'
    command = [str(python), str(r / controller), '--root', str(r / 'source'), '--output', str(r / output), '--jobs', job, '--swift-version', '6.4', '--xcode-version', '27.0', '--sdk-version', '27.0']
    if job == 'security-python':
        command += ['--codeql', '/private/tmp/swiftsci-prepared-pca-20261026/local-ci/codeql/codeql', '--codeql-version', '2.27.3']
os.chdir(r / 'source')
os.execvpe(command[0], command, env)
