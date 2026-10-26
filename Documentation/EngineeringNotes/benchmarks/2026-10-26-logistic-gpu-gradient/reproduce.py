from pathlib import Path
import argparse,json,math,struct,subprocess
root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--probe',type=Path);parser.add_argument('--metal',type=Path);args=parser.parse_args()
probe=args.probe or Path('/private/tmp/swiftsci-prepared-classification-20261026/verification/baseline-probe')
result=subprocess.run([str(probe)]+([str(args.metal)] if args.metal else []),cwd='/private/tmp/swiftsci-prepared-pca-20261026/baseline-standardized/derived/Build/Products/Release',capture_output=True,text=True,check=True)
(root/('corrected-rerun.json' if args.probe else 'original-rerun.json')).write_text(result.stdout)
data=json.loads(result.stdout)
x=[[(i%17-8)/4,((i*7)%19-9)/5] for i in range(1000)]
y=[float(a*.8-b*.35>.15) for a,b in x]
lr=struct.unpack('f',struct.pack('f',.05))[0]
expected_bias=-lr*sum(.5-t for t in y)/len(y)
for route in ('cpu','gpu'):
 c=next(c for c in data['cases'] if c['requested']==route and c['epochs']==1)
 print(route,'bias',c['bias'],'expected',expected_bias,'absolute error',abs(c['bias']-expected_bias),flush=True)
 if route=='gpu':
  assert math.isclose(c['bias'],expected_bias,abs_tol=1e-6),'GPU first update disagrees with analytical BCE gradient'
print('PASS')
