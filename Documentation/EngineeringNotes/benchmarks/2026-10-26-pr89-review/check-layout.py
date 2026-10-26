from pathlib import Path
import argparse,hashlib,json,subprocess,time
r=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('tag');a=p.parse_args();out=r/('layout-'+a.tag);out.mkdir(exist_ok=False)
files=[r/'source/Sources/SwiftDataFrame/Errors/SwiftMLError.swift',r/'source/Sources/SwiftCluster/Decomposition/PCAFullSVDLayout.swift',r/'LayoutProbe.swift']
cmd=['xcrun','swiftc','-parse-as-library','-swift-version','6','-module-name','SwiftDataFrame',*[str(x) for x in files],'-o',str(out/'probe')]
with (out/'build.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
start=time.time()
with (out/'run.log').open('w') as log:result=subprocess.run([str(out/'probe')],stdout=log,stderr=subprocess.STDOUT)
(out/'result.json').write_text(json.dumps(dict(exit_code=result.returncode,seconds=time.time()-start,command=cmd,sources={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in files}),indent=2)+'\n')
print((out/'run.log').read_text());raise SystemExit(result.returncode)
