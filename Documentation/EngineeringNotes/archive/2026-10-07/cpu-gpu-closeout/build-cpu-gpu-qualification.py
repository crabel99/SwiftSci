from pathlib import Path
import subprocess,json,sys,shutil,hashlib
root=Path('/Users/LOCAL_USER/Library/Caches/SwiftSci/retained-gpu-trial-20261007')
out=Path('/Users/LOCAL_USER/local-ai/spl/swiftsci/cpu-gpu-closeout-20261007')
manifest=root/'Package.swift';original=manifest.read_bytes();target=root/'Benchmarks/PreparedMemoryQualification'
assert not target.exists()
assert not subprocess.check_output(['git','status','--porcelain'],cwd=root).strip()
shutil.copytree(out/'qualification-sources',target)
addition='''        .executableTarget(
            name: "SwiftSciPreparedMemoryQualification",
            dependencies: ["SwiftML", "SwiftPreprocessing", .product(name: "MLX", package: "mlx-swift")],
            path: "Benchmarks/PreparedMemoryQualification"
        ),
'''
cmd=json.loads((out/'Release-command.json').read_text());cmd[1]='build-for-testing'
cmd[cmd.index('-scheme')+1]='SwiftSci-Package'
for flag in ['-resultBundlePath']:
 i=cmd.index(flag);del cmd[i:i+2]
cmd=[a for a in cmd if not a.startswith('-only-testing:')]
sys.path.insert(0,'/Users/LOCAL_USER/Library/Caches/SwiftSci/prepared-memory-integration-20261006-qualification/Benchmarks/UnifiedMemoryPrototype')
from processes import run_process
try:
 manifest.write_text(original.decode().replace('    targets: [\n','    targets: [\n'+addition,1))
 (out/'qualification-Package.swift').write_bytes(manifest.read_bytes())
 (out/'qualification-command.json').write_text(json.dumps(cmd,indent=2)+'\n')
 with (out/'qualification-build.log').open('w') as log:r=run_process(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=900)
 print('build exit',r.returncode)
 if r.returncode:print('\n'.join(l[:900] for l in (out/'qualification-build.log').read_text().splitlines() if 'error:' in l))
finally:
 manifest.write_bytes(original)
 # Remove only the temporary directory created by this script from archived sources.
 shutil.rmtree(target)
assert not subprocess.check_output(['git','status','--porcelain'],cwd=root).strip()
sys.exit(r.returncode)
