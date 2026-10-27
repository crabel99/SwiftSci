from pathlib import Path
import hashlib,json,subprocess
r=Path(__file__).resolve().parent;s=r/'source';head='08486058190836df0a3b1916aa2cb633450a35fc';ref='refs/heads/codex/fix-multi-binary-coverage';remote='https://github.com/crabel99/SwiftSci.git'
qualification=json.loads((r/'qualification.json').read_text());assert qualification['source']==head and qualification['status']=='passed'
assert (r/'audit.md').is_file()
def run(*a):return subprocess.check_output(list(a),cwd=s,text=True,stderr=subprocess.STDOUT).strip()
assert run('git','rev-parse','HEAD')==head and run('git','status','--porcelain')==''
before=run('git','ls-remote',remote,ref);assert not before or before.split()[0]==head
output=run('git','push',remote,'HEAD:'+ref)
after=run('git','ls-remote',remote,ref);assert after.split()[0]==head
receipt=dict(status='published',transport='normal Git; non-force branch update',source=head,base=run('git','rev-parse','HEAD^'),ref=ref,remote=remote,before=before,after=after,output=output,qualification_sha256=hashlib.sha256((r/'qualification.json').read_bytes()).hexdigest(),controller_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(r/'source-publication.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
