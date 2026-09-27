from pathlib import Path
import shutil,json
root=Path('/Users/crabel/Documents/src/SwiftSci');candidate=Path('/private/tmp/swiftsci-suite-finish/vision')
for p in (candidate/'Benchmarks').rglob('*'):
 if p.is_file() and '__pycache__' not in p.parts:
  dest=root/p.relative_to(candidate);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
def edit(name,old,new):
 p=root/name;s=p.read_text();assert old in s,(name,old);p.write_text(s.replace(old,new))
edit('Benchmarks/Tools/contracts.py','WORKLOADS = {','WORKLOADS = {\n    "vision-letterbox-cpu",')
edit('Benchmarks/Tools/contracts.py','            "neural-conformance",','            "vision-conformance",\n            "neural-conformance",')
edit('Benchmarks/Tools/numerical_fixtures.py','OPERATIONS = {','from vision_fixtures import validate_input as validate_vision, output_count as vision_output_count\n\nOPERATIONS = {"vision-letterbox-cpu", ')
edit('Benchmarks/Tools/numerical_fixtures.py','    neural = manifest.get','    vision = manifest.get("operation") == "vision-letterbox-cpu"\n    require(vision == (manifest.get("reference_basis") == "vision-reference-v1"), "Vision reference basis mismatch")\n    if vision:\n        require(manifest.get("tolerances") == {"atol": 2e-6, "rtol": 2e-6}, "Vision tolerance contract mismatch")\n    neural = manifest.get')
edit('Benchmarks/Tools/numerical_fixtures.py','"neural-reference-v1"), "Unknown reference basis"','"neural-reference-v1", "vision-reference-v1"), "Unknown reference basis"')
edit('Benchmarks/Tools/numerical_fixtures.py','    if operation == "decoder-fixed-f32":','    if operation == "vision-letterbox-cpu":\n        return validate_vision(payload, operation, rows)\n    if operation == "decoder-fixed-f32":')
edit('Benchmarks/Tools/numerical_fixtures.py','manifest["operation"] == "decoder-fixed-f32":','manifest["operation"] in ("decoder-fixed-f32", "vision-letterbox-cpu"):')
edit('Benchmarks/Tools/numerical_fixtures.py','    if manifest["reference_basis"] == "neural-reference-v1":','    if manifest["reference_basis"] == "vision-reference-v1":\n        require(reference["operation"] == manifest["operation"], "Reference operation mismatch")\n        values = reference["independentReference"]["values"]\n        require(len(values) == vision_output_count(payload), "Vision reference shape mismatch")\n        finite_vector(values, "vision answers")\n        return values\n    if manifest["reference_basis"] == "neural-reference-v1":')
edit('Benchmarks/Worker/NumericalWorkloads.swift','  case fixedDecoder(', '  case visionLetterbox(VisionLetterboxInput)\n  case fixedDecoder(')
edit('Benchmarks/Worker/NumericalWorkloads.swift','let isNumerical = [','let isNumerical = ["vision-letterbox-cpu", ')
edit('Benchmarks/Worker/NumericalWorkloads.swift','    case "decoder-fixed-f32":','    case "vision-letterbox-cpu": return .visionLetterbox(try VisionLetterboxInput.decode(data, rows: rows))\n    case "decoder-fixed-f32":')
edit('Benchmarks/Worker/NumericalWorkloads.swift','    case .fixedDecoder(', '    case .visionLetterbox(let input): return try executeVisionLetterbox(input)\n    case .fixedDecoder(')
edit('Benchmarks/Python/standard_worker.py','from neural_workloads import','from vision_workloads import prepare as prepare_vision, execute as execute_vision\nfrom neural_workloads import')
edit('Benchmarks/Python/standard_worker.py','        if op == "decoder-fixed-f32":\n            controlled_input', '        if op == "vision-letterbox-cpu":\n            controlled_input = prepare_vision(numerical)\n        elif op == "decoder-fixed-f32":\n            controlled_input')
edit('Benchmarks/Python/standard_worker.py','        if op == "decoder-fixed-f32":\n            return', '        if op == "vision-letterbox-cpu":\n            return execute_vision(controlled_input)\n        if op == "decoder-fixed-f32":\n            return')
edit('Benchmarks/Tools/runner.py','"neural_reference.py"]','"neural_reference.py", "vision_fixtures.py", "vision_reference.py"]')
for name in ('dataset','workload'):
 p=root/f'Benchmarks/Specs/schemas/{name}.json';s=p.read_text().replace('"decoder-fixed-f32",','"vision-letterbox-cpu",\n        "decoder-fixed-f32",').replace('"neural-reference-v1"','"neural-reference-v1",\n        "vision-reference-v1"');p.write_text(s)
p=root/'Benchmarks/Specs/acceptance.json';d=json.loads(p.read_text());d['profiles'].append(dict(profile='vision-conformance',tier='cpu',purpose='Analytic image layout, normalization preservation, constant resize and padding'));p.write_text(json.dumps(d,indent=2)+'\n')
