import json, pathlib, urllib.request, hashlib, datetime
root=pathlib.Path('/Users/LOCAL_USER/Documents/src/SwiftSci')
out=pathlib.Path('/Users/LOCAL_USER/local-ai/spl/swiftsci/data-architecture-research/local-ai')
files=['Sources/SwiftLLM/Core/KVCache.swift','Sources/SwiftLLM/Core/PagedKVCache.swift']
blocks=[]; hashes={}
for name in files:
 text=(root/name).read_text(); hashes[name]=hashlib.sha256(text.encode()).hexdigest()
 blocks.append(name+'\n'+'\n'.join(f'{i}: {line}' for i,line in enumerate(text.splitlines(),1)))
prompt='''Review only the supplied Swift code. We are researching data structures for SwiftSci on Apple Silicon. Identify concrete allocations/concatenations, copy or materialization risks, mutation/lifetime constraints, and how a compact column buffer should or should not interface with these language-model caches. Cite exact supplied file and line numbers. Separate observed source behavior from hypotheses requiring profiling. Do not claim that MLX concatenation necessarily copies immediately; distinguish a lazy operation from materialization. Do not claim that unified memory makes arbitrary Swift arrays zero-copy Metal buffers. Give up to six findings and three engineering requirements. Do not write code or invent other source files.\n\n'''+ '\n\n'.join(blocks)
(out/'prompt.txt').write_text(prompt)
body={'model':'qwen3-coder-next','messages':[{'role':'system','content':'You are a careful code reviewer. Base findings only on the provided source. State uncertainty.'},{'role':'user','content':prompt}],'temperature':0,'max_tokens':2200,'stream':False}
req=urllib.request.Request('http://127.0.0.1:1234/v1/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req,timeout=240) as response: result=json.load(response)
(out/'response.json').write_text(json.dumps(result,indent=2))
(out/'review.md').write_text(result['choices'][0]['message']['content'])
(out/'metadata.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'endpoint':'127.0.0.1:1234','requested_model':body['model'],'source_commit':'4c5bb95354','source_sha256':hashes,'usage':result.get('usage')},indent=2))
print('Local review saved:',out/'review.md')
