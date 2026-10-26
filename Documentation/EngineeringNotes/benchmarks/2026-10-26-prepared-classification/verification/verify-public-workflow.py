from pathlib import Path
import hashlib,json,subprocess,sys
import numpy as np
from scipy.special import expit
root=Path(__file__).resolve().parents[1]
source=root/'source'
verification=root/'verification'
output=verification/'public-workflow'
output.mkdir(exist_ok=True)
baseline=verification/'public-baseline/probe'
candidate=verification/'public-candidate/probe'
old_metal=Path('/private/tmp/swiftsci-prepared-pca-20261026/baseline-standardized/derived/Build/Products/Release/mlx-swift_Cmlx.bundle/Contents/Resources/default.metallib')
new_metal=root/'derived/Build/Products/Release/mlx-swift_Cmlx.bundle/Contents/Resources/default.metallib'
report={'numpy':np.__version__,'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),'cases':[],'status':'running'}
for epochs in (0,1,32):
    fixture=source/f'Benchmarks/Fixtures/supervised/inputs/wdbc-supervised-logistic-cpu-epochs{epochs}.json'
    payload=json.loads(fixture.read_text())
    result={}
    for name,binary,metal,mode in [('baseline',baseline,old_metal,'legacy'),('candidate-legacy',candidate,new_metal,'legacy'),('candidate-prepared',candidate,new_metal,'prepared')]:
        destination=output/f'epochs{epochs}-{name}.json'
        command=[str(binary),str(fixture),str(metal),mode]
        with destination.open('w') as log:
            subprocess.run(command,stdout=log,stderr=subprocess.PIPE,check=True)
        result[name]=json.loads(destination.read_text())
    x=np.array(payload['features'],dtype=np.float64);y=np.array(payload['targets'],dtype=np.float64)
    indices=[payload['splits'][name] for name in ('train','validation','test')]
    train=x[indices[0]];means=train.mean(axis=0);scales=train.std(axis=0,ddof=0)
    scales=np.where(scales<1e-12,1.,scales)
    z=[(x[rows]-means)/scales for rows in indices]
    weights=np.zeros(x.shape[1]);bias=0.
    rate=float(np.float32(payload['training']['learning_rate']))
    for _ in range(epochs):
        error=expit(z[0]@weights+bias)-y[indices[0]]
        weights-=rate*(z[0].T@error/len(indices[0]));bias-=rate*error.mean()
    probabilities=[np.column_stack((1-expit(matrix@weights+bias),expit(matrix@weights+bias))) for matrix in z]
    expected={'weights':weights.tolist(),'bias':float(bias),'probabilities':[p.tolist() for p in probabilities],'labels':[(p[:,1]>.5).astype(int).tolist() for p in probabilities],'row_positions':indices}
    max_old_new=0.;max_numpy=0.;fields=0
    def flat(r):return np.concatenate([np.asarray(r['weights']),[r['bias']],*[np.asarray(p).ravel() for p in r['probabilities']]])
    for name in ('baseline','candidate-legacy','candidate-prepared'):
        r=result[name]
        assert r['labels']==expected['labels'],(epochs,name,'labels')
        assert r['row_positions']==indices,(epochs,name,'positions')
        actual=flat(r);oracle=flat(expected)
        assert actual.shape==oracle.shape
        assert np.all(np.isfinite(actual))
        np.testing.assert_allclose(actual,oracle,atol=1e-8,rtol=1e-9)
        max_numpy=max(max_numpy,float(np.max(np.abs(actual-oracle))))
        fields+=len(actual)
    for name in ('candidate-legacy','candidate-prepared'):
        actual=flat(result[name]);old=flat(result['baseline'])
        np.testing.assert_array_equal(actual,old)
        max_old_new=max(max_old_new,float(np.max(np.abs(actual-old))))
    report['cases'].append({'epochs':epochs,'fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),'rows':len(x),'features':x.shape[1],'splits':[len(i) for i in indices],'executions':3,'numerical_fields_checked':fields,'max_old_new_abs':max_old_new,'max_numpy_abs':max_numpy,'labels_and_row_positions_exact':True})
    print('PASS WDBC',epochs,'epochs',flush=True)
report['status']='passed'
(output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
