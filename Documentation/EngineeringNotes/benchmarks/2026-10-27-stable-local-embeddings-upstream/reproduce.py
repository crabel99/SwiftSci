from pathlib import Path
import argparse,hashlib,json,os,subprocess
p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--runs',type=int,default=40);a=p.parse_args()
r=Path(__file__).resolve().parent;s=r/'source';out=r/a.tag;out.mkdir(exist_ok=False)
paths=['Core/LocalEmbeddingEngine.swift','Core/SentenceEmbedding.swift','Core/AppleSentenceEmbeddingEngine.swift','Core/AppleNLEmbedding.swift','Classification/ZeroShotTextClassifier.swift','Errors/NLPError.swift']
inputs=[s/'Sources/SwiftNLP'/name for name in paths]
# Compile the existing shared hash function verbatim without its unrelated tokenizer types/imports.
tokenizer=s/'Sources/SwiftNLP/Core/Tokenizer.swift';body=tokenizer.read_text().split('@inlinable\npublic func fnv1aTokenHash',1)[1];helper='@inlinable\npublic func fnv1aTokenHash'+body
(out/'existing-hash.swift').write_text(helper)
command=['xcrun','swiftc','-parse-as-library','-module-cache-path',str(r/'probe-module-cache'),*map(str,inputs),str(out/'existing-hash.swift'),str(r/'probe.swift'),'-o',str(out/'probe')]
with (out/'build.log').open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
env={k:v for k,v in os.environ.items() if k not in ['SWIFT_DETERMINISTIC_HASHING','SWIFT_HASH_SEED']}
outputs=[json.loads(subprocess.check_output([str(out/'probe')],env=env,text=True)) for _ in range(a.runs)]
(out/'outputs.json').write_text(json.dumps(outputs,indent=2)+'\n')
unique=len({json.dumps(d['vector']) for d in outputs});predictions={value:sum(d['prediction']==value for d in outputs) for value in ['technology','food']}
expected=[0.0]*16;expected[5]=-1.0
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
report=dict(tag=a.tag,source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=s,text=True).strip(),runs=a.runs,unique_vectors=unique,predictions=predictions,golden_passes=sum(d['golden']==expected for d in outputs),source_sha256={str(f.relative_to(s)):sha(f) for f in inputs+[tokenizer]},controller_sha256=sha(Path(__file__)),probe_sha256=sha(r/'probe.swift'),binary_sha256=sha(out/'probe'),command=command,scope='Fresh processes execute actual production embedding/classifier/provider source. Shared hash helper is extracted verbatim from Tokenizer.swift to avoid unrelated tokenizer dependencies. No deterministic-hashing environment override.')
(out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
