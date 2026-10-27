from pathlib import Path
import argparse, copy, csv, hashlib, json, math, os, shutil, subprocess, sys

p = argparse.ArgumentParser()
p.add_argument('--binary', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--label', required=True)
p.add_argument('--require-clean', action='store_true')
a = p.parse_args()
r = Path(__file__).resolve().parent
s = r / 'source'
binary = a.binary.resolve()
out = a.output.resolve()
out.mkdir(exist_ok=False)
(out / 'profiles').mkdir()
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
git = lambda *args: subprocess.check_output(['git', *args], cwd=s, text=True).strip()
files = ['Package.swift', 'README.md', *[str(x.relative_to(s)) for x in (s / 'Examples/NumericalWorkflow').rglob('*') if x.is_file() and '__pycache__' not in x.parts]]
before = {name: sha(s / name) for name in files}
status = git('status', '--porcelain')
if a.require_clean:
    assert not status
resources = [f for bundle in binary.parent.glob('*ScientificWorkflow*.bundle') for f in bundle.rglob('sample.csv')]
assert len(resources) == 1 and sha(resources[0]) == sha(s / 'Examples/NumericalWorkflow/Data/sample.csv')
state = dict(label=a.label, source=git('rev-parse', 'HEAD'), initial_git_status=status,
             source_sha256=before, binary=str(binary), binary_sha256=sha(binary),
             resource=str(resources[0]), resource_sha256=sha(resources[0]),
             controller_sha256=sha(Path(__file__)), steps=[], status='running')


def save():
    (out / 'result.json').write_text(json.dumps(state, indent=2) + '\n')


def run(name, command, expected=0, diagnostic=None):
    log = out / (name + '.log')
    env = dict(os.environ, LLVM_PROFILE_FILE=str(out / 'profiles' / (name + '-%p.profraw')))
    with log.open('w') as stream:
        result = subprocess.run(command, cwd=s, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=120)
    text = log.read_text()
    passed = result.returncode == 0 if expected == 0 else result.returncode != 0
    passed = passed and (diagnostic is None or diagnostic.lower() in text.lower())
    state['steps'].append(dict(name=name, command=[str(x) for x in command], exit_code=result.returncode,
                               expected='success' if expected == 0 else 'rejected', status='passed' if passed else 'failed',
                               log_sha256=sha(log)))
    save()
    assert passed, (name, result.returncode, text[-1500:])


def invoke(name, input_path=None):
    directory = out / name
    command = [str(binary), '--output', str(directory)]
    if input_path is not None:
        command += ['--input', str(input_path)]
    run(name, command)
    return directory


checker = s / 'Examples/NumericalWorkflow/verify.py'
save()
outputs = [invoke('bundled-first'), invoke('bundled-repeat')]
inputs = out / 'inputs with spaces'
inputs.mkdir()
explicit = inputs / 'sample input.csv'
shutil.copyfile(s / 'Examples/NumericalWorkflow/Data/sample.csv', explicit)
outputs.append(invoke('output with spaces', explicit))
for index, directory in enumerate(outputs):
    run('verify-fixture-' + str(index), [sys.executable, str(checker), str(directory)])
for name in ['report.json', 'predictions.csv']:
    assert len({sha(directory / name) for directory in outputs}) == 1, ('repeatability', name)
baseline = json.loads((outputs[0] / 'report.json').read_text())
with explicit.open(newline='') as stream:
    table = list(csv.reader(stream))
header, rows = table[0], table[1:]


def write_input(name, data, names=None):
    path = inputs / (name + '.csv')
    with path.open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(header if names is None else names)
        writer.writerows(data)
    return path


fitted_keys = ['imputationStatistics', 'scalingMean', 'scalingStd', 'pcaMean', 'pcaComponents',
               'pcaVariance', 'weights', 'bias', 'trainingScores', 'scaledTraining']
changed_features = copy.deepcopy(rows)
for row in changed_features[8:]:
    row[0] = str(float(row[0]) * 3)
    row[1] = ''
feature_output = invoke('heldout-features-changed', write_input('heldout-features-changed', changed_features))
feature_report = json.loads((feature_output / 'report.json').read_text())
assert all(feature_report[key] == baseline[key] for key in fitted_keys), 'Held-out features changed fitted state'
expected_probabilities = []
for row_id in [11, 10, 9, 8]:
    raw = [float(changed_features[row_id][0]), baseline['imputationStatistics'][1], 7.0]
    scaled = [(x - mean) / deviation for x, mean, deviation in zip(raw, baseline['scalingMean'], baseline['scalingStd'])]
    centered = [x - mean for x, mean in zip(scaled, baseline['pcaMean'])]
    scores = [math.fsum(x * y for x, y in zip(centered, vector)) for vector in baseline['pcaComponents']]
    positive = 1 / (1 + math.exp(-math.fsum(x * y for x, y in zip(scores, baseline['weights'])) - baseline['bias']))
    expected_probabilities.append([1 - positive, positive])
assert all(abs(found - expected) <= 1e-12 + 1e-12 * abs(expected)
           for left, right in zip(feature_report['probabilities'], expected_probabilities) for found, expected in zip(left, right))
changed_targets = copy.deepcopy(rows)
for row in changed_targets[8:]:
    row[3] = str(1 - int(row[3]))
target_output = invoke('heldout-targets-changed', write_input('heldout-targets-changed', changed_targets))
target_report = json.loads((target_output / 'report.json').read_text())
assert all(target_report[key] == baseline[key] for key in fitted_keys + ['queryScores', 'probabilities', 'predictions'])
assert target_report['accuracy'] == 0 and target_report['queryTargets'] == [1 - x for x in baseline['queryTargets']]

bad_label = copy.deepcopy(rows)
bad_label[-1][3] = '2'
missing_label = copy.deepcopy(rows)
missing_label[-1][3] = ''
infinite = copy.deepcopy(rows)
infinite[-1][0] = 'inf'
one_class = copy.deepcopy(rows)
for row in one_class[:8]:
    row[3] = '0'
rejects = [
    ('missing-input', inputs / 'missing.csv', 'missing'),
    ('missing-target', write_input('missing-target', [row[:3] for row in rows], header[:3]), 'class'),
    ('invalid-label', write_input('invalid-label', bad_label), '0 or 1'),
    ('missing-label', write_input('missing-label', missing_label), '0 or 1'),
    ('infinite-feature', write_input('infinite-feature', infinite), 'infinite'),
    ('too-few-rows', write_input('too-few-rows', rows[:5]), 'six'),
    ('one-training-class', write_input('one-training-class', one_class), 'both class')
]
for name, path, diagnostic in rejects:
    directory = out / name
    run(name, [str(binary), '--input', str(path), '--output', str(directory)], expected=1, diagnostic=diagnostic)
    assert not directory.exists(), name
overwrite = out / 'overwrite-input'
overwrite.mkdir()
protected = overwrite / 'predictions.csv'
shutil.copyfile(explicit, protected)
original = sha(protected)
run('overwrite-input', [str(binary), '--input', str(protected), '--output', str(overwrite)], expected=1, diagnostic='overwrite')
assert sha(protected) == original and not (overwrite / 'report.json').exists()
run('unknown-option', [str(binary), '--unknown-option'], expected=1, diagnostic='unknown option')
run('help', [str(binary), '--help'])

for name in ['wrong-imputation', 'wrong-row-id', 'wrong-probability', 'leaked-selection', 'boolean-accuracy']:
    folder = out / ('oracle-' + name)
    shutil.copytree(outputs[0], folder)
    report = copy.deepcopy(baseline)
    if name == 'wrong-imputation':
        report['imputationStatistics'][0] += 0.1
    elif name == 'wrong-probability':
        report['probabilities'][0][1] += 0.1
    elif name == 'leaked-selection':
        report['trainingSourceRows'][-1] = 8
    elif name == 'boolean-accuracy':
        report['accuracy'] = True
    else:
        with (folder / 'predictions.csv').open(newline='') as stream:
            altered = list(csv.reader(stream))
        altered[1][0] = '999'
        with (folder / 'predictions.csv').open('w', newline='') as stream:
            csv.writer(stream).writerows(altered)
    (folder / 'report.json').write_text(json.dumps(report) + '\n')
    run('oracle-' + name, [sys.executable, str(checker), str(folder)], expected=1, diagnostic='AssertionError')

assert all(sha(s / name) == digest for name, digest in before.items())
assert sha(binary) == state['binary_sha256'] and sha(resources[0]) == state['resource_sha256']
assert git('status', '--porcelain') == status
state.update(status='passed', steps_count=len(state['steps']), repeatability='CSV and JSON bytes identical across two default and one explicit-file processes',
             heldout_controls='Changing held-out features or targets leaves all fitted state unchanged; changed-feature probabilities checked by scalar use of independently verified baseline parameters',
             outputs={str(folder.relative_to(out)): {name: sha(folder / name) for name in ['report.json', 'predictions.csv']} for folder in outputs + [feature_output, target_output]},
             profile_files={str(path.relative_to(out)): sha(path) for path in (out / 'profiles').glob('*.profraw')})
save()
print(json.dumps(dict(status=state['status'], label=a.label, steps=state['steps_count'], source=state['source']), indent=2))
