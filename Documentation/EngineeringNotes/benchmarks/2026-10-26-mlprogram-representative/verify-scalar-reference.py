from pathlib import Path
import argparse, hashlib, json, math, time

p = argparse.ArgumentParser()
p.add_argument('--models', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert not a.output.exists()
results = {}
for kind in ['wdbc', 'wine']:
    path = a.models / kind / 'frozen-fixture.json'
    fixture = json.loads(path.read_text())
    maximum = 0.0
    start = time.perf_counter()
    for row, expected in enumerate(fixture['expected']):
        values = [column[row] for column in fixture['columns']]
        for index, layer in enumerate(fixture['layers']):
            width = layer['outDim']
            values = [math.fsum([layer['b'][j]] + [values[i] * layer['W'][i * width + j] for i in range(layer['inDim'])]) for j in range(width)]
            assert all(math.isfinite(value) for value in values)
            if index < len(fixture['layers']) - 1:
                values = [max(value, 0.0) for value in values]
        difference = abs(values[0] - expected)
        maximum = max(maximum, difference)
        assert difference <= 1e-12 + 1e-12 * abs(expected)
    results[kind] = dict(rows=len(fixture['expected']), maximum_absolute_difference=maximum,
        seconds=time.perf_counter() - start, fixture_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
record = dict(reference='Independent scalar Double products with math.fsum; no NumPy or BLAS',
    atol=1e-12, rtol=1e-12, datasets=results,
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
a.output.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
