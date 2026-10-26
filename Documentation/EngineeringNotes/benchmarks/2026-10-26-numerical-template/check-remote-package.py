from pathlib import Path
import argparse, hashlib, json, subprocess, time
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
r=Path(__file__).resolve().parent;out=a.output.resolve();out.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
head='0e1635199654ac6a20b32ea53eea0ffdfa39e747'
report=dict(source=head,manifest_sha256=sha(r/'template/Package.swift'),consumer_sha256=sha(r/'template/Sources/ScientificWorkflow/ScientificWorkflow.swift'),steps=[],controller_sha256=sha(Path(__file__)))
base=['xcodebuild','-scheme','ScientificWorkflow','-configuration','Release','-destination','platform=macOS,arch=arm64','-derivedDataPath',str(out/'derived'),'-clonedSourcePackagesDirPath',str(out/'packages'),'-jobs','4']
commands=[('resolve',base+['-resolvePackageDependencies']),('build',base+['MTL_FAST_MATH=NO','MTL_MATH_MODE=SAFE','MTL_MATH_FP32_FUNCTIONS=PRECISE','build'])]
for name,command in commands:
 start=time.time()
 with (out/(name+'.log')).open('w') as f:
  q=subprocess.run(command,cwd=r/'template',stdout=f,stderr=subprocess.STDOUT,timeout=1800)
 report['steps'].append(dict(name=name,command=command,exit_code=q.returncode,seconds=time.time()-start,log_sha256=sha(out/(name+'.log'))))
 (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
 print(name,q.returncode,flush=True);assert q.returncode==0
 if name=='resolve':
  checkout=out/'packages/checkouts/SwiftSci'
  assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=checkout,text=True).strip()==head
  assert subprocess.check_output(['git','status','--porcelain'],cwd=checkout,text=True)==''
  qualified=Path('/private/tmp/swiftsci-llm-completion-20261026/source')
  files=subprocess.check_output(['git','ls-files','Sources','Package.swift'],cwd=qualified,text=True).splitlines()
  assert all((checkout/n).read_bytes()==(qualified/n).read_bytes() for n in files)
  report['remote_checkout']=dict(commit=head,remote=subprocess.check_output(['git','remote','get-url','origin'],cwd=checkout,text=True).strip(),files={n:sha(checkout/n) for n in files})
binary=out/'derived/Build/Products/Release/ScientificWorkflow'
with (out/'result.json').open('w') as stdout,(out/'run.log').open('w') as stderr:
 start=time.time();q=subprocess.run([str(binary)],cwd=r/'template',stdout=stdout,stderr=stderr,timeout=60)
report['steps'].append(dict(name='run',command=[str(binary)],exit_code=q.returncode,seconds=time.time()-start,log_sha256=sha(out/'run.log')))
(out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');assert q.returncode==0
assert json.loads((out/'result.json').read_text())==json.loads((r/'final-run-qualified/prepared.json').read_text())
report.update(status='passed',binary_sha256=sha(binary),result_sha256=sha(out/'result.json'),result='Exact JSON equality with independently verified prepared workflow')
(out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print('remote package passed',flush=True)
