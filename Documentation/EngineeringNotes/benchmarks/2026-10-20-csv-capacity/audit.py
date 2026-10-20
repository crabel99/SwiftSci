from pathlib import Path
import hashlib,json,subprocess,re,difflib,statistics
R=Path(__file__).resolve().parent;repo='/private/tmp/swiftsci-scalar-resource-20261019'
base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip();expected='546510bb7d';assert base.startswith(expected)
changed={};builds={}
for v in ['baseline','presized','instrumented']:
 b=json.loads((R/'build'/v/'build.json').read_text());builds[v]=b
 changes=[];patch=[]
 for name,digest in b['sources'].items():
  p=Path(b['variant']['path'])/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==digest
  original=subprocess.check_output(['git','show',base+':'+name],cwd=repo)
  if original!=p.read_bytes():
   changes.append(name);patch.extend(difflib.unified_diff(original.decode().splitlines(True),p.read_text().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
 assert hashlib.sha256((R/'build'/v/'ResourceProbe').read_bytes()).hexdigest()==b['binary_sha256']
 assert b['harness_sha256']==hashlib.sha256((R/('Inspect.swift' if v=='instrumented' else 'ResourceProbe.swift')).read_bytes()).hexdigest()
 changed[v]=changes
 if patch:(R/(v+'.patch')).write_text(''.join(patch))
assert changed['baseline']==[]
assert changed['presized']==['Sources/SwiftDataFrame/IO/SystemsCSVParser.swift']
assert set(changed['instrumented'])=={'Sources/SwiftDataFrame/IO/SystemsCSVParser.swift','Sources/SwiftDataFrame/IO/CSVColumnBuilder.swift'}
assert builds['baseline']['dependency_objects']==builds['presized']['dependency_objects']
for v in ['baseline','presized']:
 assert all('[DEBUG-csvcap]' not in p.read_text() for p in (R/v/'Sources').rglob('*.swift'))
lines=(R/'trace.log').read_text().splitlines()
grow={re.search(r'pointer=Optional\(([^)]+)\)',l)[1]:int(re.search(r'capacity=(\d+)',l)[1]) for l in lines if 'fields-grow' in l}
reuse=[]
for l in lines:
 if 'builder requested' in l:
  m=re.search(r'requested=(\d+) capacity=(\d+) pointer=Optional\(([^)]+)\)',l)
  if int(m[2])>int(m[1])*1.1:
   assert grow[m[3]]==int(m[2]);reuse.append({'requested':int(m[1]),'capacity':int(m[2]),'pointer':m[3]})
assert reuse
es=[json.loads(l) for l in (R/'workers.jsonl').read_text().splitlines()];assert len(es)==80
assert len({(tuple(e['case']),e['phase'],e['pair'],e['variant']) for e in es})==80
for e in es:assert e['validated'] and len(e['samples'])==(5 if e['phase']=='timing' else 1)
summary=json.loads((R/'summary.json').read_text())
for row in summary['rows']:
 for v in ['baseline','presized']:
  group=[e for e in es if e['case']==row['case'] and e['variant']==v and e['phase']=='timing']
  assert len(group)==5
  for metric in ['total_ns','total_cpu_ns']:
   assert statistics.median(statistics.median(s[metric] for s in e['samples']) for e in group)==row['statistics'][v][metric]
checks=json.loads((R/'checks.json').read_text())
assert len(checks)==4 and all('PASS: 7' in c['stdout'] for c in checks if c['probe']=='Semantics')
record={'status':'passed','baseline_sha':base,'changes':changed,'reused_parser_blocks':reuse,'workers':80,'timing_samples':250,'memory_samples':30,'semantic_fixtures_per_variant':7}
(R/'audit.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
