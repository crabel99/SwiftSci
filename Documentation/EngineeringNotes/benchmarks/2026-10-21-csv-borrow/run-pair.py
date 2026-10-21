"""One fresh output directory per comparison; fixture paths never depend on result labels."""
from pathlib import Path
import argparse,json,hashlib,subprocess,sys
R=Path(__file__).resolve().parent
sys.path.insert(0,'/private/tmp/swiftsci-csv-sort-20261017/Benchmarks/Tools')
from runner import power_state,verify_uninstrumented,environment
from execution_policy import worker_environment,PRODUCTION_MODE
parser=argparse.ArgumentParser()
parser.add_argument('reference',choices=list(json.loads((R/'variants.json').read_text())))
parser.add_argument('candidate',choices=list(json.loads((R/'variants.json').read_text())))
parser.add_argument('suite',choices=['primary','heldout','diverse','flat'])
parser.add_argument('output',type=Path)
a=parser.parse_args();assert a.reference!=a.candidate
primary=[('csv-quoted',100000,4,R/'fixtures/100000-4-True.csv'),('csv-quoted',250000,4,R/'fixtures/250000-4-True.csv'),('csv-quoted',1000000,4,Path('/Users/crabel/local-ai/spl/swiftsci/pr-resource-metrics-20261018/fixtures/02-pr39-csv-quoted-1000000-4.csv')),('csv-quoted',1000000,2,R/'fixtures/1000000-2-True.csv'),('csv',1000000,4,R/'fixtures/1000000-4-False.csv')]
heldout=[('csv',1000,4,R/'heldout-fixtures/1000-4-False.csv'),('csv-quoted',1000,4,R/'heldout-fixtures/1000-4-True.csv'),('csv-quoted',10000,4,R/'heldout-fixtures/10000-4-True.csv'),('csv-quoted',131071,7,R/'heldout-fixtures/131071-7-True.csv'),('csv-quoted',75001,13,R/'heldout-fixtures/75001-13-True.csv')]
if a.suite in ['primary','heldout']:
 cases=primary if a.suite=='primary' else heldout
else:
 cases=[(*c[:3],Path(c[3])) for c in json.loads((R/(a.suite+'-cases.json')).read_text())]

fixtures={str(c[3]):hashlib.sha256(c[3].read_bytes()).hexdigest() for c in cases}
builds={v:json.loads((R/'build'/v/'build.json').read_text()) for v in [a.reference,a.candidate]}
assert builds[a.reference]['dependency_objects']==builds[a.candidate]['dependency_objects']
assert builds[a.reference]['harness_sha256']==builds[a.candidate]['harness_sha256']
for v in builds:verify_uninstrumented(R/'build'/v/'ResourceProbe')
power=power_state();assert power['source']=='AC'
# Exclusive directory creation is the mutation boundary. Existing results are immutable.
a.output.mkdir(parents=True,exist_ok=False)
plan=dict(reference=a.reference,candidate=a.candidate,suite=a.suite,cases=[[*c[:3],str(c[3])] for c in cases],builds=builds,fixtures=fixtures,power=power,environment=environment())
(a.output/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
with (a.output/'workers.jsonl').open('x') as f:
 for ci,c in enumerate(cases):
  for phase,count in [('timing',5),('memory',3)]:
   for pair in range(count):
    variants=[a.reference,a.candidate]
    if (ci+pair)%2:variants.reverse()
    for v in variants:
     args=[c[0],str(c[1]),str(c[2]),'5',phase,str(c[3])]
     p=subprocess.run([str(R/'build'/v/'ResourceProbe'),*args],env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=120)
     assert p.returncode==0,p.stderr
     result=json.loads(p.stdout);assert result['validated'] and len(result['samples'])==(5 if phase=='timing' else 1)
     f.write(json.dumps(dict(case=c[:3],phase=phase,pair=pair,variant=v,**result))+'\n');f.flush()
  print(ci+1,len(cases),c[:3],flush=True)
end=power_state();assert end['source']=='AC';(a.output/'power-end.json').write_text(json.dumps(end,indent=2)+'\n')
