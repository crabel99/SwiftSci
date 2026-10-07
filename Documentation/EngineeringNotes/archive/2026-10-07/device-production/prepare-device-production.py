from pathlib import Path
import hashlib,json,shutil,subprocess
root=Path('/Users/crabel/Library/Caches/SwiftSci/retained-gpu-trial-20261007')
out=Path('/Users/crabel/local-ai/spl/swiftsci/device-production-20261007');out.mkdir(exist_ok=False)
worker=Path('/Users/crabel/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release/SwiftSciRetainedGPUTrial')
p=json.loads(Path('/Users/crabel/local-ai/spl/swiftsci/device-reuse-20261007/comparison/provenance.json').read_text())
assert hashlib.sha256(worker.read_bytes()).hexdigest()==p['binary_sha256']
for name,digest in p['source_sha256'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
baseline=worker.with_name('SwiftSciRetainedGPUTrial-device-production-baseline')
assert not baseline.exists();shutil.copy2(worker,baseline)
p.update(commit='98f9a9268aa2fa82beada688b00b7ddb74171e00',binary_path=str(baseline))
(out/'baseline-provenance.json').write_text(json.dumps(p,indent=2)+'\n')
for name in ['ScopedGPURead.swift','RetainedGPUInputTrial.swift']:
 path=root/'Sources/SwiftPreprocessing/Core'/name
 s=path.read_text();assert s.count('MTLCreateSystemDefaultDevice()')==1
 path.write_text(s.replace('MTLCreateSystemDefaultDevice()', 'MetalDeviceOwner.defaultDevice'))
(root/'Sources/SwiftPreprocessing/Core/MetalDeviceOwner.swift').write_text('''import Metal

/// Retains the default device for shared-buffer allocations, without retaining buffers.
enum MetalDeviceOwner {
    private static let initialDevice = MTLCreateSystemDefaultDevice()

    static var defaultDevice: (any MTLDevice)? {
        // A failed initial lookup must not make later allocation attempts fail permanently.
        initialDevice ?? MTLCreateSystemDefaultDevice()
    }
}
''')
s=Path('/private/tmp/run-device-reuse-tests.py').read_text().replace('device-reuse-20261007','device-production-20261007')
Path('/private/tmp/run-device-production-tests.py').write_text(s)
assert int(subprocess.check_output(['sysctl','-n','kern.memorystatus_vm_pressure_level']))==1
print('Baseline preserved',baseline)
