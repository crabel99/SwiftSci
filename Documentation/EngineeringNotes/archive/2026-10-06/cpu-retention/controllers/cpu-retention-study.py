import json,shutil,subprocess,sys,tempfile,os
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');sys.path.insert(0,str(root/'Benchmarks/UnifiedMemoryPrototype'))
import run as c
from processes import run_process
from mixed_device import check_memory_pressure
out=Path('/Users/crabel/local-ai/spl/swiftsci/cpu-retention-20261006');out.mkdir(exist_ok=True)
worker=c.CACHE/'derived/Build/Products/Release/SwiftSciMemoryIntegrationPrototype'
base=json.loads(Path(str(worker)+'.build.json').read_text())
assert all(c.digest(root/n)==v for n,v in base['files'].items())
fixed=worker.with_name('SwiftSciMatrixCleanupFixed');assert c.digest(fixed)==base['binary_sha256']
env={k:v for k,v in os.environ.items() if k not in c.THREAD_OVERRIDES}
for profile in ['cpu-same','cpu-sizes']:
 check_memory_pressure(out,{'phase':'reproduce','profile':profile})
 r=c.invoke_admission([str(fixed),'--retained-memory',profile,'retain','3','sequence'],env,out,{'profile':profile},expected_job_count=None,timeout=45)
 c.write(out/(profile+'-current.json'),r)
 ready=r['records'][0]['memory'];last=r['records'][-1]['after_intervention']
 print(profile,'footprint growth MiB', (last['physical_footprint_bytes']-ready['physical_footprint_bytes'])/1048576,'live malloc growth MiB',(last['malloc_bytes_in_use']-ready['malloc_bytes_in_use'])/1048576,flush=True)
source=Path(tempfile.mkdtemp(prefix='source-cpu-retention-',dir=c.CACHE))
for n in base['files']:
 dest=source/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/n,dest)
p=source/'Benchmarks/UnifiedMemoryPrototype/Integration/RetainedMemory.swift';s=p.read_text()
helper='''
// Disposable profiling instrumentation. The enclosing controller owns a deadline.
private func cpuVMCheckpoint(_ phase: String) throws {
    guard let path = ProcessInfo.processInfo.environment["CPU_VM_MAP"] else { return }
    let url = URL(fileURLWithPath: path).appendingPathComponent(phase + ".txt")
    FileManager.default.createFile(atPath: url.path, contents: nil)
    let handle = try FileHandle(forWritingTo: url)
    defer { try? handle.close() }
    let process = Process()
    process.executableURL = URL(fileURLWithPath: "/usr/bin/vmmap")
    process.arguments = ["-summary", String(getpid())]
    process.standardOutput = handle
    process.standardError = handle
    try process.run()
    process.waitUntilExit()
    try expect(process.terminationStatus == 0, "VM checkpoint succeeds")
}
'''
s=s.replace('private struct RetentionEvidence',helper+'\nprivate struct RetentionEvidence')
s=s.replace('    var references = [(ConcurrentShape, MixedResult)]()', '    try cpuVMCheckpoint("inputs-ready")\n    var references = [(ConcurrentShape, MixedResult)]()')
s=s.replace('    withExtendedLifetime(inputs) {}','    withExtendedLifetime(inputs) {}')
s=s.replace('                            "malloc_reported_released_bytes": released])','                            "malloc_reported_released_bytes": released])\n            if step == 2 && (cycle == 0 || cycle == cycles - 1) { try cpuVMCheckpoint("cycle-\\(cycle + 1)") }')
s=s.replace('try await warmCalibrationRuntime(.cpu); try await warmCalibrationRuntime(.gpu)','try await warmCalibrationRuntime(.cpu)\n    if ProcessInfo.processInfo.environment["CPU_WARMUP_ONLY"] != "1" { try await warmCalibrationRuntime(.gpu) }')
s=s.replace('    let warmed = try retentionSnapshot()','    let warmed = try retentionSnapshot()\n    try cpuVMCheckpoint("warmed")')
s=s.replace('    let dropped = try retentionSnapshot()','    let dropped = try retentionSnapshot()\n    try cpuVMCheckpoint("inputs-dropped")')
s=s.replace('    let relieved = try retentionSnapshot()','    let relieved = try retentionSnapshot()\n    try cpuVMCheckpoint("final-cleanup")')
p.write_text(s)
p=source/'Benchmarks/UnifiedMemoryPrototype/Integration/main.swift';s=p.read_text();assert s.count('(1...3).contains(cycles)')==1;s=s.replace('(1...3).contains(cycles)','(1...12).contains(cycles)');p.write_text(s)
for name in ['RetainedMemory.swift','main.swift']:
 rel='Benchmarks/UnifiedMemoryPrototype/Integration/'+name
 diff=subprocess.run(['diff','-u',str(root/rel),str(source/rel)],text=True,capture_output=True)
 (out/(name+'.patch')).write_text(diff.stdout)
(out/'source.txt').write_text(str(source)+'\n')
with (out/'build.log').open('w') as log:
 r=run_process(base['command'],cwd=source,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
assert r.returncode==0,'See build.log'
copy=worker.with_name('SwiftSciCPURetentionProfile');shutil.copy2(worker,copy)
c.write(out/'build.json',dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),source=str(source),command=base['command'],files={n:c.digest(source/n) for n in base['files']},binary_sha256=c.digest(copy),scope='Disposable profiling snapshot. Optional CPU-only warmup and phase VM maps; raises bounded cycle maximum to 12. Production sources unchanged.'))
shutil.copy2(fixed,worker)
assert c.digest(worker)==base['binary_sha256']
print('BUILD PASSED',copy,flush=True)
