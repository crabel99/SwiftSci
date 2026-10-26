from pathlib import Path
import argparse, hashlib, json, math
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args();r=a.run
prepared=json.loads((r/'prepared.json').read_text());legacy=json.loads((r/'legacy.json').read_text())
errors={}
def close(name,actual,expected):
    if isinstance(expected,list):
        assert len(actual)==len(expected),(name,'shape')
        for index,(found,wanted) in enumerate(zip(actual,expected)):close(name,found,wanted)
    else:
        assert math.isfinite(actual) and math.isfinite(expected),(name,'nonfinite')
        difference=abs(actual-expected);errors[name]=max(errors.get(name,0),difference)
        assert difference<=1e-12+1e-12*abs(expected),(name,actual,expected,difference)

def dot(left,right):return math.fsum(x*y for x,y in zip(left,right))
def sigmoid(value):return 1/(1+math.exp(-value))

train_ids=list(range(8));query_ids=[10,8,10,9,11]
raw=[[-4,-7,7],[-3,-5,7],[-2,None,7],[-1,-1,7],[1,2,7],[2,3,7],[3,6,7],[4,8,7],[-2.5,-4.5,7],[2.5,5,7],[0.5,None,7],[-0.5,1,7]]
targets=[0,0,0,0,1,1,1,1,0,1,1,0]
assert prepared['rawRows']==raw and prepared['sourceTargets']==targets
assert prepared['trainingSourceRows']==train_ids and prepared['querySourceRows']==query_ids
assert set(train_ids).isdisjoint(query_ids) and prepared['sourceSnapshotPreserved'] is True
assert prepared['featureNames']==['signal','companion','constant'] and prepared['scoreNames']==['PC1','PC2']
assert prepared['trainingTargets']==[targets[i] for i in train_ids]
assert prepared['queryTargets']==[targets[i] for i in query_ids]
assert prepared['epochs']==64 and prepared['learningRate']==0.125
replacements=[]
for column in range(3):
    values=[raw[i][column] for i in train_ids if raw[i][column] is not None]
    replacements.append(math.fsum(values)/len(values))
imputed=[[replacements[j] if value is None else value for j,value in enumerate(row)] for row in raw]
means=[math.fsum(imputed[i][j] for i in train_ids)/8 for j in range(3)]
deviations=[math.sqrt(math.fsum((imputed[i][j]-means[j])**2 for i in train_ids)/8) for j in range(3)]
deviations=[value if value>=1e-12 else 1 for value in deviations]
scaled=[[(row[j]-means[j])/deviations[j] for j in range(3)] for row in imputed]
train=[scaled[i] for i in train_ids];query=[scaled[i] for i in query_ids]
close('imputation',prepared['imputationStatistics'],replacements)
close('scaling_mean',prepared['scalingMean'],means)
close('scaling_std',prepared['scalingStd'],deviations)
close('scaled_training',prepared['scaledTraining'],train)
close('scaled_query',prepared['scaledQuery'],query)
assert all(row[2]==0 for row in prepared['scaledTraining']+prepared['scaledQuery'])

# Independent closed-form eigensystem of the two varying standardized features.
pca_mean=[math.fsum(row[j] for row in train)/8 for j in range(3)]
centered=[[row[j]-pca_mean[j] for j in range(3)] for row in train]
aa=math.fsum(row[0]**2 for row in centered)/7
bb=math.fsum(row[0]*row[1] for row in centered)/7
cc=math.fsum(row[1]**2 for row in centered)/7
discriminant=math.hypot(aa-cc,2*bb)
variances=[(aa+cc+discriminant)/2,(aa+cc-discriminant)/2]
assert bb!=0 and variances[0]>variances[1]>0
vectors=[]
for index,value in enumerate(variances):
    vector=[bb,value-aa,0.0];length=math.sqrt(dot(vector,vector));vector=[x/length for x in vector]
    if dot(vector,prepared['pcaComponents'][index])<0:vector=[-x for x in vector]
    vectors.append(vector)
close('pca_mean',prepared['pcaMean'],pca_mean)
close('pca_variance',prepared['pcaVariance'],variances)
close('pca_components',prepared['pcaComponents'],vectors)
close('pca_orthogonality',dot(prepared['pcaComponents'][0],prepared['pcaComponents'][1]),0)
score=lambda rows:[[dot([row[j]-pca_mean[j] for j in range(3)],vector) for vector in vectors] for row in rows]
train_scores=score(train);query_scores=score(query)
close('training_scores',prepared['trainingScores'],train_scores)
close('query_scores',prepared['queryScores'],query_scores)

# Independent scalar full-batch binary logistic updates, using the independently computed scores.
weights=[0.0,0.0];bias=0.0
for _ in range(64):
    residuals=[sigmoid(dot(row,weights)+bias)-targets[i] for i,row in enumerate(train_scores)]
    gradients=[math.fsum(error*row[j] for error,row in zip(residuals,train_scores))/8 for j in range(2)]
    weights=[weight-0.125*gradient for weight,gradient in zip(weights,gradients)]
    bias-=0.125*math.fsum(residuals)/8
probabilities=[[1-(positive:=sigmoid(dot(row,weights)+bias)),positive] for row in query_scores]
predictions=[int(row[1]>0.5) for row in probabilities]
close('logistic_weights',prepared['weights'],weights);close('logistic_bias',prepared['bias'],bias)
close('probabilities',prepared['probabilities'],probabilities)
assert prepared['predictions']==predictions
for index,row in enumerate(prepared['outputRows']):
    assert row['sourceRow']==query_ids[index] and row['target']==targets[query_ids[index]]
    assert row['prediction']==predictions[index]
    close('associated_probability',row['probabilityClass1'],probabilities[index][1])
assert prepared['queryScores'][0]==prepared['queryScores'][2]
assert prepared['probabilities'][0]==prepared['probabilities'][2]

# The legacy control is an API parity check, separate from the independent scalar oracle.
for name in ['imputationStatistics','scalingMean','scalingStd','scaledTraining','scaledQuery','pcaMean','pcaVariance','probabilities','bias']:
    close('legacy_'+name,prepared[name],legacy[name])
signs=[1 if dot(left,right)>=0 else -1 for left,right in zip(prepared['pcaComponents'],legacy['pcaComponents'])]
close('legacy_components',prepared['pcaComponents'],[[sign*x for x in row] for sign,row in zip(signs,legacy['pcaComponents'])])
for name in ['trainingScores','queryScores']:
    close('legacy_'+name,prepared[name],[[sign*x for sign,x in zip(signs,row)] for row in legacy[name]])
close('legacy_weights',prepared['weights'],[sign*x for sign,x in zip(signs,legacy['weights'])])
assert prepared['predictions']==legacy['predictions']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=dict(status='passed',tolerance='abs(error)<=1e-12+1e-12*abs(reference)',
    source=json.loads((r/'provenance.json').read_text())['source'],training_rows=8,query_rows=query_ids,
    independent='Scalar training-only preprocessing; closed-form 2x2 PCA eigensystem with sign alignment; scalar64-step logistic gradient descent',
    legacy_control='Separate public nested-row preprocessing/PCA/classifier fit on identical frozen data',
    maximum_absolute_errors=errors,predictions=predictions,statistical_quality_claim=False,performance_claim=False,
    verifier_sha256=sha(Path(__file__)),prepared_sha256=sha(r/'prepared.json'),legacy_sha256=sha(r/'legacy.json'))
(r/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
