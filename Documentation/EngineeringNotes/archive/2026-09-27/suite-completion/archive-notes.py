import gzip,hashlib,io,json,os,subprocess,tarfile,tempfile
from pathlib import Path
root=Path('/Users/LOCAL_USER/Documents/src/SwiftSci');work=Path('/private/tmp/swiftsci-suite-finish');prefix='Documentation/EngineeringNotes/archive/2026-09-27/suite-completion/'
def git(*args,**kw):return subprocess.check_output(['git','-C',str(root),*args],**kw).decode().strip()
base=git('rev-parse','codex/engineering-notes');assert base==git('rev-parse','origin/codex/engineering-notes')
head=git('rev-parse','HEAD');index_tree=git('write-tree')
files={'Documentation/EngineeringNotes/benchmarks/2026-09-27-suite-completion.md':(work/'report.md').read_bytes()}
for p in work.rglob('*'):
 if p.is_file() and not any(x in p.parts for x in ['__pycache__','module-cache']) and p.suffix in ('.py','.swift','.md','.json','.jsonl','.tsv','.log','.txt','.f64') and p.name not in ('notes-commit.txt',):
  files[prefix+str(p.relative_to(work))]=p.read_bytes()
run_names=['finish-vision-01','finish-boundary-01','finish-acceptance-01','finish-acceptance-02']
run_manifest={}
archive=work/'runs.tar.gz'
with archive.open('wb') as raw:
 with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as zipped:
  with tarfile.open(fileobj=zipped,mode='w|') as tar:
   for name in run_names:
    directory=root/'Benchmarks/Runs'/name
    for p in sorted(directory.rglob('*')):
     if p.is_file():
      data=p.read_bytes();relative=name+'/'+str(p.relative_to(directory))
      run_manifest[relative]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
      info=tarfile.TarInfo(relative);info.size=len(data);info.mode=0o644;info.mtime=0;tar.addfile(info,io.BytesIO(data))
with tarfile.open(archive,'r:gz') as tar:
 observed={}
 for info in tar:
  data=tar.extractfile(info).read();observed[info.name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
assert observed==run_manifest
blob=archive.read_bytes()
if len(blob)<48*1024*1024:
 files[prefix+'runs.tar.gz']=blob
else:
 for i,start in enumerate(range(0,len(blob),48*1024*1024)):
  files[prefix+f'runs.tar.gz.part{i:03d}']=blob[start:start+48*1024*1024]
files[prefix+'runs-manifest.json']=(json.dumps(dict(archive_sha256=hashlib.sha256(blob).hexdigest(),archive_bytes=len(blob),members=run_manifest),indent=2)+'\n').encode()
path='Documentation/EngineeringNotes/benchmarks/2026-09-27-dataset-strategy.md'
s=git('show',base+':'+path)
s+='\n\n## Suite completion checkpoint\n\nThe four agreed remaining items now have implemented contracts and recorded outcomes: analytic vision preprocessing, dataframe-to-tensor integration, bounded stage/size sweeps and complete profile acceptance. See [the completion report](2026-09-27-suite-completion.md) for the exact revision, complete outcomes and remaining production failures. The contribution branch stays local. Proceed next to the separate repair branch, one commit per diagnosed error, then establish the formal performance baseline after the relevant suite passes. Trained checkpoint quality, unmatched algorithms and physical zero-copy claims remain outside this completed scope.\n'
files[path]=s.encode()
files[prefix+'manifest.json']=(json.dumps({k:dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for k,v in sorted(files.items())},indent=2)+'\n').encode()
with tempfile.TemporaryDirectory(prefix='swiftsci-notes-index-') as directory:
 env=dict(os.environ,GIT_INDEX_FILE=str(Path(directory)/'index'));git('read-tree',base,env=env)
 for name,data in files.items():
  oid=git('hash-object','-w','--stdin',input=data);git('update-index','--add','--cacheinfo','100644,'+oid+','+name,env=env)
 tree=git('write-tree',env=env);commit=git('commit-tree',tree,'-p',base,input=b'docs(engineering): record complete suite acceptance and remaining defects\n');git('update-ref','refs/heads/codex/engineering-notes',commit,base)
 for name,data in files.items():assert subprocess.check_output(['git','-C',str(root),'show',commit+':'+name])==data
 assert head==git('rev-parse','HEAD') and index_tree==git('write-tree')
 assert all(n.startswith('Documentation/EngineeringNotes/') for n in git('diff-tree','--no-commit-id','--name-only','-r',commit).splitlines())
 (work/'notes-commit.txt').write_text(commit+'\n')
 print('Notes commit',commit,'files',len(files),'archive members',len(run_manifest),'archive bytes',len(blob))
 print('All archive member bytes and Git blobs verified; contribution checkout/index unchanged.')
