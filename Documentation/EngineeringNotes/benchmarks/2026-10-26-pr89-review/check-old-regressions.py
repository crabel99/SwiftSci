from pathlib import Path
import hashlib, json, os, subprocess, time

r = Path(__file__).resolve().parent
source = r / 'source'
out = r / 'compatibility-regressions'
out.mkdir(exist_ok=False)
env = dict(os.environ)
env.update(TOOLCHAINS='org.swift.633202606251a', SDKROOT='/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk', MACOSX_DEPLOYMENT_TARGET='14.0', PATH='/Users/crabel/Library/Developer/Toolchains/swift-6.3.3-RELEASE.xctoolchain/usr/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin')
command = ['swift', 'test', '--scratch-path', str(r / 'swift633'), '-j', '2', '--enable-code-coverage', '--filter', 'PCAFullSVDLayoutTests|PCAMeanOverflowTests']
before = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['Sources', 'Tests'] for p in (source / folder).rglob('*.swift')}
start = time.time()
with (out / 'tests.log').open('w') as log:
    result = subprocess.run(command, cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT)
assert all(hashlib.sha256((source / name).read_bytes()).hexdigest() == digest for name, digest in before.items())
(out / 'result.json').write_text(json.dumps({'command': command, 'exit_code': result.returncode, 'seconds': time.time() - start, 'sources': before}, indent=2) + '\n')
print((out / 'tests.log').read_text()[-5000:])
raise SystemExit(result.returncode)
