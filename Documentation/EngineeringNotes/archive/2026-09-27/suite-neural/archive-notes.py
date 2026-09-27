import hashlib,json,os,subprocess,tempfile
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');work=Path('/private/tmp/swiftsci-suite-neural');archive='Documentation/EngineeringNotes/archive/2026-09-27/suite-neural/'
def git(*args,**kwargs):return subprocess.check_output(['git','-C',str(root),*args],**kwargs).decode().strip()
base=git('rev-parse','codex/engineering-notes');assert base==git('rev-parse','origin/codex/engineering-notes')
head=git('rev-parse','HEAD');index_tree=git('write-tree')
files={'Documentation/EngineeringNotes/benchmarks/2026-09-27-neural-suite.md':(work/'report.md').read_bytes()}
for p in work.rglob('*'):
 if p.is_file() and '__pycache__' not in p.parts and p.name not in ('notes-commit.txt',):
  files[archive+str(p.relative_to(work))]=p.read_bytes()
for name in ['suite-neural-01','suite-neural-loader-01','suite-neural-03','suite-neural-loader-02','suite-neural-cpu-01','suite-neural-smoke-01']:
 for p in (root/'Benchmarks/Runs'/name).iterdir():
  if p.is_file():files[archive+'runs/'+name+'/'+p.name]=p.read_bytes()
path='Documentation/EngineeringNotes/benchmarks/2026-09-27-dataset-strategy.md'
s=git('show',base+':'+path)
s+='\n\n## Fixed neural inference checkpoint\n\nLocal commit `f8cec1f93b` adds fourteen fixed decoder fixture packs with independent logits and exact parameter readback. All 105 controller tests pass. Direct inference passes 23 of 24 engine cases; batched GPU cached RoPE fails, while both single-batch controls pass. Both Swift public-loader cases expose incomplete parameter replacement. CPU CI and smoke profiles pass and certify. Sixteen controls pass and all 56 deliberately invalid worker cases reject. See [the neural report](2026-09-27-neural-suite.md). No production fixes or formal performance baseline were included. Complete remaining integration coverage before the separate repair branch.\n'
files[path]=s.encode()
files[archive+'manifest.json']=(json.dumps({name:dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest()) for name,data in sorted(files.items())},indent=2)+'\n').encode()
with tempfile.TemporaryDirectory(prefix='swiftsci-notes-index-') as directory:
 env=dict(os.environ,GIT_INDEX_FILE=str(Path(directory)/'index'));git('read-tree',base,env=env)
 for name,data in files.items():
  blob=git('hash-object','-w','--stdin',input=data);git('update-index','--add','--cacheinfo','100644,'+blob+','+name,env=env)
 tree=git('write-tree',env=env);commit=git('commit-tree',tree,'-p',base,input=b'docs(engineering): record neural conformance evidence\n');git('update-ref','refs/heads/codex/engineering-notes',commit,base)
 (work/'notes-commit.txt').write_text(commit+'\n')
 for name,data in files.items():assert subprocess.check_output(['git','-C',str(root),'show',commit+':'+name])==data
 assert head==git('rev-parse','HEAD');assert index_tree==git('write-tree')
 assert all(name.startswith('Documentation/EngineeringNotes/') for name in git('diff-tree','--no-commit-id','--name-only','-r',commit).splitlines())
 print('Notes commit:',commit,'Files:',len(files),'Bytes:',sum(map(len,files.values())))
 print('All archived bytes verified; contribution checkout and index unchanged.')
