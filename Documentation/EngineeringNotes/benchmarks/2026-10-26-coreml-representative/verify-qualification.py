from pathlib import Path
import hashlib,json,subprocess,sys
r=Path(__file__).resolve().parent;s=r/'source'
read=lambda path:json.loads((r/path).read_text())
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=s,text=True).strip()
assert head=='a1e234d25677d91ce5914062603c41233fe13c09'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=s,text=True).strip()
fingerprints={str(p.relative_to(s)):hashlib.sha256(p.read_bytes()).hexdigest() for b in ['Sources','Tests'] for p in (s/b).rglob('*.swift')}
native={}
for tag in ['full-debug','full-release']:
 build=read(f'native-{tag}/build.json');result=read(f'native-{tag}/tests.json')
 assert build['exit_code']==0 and build['sources']==fingerprints
 assert result['exit_code']==0
 counts={k:result['summary'][k] for k in ['totalTestCount','passedTests','failedTests','skippedTests']}
 assert counts==dict(totalTestCount=1685,passedTests=1685,failedTests=0,skippedTests=0)
 native[tag]=counts
assert read('native-export-red/tests.json')['summary']['failedTests']==2
assert read('native-export-green-native/tests.json')['summary']['passedTests']==2
compatibility=read('compatibility/result.json')
assert compatibility['status']=='passed' and compatibility['sources']==fingerprints
assert read('compatibility/multiclass-tests.json')['exit_code']==0
ci={}
for scope,folder in [('main','ci-main'),('benchmarks','ci-bench'),('security-python','ci-security-python')]:
 data=read(f'{folder}/{scope}-result.json');assert data['status']=='passed' and data['commit']==head
 assert all(x['exit_code']==0 for x in data['steps']);ci[scope]=len(data['steps'])
sys.path.insert(0,str(s/'Benchmarks/CoreMLInference'))
from run import reference_accuracy_met
records=read('trained-results/results.json');assert len(records)==66 and all(reference_accuracy_met(x) for x in records)
assert all(x['reservedBytesAfterPrediction']==0 for x in records)
fromrunner=read('trained-results/provenance.json');assert fromrunner['source']['commit']==head
workflows={}
for kind in ['wdbc','wine']:
 data=read(f'workflow-probe/{kind}.json');assert len(data['samples'])==32 and data['referenceExceedances']==0 and data['reservedBytesAfterPrediction']==0
 assert data['maximumScalingDifference']<1e-10
 workflows[kind]=dict(rows=data['rows'],maximumScalingDifference=data['maximumScalingDifference'],referenceExceedances=0)
coverage=read('compatibility/multiclass-coverage.json');assert coverage['line_counts']['696']>0 and coverage['line_counts']['698']>0
traces=read('traces/inspected-events.json');assert len(traces)==4
for t in traces:assert t['dispatch_counts']=={'CPU':t['completed_requests']}
report=dict(source_commit=head,base_commit='53063789b1893b28250ea239d5fdca4fed84c4c9',native=native,local_ci_steps=ci,
 swift633='Debug build, all test targets compiled, safe suite, Release build, both new runtime regressions passed',
 representative_cases=66,strict_reference_passes=66,raw_workflows=workflows,corrected_softmax_coverage=coverage['line_counts'],
 actual_dispatches={t['name']:t['dispatch_counts'] for t in traces},
 limitations=['Swift CodeQL unavailable with retained Xcode 27 / Swift 6.4.',
 'Known four Python Wampler conformance failures remain under the unchanged accepted regression policy.',
 'Native xccov lists library targets without source coverage. Its aggregate covers test sources and is not a library coverage percentage. The main CI export check passed as written.',
 'Only the legacy Float32-weight Core ML artifacts were qualified here. ML Program / Float16 / Neural Engine application qualification remains separate.',
 'Wine frozen reference model reached its optimizer iteration limit and performed worse than the constant test baseline. No application-quality threshold was established.',
 'Single fresh process per comparison cell with repeated warm samples; local development evidence, not a production performance baseline.'])
(r/'qualification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status='passed',commit=head,native_tests=1685,configurations=2,representative_cases=66,inspected_traces=4)))
