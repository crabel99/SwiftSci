from pathlib import Path
import argparse,hashlib,json,shlex,subprocess
p=argparse.ArgumentParser()
p.add_argument('--build-log',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--prepared',action='store_true')
p.add_argument('--source',type=Path)
a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
probe=(a.source or Path(__file__).with_name('PublicClassificationProbe.swift')).resolve()
compile_base=link=None
for line in a.build_log.read_text().splitlines():
    args=shlex.split(line)
    if args[:2]==['builtin-SwiftDriver','--'] and '-module-name' in args and args[args.index('-module-name')+1]=='SwiftSciBenchmarkWorker':compile_base=args[2:]
    if '-o' in args and args[args.index('-o')+1].endswith('/SwiftSciBenchmarkWorker'):link=args
assert compile_base and link
command=[compile_base[0],'-parse-as-library','-swift-version','6','-module-name','PublicClassificationProbe','-module-cache-path',str(out/'module-cache')]
if a.prepared:command+=['-D','PREPARED']
i=1
while i<len(compile_base):
    arg=compile_base[i]
    if arg in ['-sdk','-target','-I','-F','-Isystem','-Fsystem']:
        command+=compile_base[i:i+2];i+=2;continue
    if arg=='-Xcc' and i+1<len(compile_base):
        value=compile_base[i+1]
        if value.startswith(('-fmodule-map-file=','-I','-D')):command +=[arg,value]
        i+=2;continue
    if arg.startswith(('-I/','-F/')):command.append(arg)
    i+=1
command+=['-c',str(probe),'-o',str(out/'probe.o')]
with (out/'compile.log').open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
response=next(arg[1:] for arg in link if arg.startswith('@') and arg.endswith('.LinkFileList'))
objects=[obj for obj in shlex.split(Path(response).read_text()) if '/SwiftSciBenchmarkWorker-p.build/' not in obj]
new_response=out/'probe.LinkFileList';new_response.write_text('\n'.join(objects+[str(out/'probe.o')])+'\n')
new=[];i=0
while i<len(link):
    if link[i:i+2] in [['-Xlinker','-object_path_lto'],['-Xlinker','-dependency_info'],['-Xlinker','-add_ast_path'],['-Xlinker','-final_output']]:
        assert link[i+2]=='-Xlinker';i+=4;continue
    if link[i]=='@'+response:new.append('@'+str(new_response));i+=1;continue
    if link[i]=='-o':new+=['-o',str(out/'probe')];i+=2;continue
    new.append(link[i]);i+=1
with (out/'link.log').open('w') as log:subprocess.run(new,stdout=log,stderr=subprocess.STDOUT,check=True)
proof={'compile':command,'link':new,'input_build_log':str(a.build_log.resolve()),'input_build_log_sha256':hashlib.sha256(a.build_log.read_bytes()).hexdigest(),'probe_source_sha256':hashlib.sha256(probe.read_bytes()).hexdigest(),'objects':{obj:hashlib.sha256(Path(obj).read_bytes()).hexdigest() for obj in objects},'binary_sha256':hashlib.sha256((out/'probe').read_bytes()).hexdigest()}
(out/'proof.json').write_text(json.dumps(proof,indent=2)+'\n')
print(out/'probe')
