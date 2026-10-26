from pathlib import Path
import argparse, hashlib, json, subprocess, time
p=argparse.ArgumentParser();p.add_argument('--library-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--prepared-probe',type=Path,required=True);p.add_argument('--legacy-probe',type=Path,required=True);a=p.parse_args()
r=Path(__file__).resolve().parent;source=a.library_root/'source';out=a.output;out.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build_path=Path(str(a.library_root/'ci-bench-cache/standardized/derived/Build/Products/Release/SwiftSciBenchmarkWorker')+'.build.json')
build=json.loads(build_path.read_text());head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
build_log=Path(build['log']).resolve();build_log_sha256=sha(build_log)
assert build['source']['commit']==head and subprocess.check_output(['git','status','--porcelain'],cwd=source,text=True)==''
assert all(sha(source/name)==digest for name,digest in build['source']['files'].items())
proofs={}
for name,folder in [('prepared',a.prepared_probe),('legacy',a.legacy_probe)]:
 proof=json.loads((folder/'proof.json').read_text());assert sha(folder/'probe')==proof['binary_sha256']
 assert Path(proof['input_build_log']).resolve()==build_log, 'Probe belongs to a different library build'
 assert proof['input_build_log_sha256']==build_log_sha256, 'Probe build log has changed'
 assert all(Path(path).resolve().is_relative_to(build_path.parent.resolve()) for path in proof['objects']), 'Probe objects belong to a different build'
 assert all(sha(Path(path))==digest for path,digest in proof['objects'].items())
 assert '-package-name' not in proof['compile'] and '-enable-testing' not in proof['compile']
 expected=r/('ScientificWorkflow.swift' if name=='prepared' else 'LegacyWorkflowProbe.swift')
 assert sha(expected)==proof['probe_source_sha256'];proofs[name]=proof
command=[str(a.prepared_probe/'probe')]
attempts=[]
with (out/'prepared.json').open('w') as stdout,(out/'prepared.log').open('w') as stderr:
 start=time.time();result=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=60)
attempts.append(dict(command=command,exit_code=result.returncode,seconds=time.time()-start))
(out/'attempts.json').write_text(json.dumps(attempts,indent=2)+'\n')
assert result.returncode==0
prepared=json.loads((out/'prepared.json').read_text())
command=[str(a.legacy_probe/'probe'),str((out/'prepared.json').resolve())]
with (out/'legacy.json').open('w') as stdout,(out/'legacy.log').open('w') as stderr:
 start=time.time();result=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=60)
attempts.append(dict(command=command,exit_code=result.returncode,seconds=time.time()-start))
(out/'attempts.json').write_text(json.dumps(attempts,indent=2)+'\n')
assert result.returncode==0
json.loads((out/'legacy.json').read_text())
receipt=dict(source=head,worker_build_sha256=sha(build_path),build=build,proofs=proofs,
    input_build_log_sha256=build_log_sha256,
    prepared_result_sha256=sha(out/'prepared.json'),legacy_result_sha256=sha(out/'legacy.json'),
    scope='Public imports, no package/test access. CPU full SVD and CPU logistic. No speed, memory or statistical-quality claim.',
    runner_sha256=sha(Path(__file__)))
(out/'provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(source=head,training_rows=len(prepared['trainingSourceRows']),query_rows=prepared['querySourceRows'],predictions=prepared['predictions'])))
