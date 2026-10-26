from pathlib import Path
import hashlib,json,subprocess,sys
root=Path(__file__).resolve().parent
products=Path(sys.argv[1]);name=sys.argv[2]
derived=products.parents[2]
packages=Path('/Users/crabel/Library/Caches/SwiftSci/mlx-simd-backport-20261006/swiftsci/.build')
objects=['SwiftCluster','SwiftPreprocessing','SwiftStats','SwiftDataFrame','Arrow','ArrowC','FlatBuffers','MLX','MLXNN','Cmlx','ComplexModule','Numerics','RealModule','cLogSupport','_NumericsShims','Atomics','_AtomicsShims']
cmd=['xcrun','swiftc','-O','-parse-as-library','-I',str(products),'-package-name','SwiftSci','-module-cache-path',str(root/'module-cache')]
for module in ['ArrowC','cLogSupport']:
 cmd+=['-Xcc','-fmodule-map-file='+str(derived/'Build/Intermediates.noindex/GeneratedModuleMaps'/f'{module}.modulemap')]
cmd+=['-Xcc','-fmodule-map-file='+str(packages/'checkouts/mlx-swift/Source/Cmlx/include/module.modulemap')]
cmd+=['-Xcc','-fmodule-map-file='+str(packages/'checkouts/swift-atomics/Sources/_AtomicsShims/include/module.modulemap')]
cmd+=['-Xcc','-fmodule-map-file='+str(packages/'checkouts/swift-numerics/Sources/_NumericsShims/include/module.modulemap')]
for subdir in ['mlx-c','mlx']:
 cmd+=['-Xcc','-I'+str(packages/'checkouts/mlx-swift/Source/Cmlx'/subdir)]
if name!='baseline':cmd+=['-D','PREPARED_PCA']
cmd += [str(root/'Workflow.swift')]+[str(products/(p+'.o')) for p in objects]
for framework in ['Accelerate','Metal','Foundation','CoreImage','CoreGraphics','AVFoundation']:
 cmd+=['-framework',framework]
cmd+=['-lc++','-lcompression','-lz','-o',str(root/name)]
with (root/(name+'-build.log')).open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
record={'command':cmd,'exit_code':r.returncode,'source_sha256':hashlib.sha256((root/'Workflow.swift').read_bytes()).hexdigest(),'objects':{p:hashlib.sha256((products/(p+'.o')).read_bytes()).hexdigest() for p in objects}}
if r.returncode==0:record['binary_sha256']=hashlib.sha256((root/name).read_bytes()).hexdigest()
(root/(name+'-build.json')).write_text(json.dumps(record,indent=2)+'\n')
print(name,'build',r.returncode)
raise SystemExit(r.returncode)
