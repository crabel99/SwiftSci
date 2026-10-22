from pathlib import Path
import subprocess,json,hashlib,time,sys
R=Path(__file__).resolve().parent
P=Path('/Users/crabel/Library/Caches/SwiftSci/mixed-workloads-derived/Build/Products/Release')
M=P.parent.parent/'Intermediates.noindex/GeneratedModuleMaps/ArrowC.modulemap'
A=Path('/Users/crabel/Library/Caches/SwiftSci/xcode-packages/checkouts/swift-atomics/Sources/_AtomicsShims/include/module.modulemap')
SDK=subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip()
common=['-package-name','SwiftSci','-O','-whole-module-optimization','-swift-version','6','-enable-upcoming-feature','ExistentialAny','-target','arm64-apple-macos14.0','-sdk',SDK,'-I',str(P),'-Xcc','-fmodule-map-file='+str(M),'-Xcc','-fmodule-map-file='+str(A),'-module-cache-path',str(R/'module-cache')]
for label in sys.argv[1:]:
 v=json.loads((R/'variants.json').read_text())[label];D=R/'build'/label;D.mkdir(parents=True,exist_ok=True)
 sources=sorted((Path(v['path'])/'Sources/SwiftDataFrame').rglob('*.swift'))
 cmd=['xcrun','swiftc',*common,'-parse-as-library','-module-name','SwiftDataFrame','-emit-module','-emit-module-path',str(D/'SwiftDataFrame.swiftmodule'),'-emit-object','-o',str(D/'SwiftDataFrame.o'),*[str(s) for s in sources]]
 start=time.time()
 module_signature={'command':cmd,'sources':{str(s):hashlib.sha256(s.read_bytes()).hexdigest() for s in sources}}
 sig=D/'module-signature.json'
 if not sig.exists() or json.loads(sig.read_text()) != module_signature:
  with (D/'module.log').open('w') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  if p.returncode:print((D/'module.log').read_text()[-5000:]);raise SystemExit(p.returncode)
  sig.write_text(json.dumps(module_signature,indent=2)+'\n')
 defines=['-D','HAS_COMPACT'] if v['pr']==82 else []
 cmd2=['xcrun','swiftc','-I',str(D),*common,*defines,'-parse-as-library',str(R/'ResourceProbe.swift'),str(D/'SwiftDataFrame.o'),*[str(P/(s+'.o')) for s in ['Arrow','ArrowC','FlatBuffers','Atomics','_AtomicsShims']],'-framework','Accelerate','-lcompression','-o',str(D/'ResourceProbe')]
 with (D/'link.log').open('w') as log:p=subprocess.run(cmd2,stdout=log,stderr=subprocess.STDOUT)
 if p.returncode:print((D/'link.log').read_text()[-5000:]);raise SystemExit(p.returncode)
 receipt={'variant':v,'commands':[cmd,cmd2],'seconds':time.time()-start,'sources':{str(s.relative_to(v['path'])):hashlib.sha256(s.read_bytes()).hexdigest() for s in sources},'harness_sha256':hashlib.sha256((R/'ResourceProbe.swift').read_bytes()).hexdigest(),'binary_sha256':hashlib.sha256((D/'ResourceProbe').read_bytes()).hexdigest(),'dependency_objects':{s:hashlib.sha256((P/(s+'.o')).read_bytes()).hexdigest() for s in ['Arrow','ArrowC','FlatBuffers','Atomics','_AtomicsShims']}}
 (D/'build.json').write_text(json.dumps(receipt,indent=2)+'\n');print(label,'built',round(time.time()-start,1),flush=True)
