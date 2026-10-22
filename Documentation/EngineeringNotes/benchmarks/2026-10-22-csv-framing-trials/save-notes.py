from pathlib import Path
import hashlib,json,subprocess,shutil,gzip,difflib,tarfile,re,statistics as st
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');N=Path('/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018');P=Path('/private/tmp/swiftsci-csv-wide-profile-20261022')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()=='9c067c6c5116d78c0849073acea7fb150404efab'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
assert subprocess.check_output(['git','branch','--show-current'],cwd=N,text=True).strip()=='codex/engineering-notes'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=N)
for f in ['pilot.json','derived-pilot.json']:
 assert all(d['result']['validated'] for d in json.loads((R/f).read_text())['records'])
assert sum(x['samples'] for x in json.loads((R/'public-read-summary.json').read_text()))==1344
scan=json.loads((R/'scan-matched.json').read_text());assert len(scan)==128
for case in set(d['case'] for d in scan):
 ds=[d['result'] for d in scan if d['case']==case];assert len({(d['rows'],d['fields'],d['batches'],d['sha256']) for d in ds})==1
production=json.loads((P/'build/production/build.json').read_text())['commands'][0];common=production[2:production.index('-parse-as-library')]
for e in ['parent','consume','header','derived-count']:
 rec=json.loads((R/('scan-wmo-'+e+'-build.json')).read_text());assert rec['production_compiler_options']==common and h(R/('ScanProbe-wmo-'+e))==rec['binary_sha256']
for e,variant in json.loads((R/'variants.json').read_text()).items():
 rec=json.loads((R/'build'/e/'build.json').read_text());assert h(R/'build'/e/'ResourceProbe')==rec['binary_sha256']
 assert all(h(Path(variant['path'])/rel)==sha for rel,sha in rec['sources'].items())
D=N/'Documentation/EngineeringNotes/benchmarks/2026-10-22-csv-framing-trials';D.mkdir(parents=True,exist_ok=False)
for p in [*R.glob('*.py'),*R.glob('*.swift'),*R.glob('*.json')]:shutil.copy2(p,D/p.name)
for p in [*R.glob('*.txt'),*R.glob('*.log'),*R.glob('*.stderr'),*R.glob('*.stdout')]:
 if p.is_file():
  with gzip.open(D/(p.name+'.gz'),'wb') as f:f.write(p.read_bytes())
for label in ['consume','header','derived-count']:
 out=D/'build-receipts'/label;out.mkdir(parents=True)
 for name in ['build.json','module-signature.json']:shutil.copy2(R/'build'/label/name,out/name)
out=D/'build-receipts/parent';out.mkdir(parents=True)
for name in ['build.json','module-signature.json']:shutil.copy2(P/'build/production'/name,out/name)
patches=R/'trial-patches';patches.mkdir(exist_ok=False)
for label in ['consume','header','derived-count']:
 changes=[]
 for p in sorted((R/(label+'-trial')/'Sources/SwiftDataFrame').rglob('*.swift')):
  rel=p.relative_to(R/(label+'-trial'));base=S/rel
  if h(p)!=h(base):changes+=difflib.unified_diff(base.read_text().splitlines(keepends=True),p.read_text().splitlines(keepends=True),fromfile='a/'+str(rel),tofile='b/'+str(rel))
 (patches/(label+'.patch')).write_text(''.join(changes))
with tarfile.open(D/'experiments.tar.gz','w:gz') as archive:
 archive.add(patches,arcname='trial-patches')
 for file in ['SystemsCSVParser.swift','CSVRecordIndex.swift']:
  archive.add(S/'Sources/SwiftDataFrame/IO'/file,arcname='parent-sources/'+file)
  for label in ['consume','header','derived-count']:archive.add(R/(label+'-trial')/'Sources/SwiftDataFrame/IO'/file,arcname='trial-sources/'+label+'/'+file)
 for file in ['energy-prefix.txt','energy-prefix.json']:archive.add(R/file,arcname='input/'+file)
rows=json.loads((R/'public-read-summary.json').read_text());table=['| Input, schema, scheduling | Parent A CPU ms | Consume CPU ms | Header CPU ms | Parent B CPU ms | Derived count CPU ms |','|---|---:|---:|---:|---:|---:|']
for case,mode in [('bike-day','known'),('bike-hour','known'),('Aotizhongxin','known'),('Wanliu','known'),('energy','known'),('energy','infer'),('energy-date-full','known'),('late-bool','infer'),('late-text','infer')]:
 for policy in ['parallel','serial']:
  first={d['engine']:d for d in rows if d['run']=='pilot.json' and (d['case'],d['mode'],d['policy'])==(case,mode,policy)}
  second={d['engine']:d for d in rows if d['run']=='derived-pilot.json' and (d['case'],d['mode'],d['policy'])==(case,mode,policy)}
  if not first:continue
  # The two trials have distinct contemporaneous parent measurements.
  table.append(f"| {case}, {mode}, {policy} | {first['parent']['medians']['total_cpu_ns']/1e6:.3f} | {first['consume']['medians']['total_cpu_ns']/1e6:.3f} | {first['header']['medians']['total_cpu_ns']/1e6:.3f} | {second['parent']['medians']['total_cpu_ns']/1e6:.3f} | {second['derived-count']['medians']['total_cpu_ns']/1e6:.3f} |")
table.append('\nParent A is measured alongside the consume and header trials. Parent B is measured alongside the derived-count trial. Compare each trial with its contemporaneous parent. Full per-case elapsed and memory results remain in the machine-readable summary.')
framing=[]
for case in dict.fromkeys(d['case'] for d in scan):
 vals={e:st.median(d['result']['cpu_ns'] for d in scan if d['case']==case and d['engine']==e)/1e6 for e in ['parent','consume','header','derived-count']}
 framing.append('| '+case+' | '+' | '.join(f'{vals[e]:.3f}' for e in ['parent','consume','header','derived-count'])+' |')
body=(R/'report-body.md').read_text().replace('PUBLIC_TABLE','\n'.join(table)).replace('FRAMING_TABLE','\n'.join(framing));(D/'README.md').write_text(body)
for p in D.glob('*.json'):
 if p.stat().st_size>256*1024:
  data=p.read_bytes()
  with gzip.open(str(p)+'.gz','wb') as f:f.write(data)
  assert gzip.decompress(Path(str(p)+'.gz').read_bytes())==data;p.unlink()
manifest={str(p.relative_to(D)):h(p) for p in D.rglob('*') if p.is_file() and p.name!='artifact-sha256.json'}
(D/'artifact-sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
for target in re.findall(r'\]\(([^)]+)\)',body):assert (D/target).exists(),target
assert all(h(D/p)==sha for p,sha in manifest.items())
print(D,len(manifest),'verified artifacts')
