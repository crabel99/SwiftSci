from pathlib import Path
import argparse,hashlib,json,subprocess,uuid
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021')
p=argparse.ArgumentParser();p.add_argument('configuration',choices=['Debug','Release']);p.add_argument('--coverage',action='store_true');p.add_argument('--address-sanitizer',action='store_true');p.add_argument('--label',required=True);a=p.parse_args()
subprocess.run(['git','diff','--check'],cwd=S,check=True)
result=R/(a.label+'.xcresult');assert not result.exists()
name='CSVSortValidation-'+uuid.uuid4().hex;scheme=S/'.swiftpm/xcode/xcshareddata/xcschemes'/(name+'.xcscheme')
s= (S/'.swiftpm/xcode/xcshareddata/xcschemes/SwiftDataFrame.xcscheme').read_text()
s=s.replace('   </TestAction>','''      <Testables><TestableReference skipped="NO"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="SwiftDataFrameTests" BuildableName="SwiftDataFrameTests.xctest" BlueprintName="SwiftDataFrameTests" ReferencedContainer="container:"/></TestableReference></Testables>
   </TestAction>''')
scheme.write_text(s)
cmd=['xcodebuild','test','-scheme',name,'-configuration',a.configuration,'-destination','platform=macOS,arch=arm64','-derivedDataPath','/Users/crabel/local-ai/spl/swiftsci/csv-sort-throughput-20261017/tests-derived','-clonedSourcePackagesDirPath','/Users/crabel/Library/Caches/SwiftSci/xcode-packages','-onlyUsePackageVersionsFromResolvedFile','-parallel-testing-enabled','NO','-resultBundlePath',str(result),'-jobs','4','-enableCodeCoverage','YES' if a.coverage else 'NO','ENABLE_TESTABILITY=YES','ENABLE_CODE_COVERAGE='+('YES' if a.coverage else 'NO')]
if a.address_sanitizer:cmd+=['-enableAddressSanitizer','YES']
inputs={str(f.relative_to(S)):hashlib.sha256(f.read_bytes()).hexdigest() for folder in ['Sources/SwiftDataFrame','Tests/SwiftDataFrameTests'] for f in (S/folder).rglob('*.swift')}
try:
 with (R/(a.label+'.log')).open('w') as log: proc=subprocess.run(cmd,cwd=S,stdout=log,stderr=subprocess.STDOUT,timeout=900)
 (R/(a.label+'-command.json')).write_text(json.dumps(dict(command=cmd,exit_code=proc.returncode,source_sha256=inputs),indent=2)+'\n')
 if proc.returncode:raise SystemExit(proc.returncode)
 summary=json.loads(subprocess.check_output(['xcrun','xcresulttool','get','test-results','summary','--path',str(result),'--format','json'],text=True))
 (R/(a.label+'-summary.json')).write_text(json.dumps(summary,indent=2)+'\n');print({k:summary.get(k) for k in ['result','totalTestCount','passedTests','failedTests','skippedTests']},flush=True)
finally:scheme.unlink()
