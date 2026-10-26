from pathlib import Path
import gzip,hashlib,json,shutil,tarfile,subprocess,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;out=r/'records';out.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def copy(relative,destination=None):
 p=r/relative;target=out/(destination or relative);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
for name in ['README.md','qualification.json','production.patch','plan.md','spec-review.md','standards-review.md',
 'how-synthesis.md','adapter-grounding.md','evidence-grounding.md','harness-grounding.md','multiclass-export-assessment.md',
 'CoreMLExportProbe.swift','RepresentativeWorkflowProbe.swift','CorrectSoftmax.mlmodel',
 'verify-qualification.py','validate-native.py','check-swift633.py','full-ci-runner.py','benchmark-ci-runner.py',
 'run-representative.py','trace-trained.py','inspect-traces.py','summarize-trained.py','package-records.py',
 'study-requirements.txt','study-environment.log','trained-environment-failure.log','trained-environment-failure.command.json',
 'trained.command.json','coreml-controller-tests.log','softmax-schema-probe.log','softmax-schema-compile.log',
 'export-before/result.json','export-before/run.log','export-before/proof.json','export-before/artifacts/ThreeClasses.mlmodel',
 'workflow-probe/wdbc.json','workflow-probe/wine.json','workflow-probe/binding.json','workflow-probe/proof.json',
 'compatibility/multiclass-tests.json','compatibility/multiclass-tests.log','compatibility/multiclass-coverage.json','compatibility/multiclass-coreml.lcov',
 'traces/inspected-events.json','traces/provenance.json','traces/results.json','inspect-traces.log']:
 copy(name)
copy('../swiftsci-gpu-logistic-correctness-20261026/verification/link-public-probe.py','link-public-probe.py')
copy('ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker.build.json','worker-build.json')
compression={}
transforms={}
logs=[]
for d in ['native-export-red','native-export-green','native-export-green-native','native-full-debug','native-full-release','compatibility','ci-main','ci-bench','ci-security-python']:
 for p in (r/d).glob('*.log'):logs.append(p)
 for p in (r/d).glob('*.json'):
  if p.name!='coverage.json':copy(str(p.relative_to(r)))
for p in sorted(set(logs)):
 relative=p.relative_to(r);target=out/(str(relative)+'.gz');target.parent.mkdir(parents=True,exist_ok=True)
 target.write_bytes(gzip.compress(p.read_bytes(),compresslevel=6,mtime=0))
 compression[str(target.relative_to(out))]=dict(original_path=str(p),original_sha256=sha(p),original_size_bytes=p.stat().st_size)
for name in ['wdbc-cpu','wdbc-neural','wine-cpu','wine-neural']:
 for suffix in ['.json','.request.json','.command.json','.log','-uninstrumented.json','-uninstrumented.request.json','-uninstrumented.log']:
  copy('traces/'+name+suffix)
 for suffix in ['.coreml.xml','.intervals.xml','.ane.xml']:
  p=r/'traces'/(name+suffix);target=out/'traces'/(name+suffix+'.gz')
  target.write_bytes(gzip.compress(p.read_bytes(),compresslevel=6,mtime=0))
  compression[str(target.relative_to(out))]=dict(original_path=str(p),original_sha256=sha(p),original_size_bytes=p.stat().st_size)
 toc=r/'traces'/(name+'.toc.xml');tree=E.parse(toc)
 for device in tree.findall('.//device'):
  for key in ['name','uuid']:device.attrib.pop(key,None)
 published=out/'traces'/(name+'.toc.xml');tree.write(published,encoding='utf-8',xml_declaration=True)
 transforms[str(published.relative_to(out))]=dict(original_sha256=sha(toc),published_sha256=sha(published),redaction='Device name and UUID removed; launched process and table scope preserved')
(out/'publication-transforms.json').write_text(json.dumps(transforms,indent=2)+'\n')
with tarfile.open(out/'trained-results.tar.gz','w:gz') as tar:tar.add(r/'trained-results',arcname='trained-results')
with tarfile.open(out/'ci-comparisons.tar.gz','w:gz') as tar:
 for p in sorted((r/'ci-bench').rglob('*')):
  if p.is_file() and p.parent!=r/'ci-bench' and p.suffix in ['.json','.log','.md','.sarif']:
   tar.add(p,arcname=str(p.relative_to(r)))
(out/'compression-map.json').write_text(json.dumps(compression,indent=2)+'\n')
files=sorted(p for p in out.rglob('*') if p.is_file())
(out/'FILES.sha256').write_text(''.join(f'{sha(p)}  {p.relative_to(out)}\n' for p in files))
for p in files:
 assert p.stat().st_size<50_000_000,(p,p.stat().st_size)
print(json.dumps(dict(files=len(files)+1,total_bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))))
