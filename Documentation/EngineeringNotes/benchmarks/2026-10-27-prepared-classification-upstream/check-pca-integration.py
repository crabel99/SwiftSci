from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys
r = Path(__file__).resolve().parent
s = r / 'source'
out = r / 'pca-integration'
out.mkdir(exist_ok=False)
git = lambda *args: subprocess.check_output(['git', *args], cwd=s, text=True).strip()
head = git('rev-parse', 'HEAD')
pca = '4f33c76f3938e070105c2a5928c712aa5e067a00'
tree = git('merge-tree', '--write-tree', head, pca)
commit = subprocess.check_output(['git', 'commit-tree', tree, '-p', head, '-p', pca], input='Qualification-only PCA and classification integration\n', cwd=s, text=True).strip()
subprocess.run(['git', 'clone', '--shared', '--no-checkout', str(s), str(out / 'source')], check=True)
subprocess.run(['git', 'checkout', '--detach', commit], cwd=out / 'source', check=True)
assert subprocess.check_output(['git', 'status', '--porcelain'], cwd=out / 'source', text=True) == ''
prior = Path('/private/tmp/swiftsci-upstream-doc-reporting-20261027')
for name in ['derived', 'native-packages']:
    subprocess.run(['cp', '-cR', str(prior / name), str(out / name)], check=True)
shutil.copy2(r / 'validate-native.py', out / 'validate-native.py')
selected = ['SwiftMLTests/PreparedLogisticRegressionTests', 'SwiftMLTests/PreparedClassificationIntegrationTests', 'SwiftMLTests/ClassificationPipelineConcurrencyTests', 'SwiftDataFrameTests/PreparedRowMappingTests', 'SwiftClusterTests/PreparedPCATests', 'SwiftClusterTests/PreparedPCAGPUTests', 'SwiftClusterTests/PCAMeanOverflowTests', 'SwiftClusterTests/PCAFullSVDLayoutTests']
command = [sys.executable, str(out / 'validate-native.py'), 'Debug', 'pca-classification', *selected]
report = dict(classification=head, pca=pca, tree=tree, integration_commit=commit, selected=selected, command=command, controller_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), scope='Qualification-only clean merge, not a source delivery or upstream merge')
(out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
result = subprocess.run(command, cwd=out / 'source')
report.update(exit_code=result.returncode, status='passed' if result.returncode == 0 else 'failed')
(out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
raise SystemExit(result.returncode)
