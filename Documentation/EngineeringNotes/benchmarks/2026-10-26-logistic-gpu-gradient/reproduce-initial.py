from pathlib import Path
import json,math,struct,subprocess
root=Path(__file__).resolve().parent
probe=Path('/private/tmp/swiftsci-prepared-classification-20261026/verification/baseline-probe')
result=subprocess.run([str(probe)],cwd='/private/tmp/swiftsci-prepared-pca-20261026/baseline-standardized/derived/Build/Products/Release',capture_output=True,text=True,check=True)
(root/'original-rerun.json').write_text(result.stdout)
data=json.loads(result.stdout)
x=[[(i%17-8)/4,((i*7)%19-9)/5] for i in range(1000)]
y=[float(a*.8-b*.35>.15) for a,b in x]
lr=struct.unpack('f',struct.pack('f',.05))[0]
expected_bias=-lr*sum(.5-t for t in y)/len(y)
expected_weights=[-lr*sum(row[j]*(.5-t) for row,t in zip(x,y))/len(y) for j in range(2)]
for route in ('cpu','gpu'):
 c=next(c for c in data['cases'] if c['requested']==route and c['epochs']==1)
 print(route,'bias',c['bias'],'expected',expected_bias,'absolute error',abs(c['bias']-expected_bias),flush=True)
 if route=='gpu':
  assert math.isclose(c['bias'],expected_bias,abs_tol=1e-6),'GPU first update disagrees with analytical BCE gradient'
print('PASS')
