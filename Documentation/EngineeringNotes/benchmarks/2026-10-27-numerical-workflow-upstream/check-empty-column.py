from pathlib import Path
import argparse, csv, hashlib, json, os, subprocess

p = argparse.ArgumentParser()
p.add_argument('--binary', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
r = Path(__file__).resolve().parent
s = r / 'source'
out = a.output.resolve()
out.mkdir(exist_ok=False)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
with (s / 'Examples/NumericalWorkflow/Data/sample.csv').open(newline='') as stream:
    table = list(csv.reader(stream))
header, rows = table[0], table[1:]
empty = [row[:2] + [''] + row[3:] for row in rows]
late = [empty[i % len(empty)][:] for i in range(1000)] + [rows[0][:]]
invalid = [row[:] for row in rows]
invalid[-1][2] = 'invalid-text'
cases = []
for name, data in [('all-missing-feature', empty), ('first-numeric-after-1000', late), ('invalid-feature-text', invalid)]:
    input_path = out / (name + '.csv')
    with input_path.open('w', newline='') as stream:
        csv.writer(stream).writerows([header, *data])
    directory = out / (name + '-results')
    command = [str(a.binary.resolve()), '--input', str(input_path), '--output', str(directory)]
    log_path = out / (name + '.log')
    with log_path.open('w') as log:
        result = subprocess.run(command, cwd=s, env=dict(os.environ, LLVM_PROFILE_FILE=str(out / 'profile-%p.profraw')), stdout=log, stderr=subprocess.STDOUT, timeout=120)
    assert result.returncode != 0 and "Cannot cast column 'constant' to Double" in log_path.read_text()
    assert not directory.exists()
    cases.append(dict(name=name, command=command, exit_code=result.returncode, input_sha256=sha(input_path), log_sha256=sha(log_path)))
receipt = dict(status='passed', expectation='CSV inference rejects empty, late-first-numeric and invalid-text feature columns before imputation', source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=s,text=True).strip(), cases=cases, binary_sha256=sha(a.binary), controller_sha256=sha(Path(__file__)))
(out / 'result.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
