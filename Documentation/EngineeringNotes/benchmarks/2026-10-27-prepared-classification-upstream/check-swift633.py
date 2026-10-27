from pathlib import Path
import hashlib,json,os,subprocess,time
root=Path(__file__).resolve().parent
source=root/'source';out=root/'compatibility';out.mkdir(exist_ok=True)
env=dict(os.environ)
for key in ['TOOLCHAINS','XCODE_XCCONFIG_FILE']:env.pop(key,None)
toolchain='/Users/crabel/Library/Developer/Toolchains/swift-6.3.3-RELEASE.xctoolchain'
env.update(TOOLCHAINS='org.swift.633202606251a',SDKROOT='/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk',MACOSX_DEPLOYMENT_TARGET='14.0',PATH=toolchain+'/usr/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin',SWIFTSCI_LLAMA_TOKENIZER_JSON='/Users/crabel/Library/Caches/SwiftSci/models/Llama-3.2-1B-Instruct-bf16-863c846a/tokenizer.json')
commands=[('debug-build',['swift','build','--scratch-path',str(root/'swift633'),'-j','2']),('safe-tests',['swift','test','--scratch-path',str(root/'swift633'),'-j','2','--enable-code-coverage',*[arg for suite in ['SwiftMLTests','SwiftClusterTests','SwiftForecastTests','SwiftExplainTests','SwiftPreprocessingTests','SwiftOptimizeTests','SwiftLLMTests','SwiftVisionTests'] for arg in ['--skip',suite]]]),('release-build',['swift','build','--scratch-path',str(root/'swift633'),'-c','release','-j','2'])]
commands.insert(2, ('focused-prepared-tests', ['swift','test','--no-parallel','--scratch-path',str(root/'swift633'),'-j','2','--enable-code-coverage','--filter','PreparedClassificationIntegrationTests|ClassificationPipelineConcurrencyTests|PreparedRowMappingTests|PreparedLogisticRegressionTests|BinaryCrossEntropyTests']))
fingerprints=lambda:{str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for base in ('Sources','Tests') for p in (source/base).rglob('*.swift')}
before=fingerprints();report={'swift':subprocess.check_output(['swift','--version'],env=env,text=True),'sources':before,'steps':[],'focused_execution':'Explicit --no-parallel serializes suite starts to avoid observed pinned-MLX lazy stream/evaluation initialization lock cycle; concurrency tests still execute their own concurrent tasks'}
assert 'Swift version 6.3.3' in report['swift']
for name,command in commands:
 if name == 'focused-prepared-tests':
  metal = root/'derived/Build/Products/Debug/mlx-swift_Cmlx.bundle/Contents/Resources/default.metallib'
  destination = root/'swift633/arm64-apple-macosx/debug/SwiftSciPackageTests.xctest/Contents/MacOS/mlx.metallib'
  native_mlx = subprocess.check_output(['git','rev-parse','HEAD'], cwd=root/'native-packages/checkouts/mlx-swift', text=True).strip()
  compatibility_mlx = subprocess.check_output(['git','rev-parse','HEAD'], cwd=root/'swift633/checkouts/mlx-swift', text=True).strip()
  assert native_mlx == compatibility_mlx
  import shutil
  shutil.copy2(metal,destination)
  digest = hashlib.sha256(metal.read_bytes()).hexdigest()
  assert hashlib.sha256(destination.read_bytes()).hexdigest() == digest
  report['metal_runtime_resource'] = dict(source=str(metal),destination=str(destination),sha256=digest,mlx_revision=native_mlx,scope='Metal resource compiled by retained Xcode27, runtime on this Mac; Swift6.3.3 host code and all test targets built separately withSDK26.5, not an older-Xcode Metal compilation or older-OS qualification')
 start=time.time()
 with (out/(name+'.log')).open('w') as stream:result=subprocess.run(command,cwd=source,env=env,stdout=stream,stderr=subprocess.STDOUT)
 report['steps'].append({'name':name,'command':command,'exit_code':result.returncode,'seconds':time.time()-start})
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
 print(name,result.returncode,flush=True)
 assert before==fingerprints(),'source changed during compatibility checks'
 if result.returncode:raise SystemExit(result.returncode)
report['status']='passed';(out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
