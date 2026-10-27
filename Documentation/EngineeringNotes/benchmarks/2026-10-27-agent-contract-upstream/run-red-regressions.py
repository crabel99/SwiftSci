"""Reproduce each regression against its declared current-source predecessor."""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys, time
r = Path(__file__).resolve().parent
source = r / 'source'
prior = Path('/private/tmp/swiftsci-upstream-classification-20261027')
original = Path('/private/tmp/swiftsci-llm-completion-20261026')
kind = sys.argv[1]
assert kind in ['completion', 'cancellation']
out = r / ('red-' + kind)
out.mkdir(exist_ok=False)
s = out / 'source'
subprocess.run(['git','clone','--shared','--no-checkout',str(source),str(s)],check=True)
base = '01d48cbcd940c886546b2bb8d6b177d9b7a0e277' if kind == 'completion' else 'ac4e73a06412f67a09243f7516bbff769d13b677'
subprocess.run(['git','checkout','--detach',base],cwd=s,check=True)
overlay = []
if kind == 'completion':
    # These additive declarations let a rich fixture compile; the upstream agent is unchanged.
    for name in ['Sources/SwiftLLM/Core/Generation.swift','Sources/SwiftLLM/Core/LLMModel.swift','Sources/SwiftLLM/Core/TransformerDecoder.swift']:
        (s/name).write_bytes((source/name).read_bytes()); overlay.append(name)
    test = 'Tests/SwiftAgentTests/CompletionReportingTests.swift'
    shutil.copy2(original/'red-test.swift',s/test)
    selected = 'CompletionReportingTests.truncatedAction'
else:
    test = 'Tests/SwiftAgentTests/ReActCancellationTests.swift'
    shutil.copy2(source/test,s/test)
    selected = 'ReActCancellationTests'
overlay.append(test)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
agent = 'Sources/SwiftAgent/ReActAgent.swift'
assert (s/agent).read_bytes() == subprocess.check_output(['git','show',base+':'+agent],cwd=source)
before = {str(p.relative_to(s)):sha(p) for parent in ['Sources','Tests'] for p in (s/parent).rglob('*.swift')}
report = dict(kind=kind, base=base, agent_sha256=sha(s/agent), overlay={name:sha(s/name) for name in overlay}, source_fingerprints=before,
    scope='Current upstream ReAct consumer with only additive rich capability declarations/conformance and mock fixture seeded' if kind=='completion' else 'Isolated completion-only parent plus final cancellation tests; no cancellation production correction', controller_sha256=sha(Path(__file__)))
(out/'setup.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'overlay.patch').write_bytes(subprocess.check_output(['git','diff',base],cwd=s))
shutil.copy2(s/test,out/'regression-test.swift')
subprocess.run(['cp','-cR',str(prior/'source/.build'),str(s/'.build')],check=True)
python = Path('/private/tmp/swiftsci-prepared-pca-20261026/local-ci/python/cpython-3.13.17-macos-aarch64-none/bin')
env = dict(os.environ,PATH='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin:'+str(python)+':/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin',SDKROOT='/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX27.0.sdk',MACOSX_DEPLOYMENT_TARGET='14.0')
for key in ['TOOLCHAINS','XCODE_XCCONFIG_FILE']:env.pop(key,None)
command = ['swift','test','-j','2','--filter',selected]
start=time.time()
with (out/'tests.log').open('w') as log:
    result = subprocess.run(command,cwd=s,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
assert before == {str(p.relative_to(s)):sha(p) for parent in ['Sources','Tests'] for p in (s/parent).rglob('*.swift')}
text=(out/'tests.log').read_text()
report.update(command=command,exit_code=result.returncode,seconds=time.time()-start,log_sha256=sha(out/'tests.log'),build_completed='Build complete!' in text,
    expected_regression_reproduced=result.returncode==1 and 'Build complete!' in text and 'Test run with' in text and 'failed' in text)
(out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({key:value for key,value in report.items() if key not in ['source_fingerprints','overlay']},indent=2))
raise SystemExit(0 if report['expected_regression_reproduced'] else 1)
