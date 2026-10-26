from pathlib import Path
import hashlib, json, os, shlex, subprocess, time
r=Path(__file__).resolve().parent;source=r/'source';out=r/'ci-security-swift633';out.mkdir(exist_ok=False)
codeql=Path('/private/tmp/swiftsci-prepared-pca-20261026/local-ci/codeql/codeql')
toolchain=Path('/Users/crabel/Library/Developer/Toolchains/swift-6.3.3-RELEASE.xctoolchain')
env=dict(os.environ,TOOLCHAINS='org.swift.633202606251a',SDKROOT='/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk',MACOSX_DEPLOYMENT_TARGET='14.0',PATH=str(toolchain/'usr/bin')+':/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin')
for key in ['XCODE_XCCONFIG_FILE']:env.pop(key,None)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
before={str(p.relative_to(source)):sha(p) for parent in ['Sources','Tests'] for p in (source/parent).rglob('*.swift')}
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
assert subprocess.check_output(['git','status','--porcelain'],cwd=source,text=True)==''
marker='CODEQL_SWIFTSCI_QUALIFICATION_20261026'
tracked = subprocess.check_output(['git','ls-files','*.swift'],cwd=source,text=True).splitlines()
assert all(marker not in (source / path).read_text() for path in tracked)
version=subprocess.check_output(['swift','--version'],env=env,text=True);assert 'Swift version 6.3.3' in version
extractor=codeql.parent/'swift/tools/osx64/extractor'
extractor_version=subprocess.check_output([str(extractor),'--version'],text=True);assert 'Swift version 6.3.3' in extractor_version
report=dict(source=head,source_fingerprints=before,swift=version,extractor=extractor_version,
    xcode_selected=subprocess.check_output(['xcode-select','-p'],text=True).strip(),
    scope='Swift security analysis on installed compatibility compiler; selected Xcode unchanged. Unused conditional flag forces fresh Swift extraction without changing source.',steps=[])
assert report['xcode_selected']=='/Applications/Xcode.app/Contents/Developer'
commands=[('database',[str(codeql),'database','create',str(out/'database'),'--language=swift','--source-root='+str(source),
    '--command='+shlex.join(['swift','build','--arch','arm64','--scratch-path',str(r/'swift633'),'-c','release','-j','2','-Xswiftc','-D','-Xswiftc',marker])]),
    ('analysis',[str(codeql),'database','analyze',str(out/'database'),'codeql/swift-queries:codeql-suites/swift-code-scanning.qls','--format=sarifv2.1.0','--output='+str(out/'swift.sarif')])]
for name,command in commands:
    start=time.time()
    with (out/(name+'.log')).open('w') as log:
        result=subprocess.run(command,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
    report['steps'].append(dict(name=name,command=command,exit_code=result.returncode,seconds=time.time()-start,log_sha256=sha(out/(name+'.log'))))
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(name,result.returncode,flush=True)
    if result.returncode:raise SystemExit(result.returncode)
data=json.loads((out/'swift.sarif').read_text());assert all(i.get('executionSuccessful',True) for run in data['runs'] for i in run.get('invocations',[]))
assert before=={str(p.relative_to(source)):sha(p) for parent in ['Sources','Tests'] for p in (source/parent).rglob('*.swift')}
assert subprocess.check_output(['xcode-select','-p'],text=True).strip()==report['xcode_selected']
report.update(status='passed',findings=sum(len(run.get('results',[])) for run in data['runs']),sarif_sha256=sha(out/'swift.sarif'),script_sha256=sha(Path(__file__)))
(out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status=report['status'],findings=report['findings'])))
