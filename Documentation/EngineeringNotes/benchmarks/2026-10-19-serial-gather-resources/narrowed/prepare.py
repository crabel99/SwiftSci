from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parent
repo='/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018'
refs={'baseline':'d23bf7cac92fe9f9c10bd98046ca8ade354b5a3c','candidate':'546510bb7df19fc87a664bded5947c738011ee1d'}
variants={}
for label,ref in refs.items():
 root=R/'sources'/label
 paths=subprocess.check_output(['git','ls-tree','-r','--name-only',ref,'Sources/SwiftDataFrame'],cwd=repo,text=True).splitlines()
 for p in paths:
  dest=root/p;dest.parent.mkdir(parents=True,exist_ok=True)
  data=subprocess.check_output(['git','show',ref+':'+p],cwd=repo)
  if dest.exists():assert dest.read_bytes()==data
  else:dest.write_bytes(data)
 variants[label]={'path':str(root),'sha':ref,'pr':None}
(R/'variants.json').write_text(json.dumps(variants,indent=2)+'\n')
