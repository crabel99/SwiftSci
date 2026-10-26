from pathlib import Path
import hashlib,json,shlex,subprocess
out=Path(__file__).resolve().parent
baseline=Path('/private/tmp/swiftsci-prepared-pca-20261026/baseline-standardized')
products=baseline/'derived/Build/Products/Release'
receipt=json.loads((products/'SwiftSciBenchmarkWorker.build.json').read_text())
source=Path('/private/tmp/swiftsci-prepared-classification-20261026/source')
for name in ['Sources/SwiftML/Core/LogisticRegression.swift','Sources/SwiftML/Core/Numerics.swift']:
    old=subprocess.check_output(['git','show','e19db7dda4567c425b7eb002da82e234e6c7980f:'+name],cwd=source)
    assert hashlib.sha256(old).hexdigest()==receipt['source']['files'][name], name
compile_base=None
link=None
for line in (baseline/'build.log').read_text().splitlines():
    a=shlex.split(line)
    if a[:2]==['builtin-SwiftDriver','--'] and '-module-name' in a and a[a.index('-module-name')+1]=='SwiftSciBenchmarkWorker': compile_base=a[2:]
    if '-o' in a and a[a.index('-o')+1].endswith('/SwiftSciBenchmarkWorker'): link=a
assert compile_base and link
compile=[compile_base[0],'-parse-as-library','-swift-version','6','-module-name','BaselineLogisticProbe','-module-cache-path',str(out/'probe-module-cache')]
i=1
while i<len(compile_base):
    a=compile_base[i]
    if a in ['-sdk','-target','-I','-F','-Isystem','-Fsystem']:
        compile += compile_base[i:i+2]; i+=2; continue
    if a=='-Xcc' and i+1<len(compile_base):
        value=compile_base[i+1]
        if value.startswith(('-fmodule-map-file=','-I','-D')): compile += [a,value]
        i+=2; continue
    if a.startswith(('-I/','-F/')): compile.append(a)
    i+=1
compile += ['-c',str(out/'BaselineLogisticProbe.swift'),'-o',str(out/'baseline-probe.o')]
with (out/'baseline-probe-compile.log').open('w') as stream:
    subprocess.run(compile,stdout=stream,stderr=subprocess.STDOUT,check=True)
response=next(a[1:] for a in link if a.startswith('@') and a.endswith('.LinkFileList'))
objects=[p for p in shlex.split(Path(response).read_text()) if '/SwiftSciBenchmarkWorker-p.build/' not in p]
new_response=out/'baseline-probe.LinkFileList'
new_response.write_text('\n'.join(objects+[str(out/'baseline-probe.o')])+'\n')
new=[];i=0
while i<len(link):
    if link[i:i+2] in [['-Xlinker','-object_path_lto'],['-Xlinker','-dependency_info'],['-Xlinker','-add_ast_path'],['-Xlinker','-final_output']]:
        assert link[i+2]=='-Xlinker';i+=4;continue
    if link[i]=='@'+response: new.append('@'+str(new_response));i+=1;continue
    if link[i]=='-o':new+=['-o',str(out/'baseline-probe')];i+=2;continue
    new.append(link[i]);i+=1
with (out/'baseline-probe-link.log').open('w') as stream:
    subprocess.run(new,stdout=stream,stderr=subprocess.STDOUT,check=True)
with (out/'logistic-old-binary.json').open('w') as stream:
    subprocess.run([str(out/'baseline-probe')],cwd=products,stdout=stream,check=True)
proof={'baseline_build_receipt':str(products/'SwiftSciBenchmarkWorker.build.json'),'baseline_source':receipt['source'], 'compile':compile,'link':new,'objects':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in objects},'probe_sha256':hashlib.sha256((out/'baseline-probe').read_bytes()).hexdigest(),'result_sha256':hashlib.sha256((out/'logistic-old-binary.json').read_bytes()).hexdigest()}
(out/'baseline-probe-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
print('Captured original compiled LogisticRegression on CPU/GPU/auto/ANE for epochs0/1/4')
