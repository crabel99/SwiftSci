from pathlib import Path
import hashlib,json,re,shutil,subprocess
r=Path(__file__).resolve().parent;n=Path('/private/tmp/swiftsci-mlprogram-20261026/notes');ref='refs/heads/codex/engineering-notes';remote='https://github.com/crabel99/SwiftSci.git';base='ba27ec19561cf02467547c87f9434a39d44f1f04'
assert (r/'publication-audit.md').is_file()
def run(*a):return subprocess.check_output(list(a),cwd=n,text=True,stderr=subprocess.STDOUT).strip()
assert run('git','status','--porcelain')=='' and run('git','rev-parse','HEAD')==base
before=run('git','ls-remote',remote,ref);assert before.split()[0]==base
subprocess.run(['python3',str(r/'records/verify-publication.py'),'--records',str(r/'records')],check=True)
root=n/'Documentation/EngineeringNotes';dest=root/'benchmarks/2026-10-27-numerical-workflow-upstream';assert not dest.exists()
shutil.copytree(r/'records',dest)
audit=root/'benchmarks/2026-10-27-numerical-workflow-publication-audit.md';shutil.copyfile(r/'publication-audit.md',audit)
index=root/'README.md';text=index.read_text();needle='## Start here\n';assert text.count(needle)==1
text=text.replace(needle,needle+'\n- [Complete numerical workflow example](benchmarks/2026-10-27-numerical-workflow-upstream/README.md) records the runnable CSV-to-classification example, independent numerical checks, leakage and malformed-input controls, full local qualification and unchanged scientific APIs. The [publication review](benchmarks/2026-10-27-numerical-workflow-publication-audit.md) verifies retained bytes and redactions.\n',1);index.write_text(text)
links=[]
for link in re.findall(r'\]\(([^)]+)\)',text):
 if re.match(r'[A-Za-z][A-Za-z0-9+.-]*:',link) or link.startswith('#'):continue
 path=(root/link.split('#')[0]);assert path.exists(),link;links.append(link)
subprocess.run(['python3',str(dest/'verify-publication.py'),'--records',str(dest)],check=True)
run('git','add',str(dest.relative_to(n)),str(audit.relative_to(n)),str(index.relative_to(n)))
names=run('git','diff','--cached','--name-only').splitlines();assert len(names)==len([p for p in (r/'records').rglob('*') if p.is_file()])+2 and all(x.startswith(str(dest.relative_to(n))+'/') or x in [str(audit.relative_to(n)),str(index.relative_to(n))] for x in names)
run('git','commit','-m','docs: record complete numerical workflow example');head=run('git','rev-parse','HEAD');assert run('git','status','--porcelain')==''
assert run('git','ls-remote',remote,ref).split()[0]==base
output=run('git','push',remote,'HEAD:'+ref);after=run('git','ls-remote',remote,ref);assert after.split()[0]==head
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=dict(status='published',source=(r/'source-head.txt').read_text().strip(),base=base,notes=head,ref=ref,remote=remote,before=before,after=after,output=output,files=len(names),index_relative_links=len(links),manifest_sha256=sha(dest/'FILES.sha256'),readme_sha256=sha(dest/'README.md'),controller_sha256=sha(Path(__file__)))
(r/'notes-publication.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
