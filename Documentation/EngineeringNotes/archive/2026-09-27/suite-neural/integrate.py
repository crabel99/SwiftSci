from pathlib import Path
import json
r=Path('/Users/crabel/Documents/src/SwiftSci')
def edit(path,old,new):
 p=r/path;s=p.read_text();assert old in s,(path,old);p.write_text(s.replace(old,new))
edit('Package.swift','"SwiftForecast", "SwiftExplain"],','"SwiftForecast", "SwiftExplain", "SwiftLLM",\n                .product(name: "MLX", package: "mlx-swift"),\n                .product(name: "MLXNN", package: "mlx-swift")],')
edit('Benchmarks/Tools/contracts.py','WORKLOADS = {','WORKLOADS = {\n    "decoder-fixed-f32",')
edit('Benchmarks/Tools/contracts.py','            "dataframe-conformance",','            "dataframe-conformance",\n            "neural-conformance",\n            "neural-loader-conformance",')
edit('Benchmarks/Tools/numerical_fixtures.py','OPERATIONS = {','from neural_fixtures import validate_input as validate_neural, output_count as neural_output_count\n\nOPERATIONS = {"decoder-fixed-f32", ')
edit('Benchmarks/Tools/numerical_fixtures.py','    dataframe = manifest.get','    neural = manifest.get("operation") == "decoder-fixed-f32"\n    require(neural == (manifest.get("reference_basis") == "neural-reference-v1"), "Neural reference basis mismatch")\n    if neural:\n        require(manifest.get("tolerances") == {"atol": 2e-5, "rtol": 2e-5}, "Neural tolerance contract mismatch")\n    dataframe = manifest.get')
edit('Benchmarks/Tools/numerical_fixtures.py','"dataframe-reference-v1"), "Unknown reference basis"','"dataframe-reference-v1", "neural-reference-v1"), "Unknown reference basis"')
edit('Benchmarks/Tools/numerical_fixtures.py','def validate_input(payload, operation, rows):','def validate_input(payload, operation, rows):\n    if operation == "decoder-fixed-f32":\n        return validate_neural(payload, operation, rows)')
edit('Benchmarks/Tools/numerical_fixtures.py','    if manifest["reference_basis"] == "dataframe-reference-v1":','    if manifest["reference_basis"] == "neural-reference-v1":\n        require(reference["operation"] == manifest["operation"], "Reference operation mismatch")\n        values = reference["independentReference"]["values"]\n        require(len(values) == neural_output_count(payload), "Neural reference shape mismatch")\n        finite_vector(values, "neural answers")\n        return values\n    if manifest["reference_basis"] == "dataframe-reference-v1":')
edit('Benchmarks/Tools/runner.py','"dataframe_fixtures.py"]','"dataframe_fixtures.py", "neural_fixtures.py", "neural_reference.py"]')
edit('Benchmarks/Python/standard_worker.py','from numerical_fixtures import validate_input','from numerical_fixtures import validate_input\nfrom neural_workloads import prepare as prepare_neural, execute as execute_neural')
edit('Benchmarks/Python/standard_worker.py','        if op == "dataframe-semantics":','        if op == "decoder-fixed-f32":\n            controlled_input = prepare_neural(numerical)\n        elif op == "dataframe-semantics":')
# Previous replacement also hits execute branch, correct it explicitly.
edit('Benchmarks/Python/standard_worker.py','    def execute():\n        if op == "decoder-fixed-f32":\n            controlled_input = prepare_neural(numerical)\n        elif op == "dataframe-semantics":','    def execute():\n        if op == "decoder-fixed-f32":\n            return execute_neural(controlled_input)\n        if op == "dataframe-semantics":')
for name in ('dataset','workload'):
 p=r/f'Benchmarks/Specs/schemas/{name}.json';o=json.loads(p.read_text());o['properties']['operation']['enum'].append('decoder-fixed-f32')
 if name=='dataset':o['properties']['reference_basis']['enum'].append('neural-reference-v1')
 p.write_text(json.dumps(o,indent=2)+'\n')
