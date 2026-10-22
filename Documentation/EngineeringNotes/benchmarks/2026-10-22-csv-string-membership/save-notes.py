from pathlib import Path
import difflib,gzip,hashlib,json,re,shutil,subprocess,tarfile
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');N=Path('/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018');P=Path('/private/tmp/swiftsci-csv-local-builder-20261022')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source=json.loads((R/'source-state.json').read_text())
assert source['head']=='c906c3fbbb0baf1357438a7079921a6448e0c9e5'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()==source['head']
assert all(h(S/p)==sha for p,sha in source['sources'].items())
assert not subprocess.check_output(['git','status','--porcelain'],cwd=N)
assert subprocess.check_output(['git','branch','--show-current'],cwd=N,text=True).strip()=='codex/engineering-notes'
expected={'screening':648,'followup':448,'edge-controls':512,'setup-controls':256,'refined-screen':648,'refined-setup':576}
for group,count in expected.items():
 rows=[json.loads(line) for line in (R/group/'workers.jsonl').read_text().splitlines()]
 assert len(rows)==count and all(r['validated'] for r in rows)
phases=list((R/'phases').glob('*.json'));workers=[json.loads(p.read_text()) for p in phases if p.name not in ['plan.json','summary.json','full-read-summary.json']]
assert len(workers)==18 and sum(len(d['phases']) for d in workers)==1152 and all(d['validated'] and all(x['validated'] for x in d['phases']) for d in workers)
for group in ['semantics','refined-semantics']:
 results=json.loads((R/group/'summary.json').read_text());assert len(results)==4 and all(r['validated'] and r['cells']==3336243 for r in results)
for label,v in json.loads((R/'variants.json').read_text()).items():
 receipt=json.loads((R/'build'/label/'build.json').read_text());assert all(h(Path(v['path'])/p)==sha for p,sha in receipt['sources'].items());assert h(R/'build'/label/'ResourceProbe')==receipt['binary_sha256']
status=json.loads((R/'refinement-status.json').read_text());assert len(status)==2 and all(r['exit_code']==0 for r in status)
D=N/'Documentation/EngineeringNotes/benchmarks/2026-10-22-csv-string-membership';D.mkdir(exist_ok=False)
for p in [*R.glob('*.py'),*R.glob('*.swift'),*R.glob('*.json')]:shutil.copy2(p,D/p.name)
def compress(p,out):
 out.parent.mkdir(parents=True,exist_ok=True)
 with gzip.open(out,'wb') as f:f.write(p.read_bytes())
 assert gzip.decompress(out.read_bytes())==p.read_bytes()
for p in [*R.glob('*.log'),*R.glob('*.stderr')]:compress(p,D/(p.name+'.gz'))
for group in [*expected,'phases','profiles','semantics','refined-semantics']:
 out=D/group;out.mkdir()
 for p in (R/group).iterdir():
  if not p.is_file():continue
  if p.suffix in ['.jsonl','.txt','.stderr'] or (group=='phases' and p.name not in ['summary.json','full-read-summary.json','plan.json']):compress(p,out/(p.name+'.gz'))
  else:shutil.copy2(p,out/p.name)
roots={label:R/'build'/label for label in json.loads((R/'variants.json').read_text())};roots['production']=P/'build/production'
for label,root in roots.items():
 out=D/'build-receipts'/label;out.mkdir(parents=True)
 for name in ['build.json','module-signature.json','StreamProbe.build.json']:
  if (root/name).is_file():shutil.copy2(root/name,out/name)
 for p in root.glob('*.log'):compress(p,out/(p.name+'.gz'))
patches=R/'trial-patches';patches.mkdir(exist_ok=True);base=R/'variants/control'
for label,v in json.loads((R/'variants.json').read_text()).items():
 diff=[]
 for p in sorted((Path(v['path'])/'Sources/SwiftDataFrame').rglob('*.swift')):
  rel=p.relative_to(v['path']);old=base/rel
  if p.read_bytes()!=old.read_bytes():diff.extend(difflib.unified_diff(old.read_text().splitlines(keepends=True),p.read_text().splitlines(keepends=True),fromfile='a/'+str(rel),tofile='b/'+str(rel)))
 (patches/(label+'.patch')).write_text(''.join(diff))
contracts={}
for p in [*(R/'inputs').glob('*.json'),*(R/'setup-inputs').glob('*.json'),R/'unicode/all-scalars.json']:
 contracts[str(p)]=p
for group in expected:
 plan=json.loads((R/group/'plan.json').read_text())
 for case in plan['cases']:
  p=Path(case if isinstance(case,str) else case[2]);contracts[str(p)]=p
with tarfile.open(D/'experiments.tar.gz','w:gz') as t:
 t.add(R/'variants',arcname='variants');t.add(patches,arcname='trial-patches');seen=set()
 for key,p in sorted(contracts.items()):
  t.add(p,arcname='input-contracts/'+p.parent.name+'/'+p.name);inp=json.loads(p.read_text());data=Path(inp['path']);assert h(data)==inp.get('source_sha256',inp.get('sha256'))
  if data in seen:continue
  seen.add(data)
  if any(part in str(data) for part in ['/text-inputs/','/long-key-inputs/','/setup-inputs/','/unicode/']):t.add(data,arcname='generated-inputs/'+data.parent.name+'/'+data.name)
headers=['| Scope | Input | Policy | Implementation | CPU ms | Elapsed ms | Peak RSS MiB |','|---|---|---|---|---:|---:|---:|']
for group in ['screening','followup','setup-controls','refined-screen','refined-setup']:
 lines=['# '+group.replace('-',' ').capitalize(),'','CPU is process user-plus-system time. Every worker validates native output. See [the study record](README.md).','',*headers]
 for a in json.loads((R/group/'summary.json').read_text()):
  x=a['medians'];m='peak_after_bytes' if a['scope']=='stream' else 'process_peak_held_bytes';lines.append(f"| {a['scope']} | {a['case']} | {a['policy']} | {a['engine']} | {x['total_cpu_ns']/1e6:.3f} | {x['total_ns']/1e6:.3f} | {x[m]/2**20:.2f} |")
 (D/(group+'.md')).write_text('\n'.join(lines)+'\n')
edge=['# Fresh and steady edge controls','','Steady workers run two warmups and five recorded complete reads. Worker medians are combined only within the same mode and conversion policy. [Study record](README.md).','','| Input | Policy | Mode | Implementation | Workers | Recorded reads | CPU ms | Elapsed ms | Peak RSS MiB |','|---|---|---|---|---:|---:|---:|---:|---:|']
for a in json.loads((R/'edge-controls/summary.json').read_text()):
 x=a['medians'];edge.append(f"| {a['case']} | {a['policy']} | {a['phase']} | {a['engine']} | {a['workers']} | {a['recorded_reads']} | {x['total_cpu_ns']/1e6:.3f} | {x['total_ns']/1e6:.3f} | {x['process_peak_held_bytes']/2**20:.2f} |")
(D/'edges.md').write_text('\n'.join(edge)+'\n')
phase=['# String-field replay costs','','Each worker runs each phase eight times per String column. The table gives the median of each worker median, across six workers. Replay preparation is untimed. These costs are not additive fractions of complete-read time. [Study record](README.md).','','| Input | Column | Phase | CPU ms | Elapsed ms | Held heap delta MiB | Held RSS delta MiB |','|---|---|---|---:|---:|---:|---:|']
for a in json.loads((R/'phases/summary.json').read_text()):
 x=a['medians'];phase.append(f"| {a['case']} | {a['column']} | {a['mode']} | {x['total_cpu_ns']/1e6:.3f} | {x['total_ns']/1e6:.3f} | {x['held_heap_delta_bytes']/2**20:.3f} | {x['held_rss_delta_bytes']/2**20:.3f} |")
(D/'phases.md').write_text('\n'.join(phase)+'\n')
body=(R/'report-body.md').read_text();(D/'README.md').write_text(body);shutil.copy2(R/'report-body.md',D/'report-body.md.in')
files={str(p.relative_to(D)):h(p) for p in D.rglob('*') if p.is_file() and p.name!='artifact-sha256.json'};(D/'artifact-sha256.json').write_text(json.dumps(files,indent=2)+'\n')
for p in D.rglob('*.md'):
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if target.startswith('https://'):continue
  assert (p.parent/target).exists(),(p,target)
assert all(h(D/p)==sha for p,sha in files.items())
index=N/'Documentation/EngineeringNotes/README.md';s=index.read_text();needle='## Start here\n\n';assert s.count(needle)==1
s=s.replace(needle,needle+'- [CSV String lookup cost and prefix trials](benchmarks/2026-10-22-csv-string-membership/README.md) separates parsing from matching, records default-token CPU gains and exhaustive Unicode-scalar coverage, and identifies setup amortization before production qualification.\n\n');index.write_text(s)
print(D,len(files),'verified artifacts')
