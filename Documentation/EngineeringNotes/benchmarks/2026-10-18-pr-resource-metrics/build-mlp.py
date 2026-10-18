from pathlib import Path
import subprocess,json,hashlib,time,sys
R=Path(__file__).resolve().parent;P=Path('/Users/crabel/Library/Caches/SwiftSci/mixed-workloads-derived/Build/Products/Release');C=Path('/Users/crabel/Library/Caches/SwiftSci/xcode-packages/checkouts')
SDK=subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip()
common=['-package-name','swiftsci_csv_sort_20261017','-O','-whole-module-optimization','-swift-version','6','-enable-upcoming-feature','ExistentialAny','-target','arm64-apple-macos14.0','-sdk',SDK,'-I',str(P),'-module-cache-path',str(R/'module-cache')]
for m in [P.parent.parent/'Intermediates.noindex/GeneratedModuleMaps/ArrowC.modulemap',C/'swift-atomics/Sources/_AtomicsShims/include/module.modulemap',C/'mlx-swift/Source/Cmlx/include/module.modulemap',C/'swift-numerics/Sources/_NumericsShims/include/module.modulemap',P.parent.parent/'Intermediates.noindex/GeneratedModuleMaps/cLogSupport.modulemap']:
 common += ['-Xcc','-fmodule-map-file='+str(m)]
common += ['-Xcc','-I'+str(C/'mlx-swift/Source/Cmlx/include')]
objects=['SwiftDataFrame','SwiftStats','SwiftPreprocessing','Arrow','ArrowC','FlatBuffers','Atomics','_AtomicsShims','MLX','Cmlx','ComplexModule','Numerics','RealModule','_NumericsShims','cLogSupport']
for label in sys.argv[1:]:
 v=json.loads((R/'variants.json').read_text())[label];D=R/'build'/label;D.mkdir(parents=True,exist_ok=True);start=time.time()
 sources=sorted((Path(v['path'])/'Sources/SwiftML').rglob('*.swift'))
 cmd=['xcrun','swiftc',*common,'-parse-as-library','-module-name','SwiftML','-emit-module','-emit-module-path',str(D/'SwiftML.swiftmodule'),'-emit-object','-o',str(D/'SwiftML.o'),*[str(s) for s in sources]]
 sig={'command':cmd,'sources':{str(s):hashlib.sha256(s.read_bytes()).hexdigest() for s in sources}};sp=D/'module-signature.json'
 if not sp.exists() or json.loads(sp.read_text())!=sig:
  with (D/'module.log').open('w') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  if p.returncode:print((D/'module.log').read_text()[-7000:]);raise SystemExit(p.returncode)
  sp.write_text(json.dumps(sig,indent=2)+'\n')
 cmd2=['xcrun','swiftc','-I',str(D),*common,'-parse-as-library',str(R/'MLPProbe.swift'),str(D/'SwiftML.o'),*[str(P/(s+'.o')) for s in objects],'-framework','Accelerate','-framework','CoreML','-framework','Metal','-framework','MetalPerformanceShaders','-lc++','-lcompression','-o',str(D/'MLPProbe')]
 with (D/'link.log').open('w') as log:p=subprocess.run(cmd2,stdout=log,stderr=subprocess.STDOUT)
 if p.returncode:print((D/'link.log').read_text()[-7000:]);raise SystemExit(p.returncode)
 record={'variant':v,'commands':[cmd,cmd2],'sources':sig['sources'],'seconds':time.time()-start,'harness_sha256':hashlib.sha256((R/'MLPProbe.swift').read_bytes()).hexdigest(),'binary_sha256':hashlib.sha256((D/'MLPProbe').read_bytes()).hexdigest(),'dependency_objects':{s:hashlib.sha256((P/(s+'.o')).read_bytes()).hexdigest() for s in objects}}
 (D/'build.json').write_text(json.dumps(record,indent=2)+'\n');print(label,'built',round(time.time()-start,1),flush=True)
