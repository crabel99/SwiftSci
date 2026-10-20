from pathlib import Path
import subprocess,json,hashlib,shutil
R=Path(__file__).resolve().parent
repo=Path('/private/tmp/swiftsci-scalar-resource-20261019')
files=['CSVColumnBuilderTests.swift','CSVNullMatcherTests.swift','CSVNumericConversionTests.swift','CSVNumericNullFastPathTests.swift']
T=R/'tests';T.mkdir(exist_ok=True)
for name in files:
 if not (T/name).exists():shutil.copy2(repo/'Tests/SwiftDataFrameTests'/name,T/name)
(T/'TestMain.swift').write_text('import Testing\nimport Darwin\n@main struct TestMain { static func main() async { let code: CInt = await Testing.__swiftPMEntryPoint(); exit(code) } }\n')
receipts=[]
for v in ['cursor','specialized']:
 b=json.loads((R/'build'/v/'build.json').read_text());D=R/'test-build'/v;D.mkdir(parents=True,exist_ok=True)
 cmd=b['commands'][0][:]
 cmd=[x.replace(str(R/'build'/v),str(D)) for x in cmd]+['-enable-testing']
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
 link=b['commands'][1][:]
 link=[x.replace(str(R/'build'/v),str(D)) for x in link]
 i=link.index(str(R/'ResourceProbe.swift'));link[i:i+1]=[str(T/'TestMain.swift'),*[str(T/n) for n in files]]
 link[-1]=str(D/'CSVTests')
 framework='/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/Library/Frameworks'
 link += ['-F',framework,'-Xlinker','-rpath','-Xlinker',framework,'-load-plugin-library','/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/lib/swift/host/plugins/testing/libTestingMacros.dylib']
 p=subprocess.run(link,capture_output=True,text=True);assert p.returncode==0,p.stderr
 p=subprocess.run([str(D/'CSVTests')],capture_output=True,text=True)
 (D/'tests.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stdout+p.stderr
 receipts.append(dict(variant=v,commands=[cmd,link],exit_code=p.returncode,sources={name:hashlib.sha256((T/name).read_bytes()).hexdigest() for name in files},output_sha256=hashlib.sha256((D/'tests.log').read_bytes()).hexdigest()))
 print(v,(p.stdout+p.stderr)[-600:],flush=True)
(R/'test-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
