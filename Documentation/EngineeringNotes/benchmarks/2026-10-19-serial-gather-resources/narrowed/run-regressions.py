from pathlib import Path
import json,subprocess,hashlib,shutil
R=Path(__file__).resolve().parent
source=Path('/private/tmp/swiftsci-scalar-resource-20261019/Tests/SwiftDataFrameTests/ScalarGatherSpecializationTests.swift')
shutil.copy2(source,R/source.name)
(R/'TestMain.swift').write_text('import Testing\nimport Darwin\n@main struct TestMain { static func main() async { let code: CInt = await Testing.__swiftPMEntryPoint(); exit(code) } }\n')
build=json.loads((R/'build/candidate/build.json').read_text());cmd=build['commands'][1][:]
i=cmd.index(str(R/'ResourceProbe.swift'));cmd[i:i+1]=[str(R/'TestMain.swift'),str(R/source.name)]
cmd[-1]=str(R/'ScalarGatherTests')
framework='/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/Library/Frameworks'
cmd += ['-F',framework,'-Xlinker','-rpath','-Xlinker',framework,'-load-plugin-library','/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/lib/swift/host/plugins/testing/libTestingMacros.dylib']
with (R/'regression-build.log').open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
assert p.returncode==0,(R/'regression-build.log').read_text()[-6000:]
p=subprocess.run([str(R/'ScalarGatherTests')],capture_output=True,text=True)
(R/'regression-tests.log').write_text(p.stdout+p.stderr)
print(p.stdout+p.stderr);assert p.returncode==0
(R/'regression-receipt.json').write_text(json.dumps({'command':cmd,'exit_code':p.returncode,'test_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'production_object_sha256':hashlib.sha256((R/'build/candidate/SwiftDataFrame.o').read_bytes()).hexdigest()},indent=2)+'\n')
