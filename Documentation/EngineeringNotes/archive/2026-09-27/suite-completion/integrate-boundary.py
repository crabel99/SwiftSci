from pathlib import Path
import shutil,json
root=Path('/Users/crabel/Documents/src/SwiftSci');scratch=Path('/private/tmp/swiftsci-suite-finish/boundary')
for name in ['BoundaryWorkloads.swift','BoundarySweepWorkloads.swift']:shutil.copyfile(scratch/name,root/'Benchmarks/Worker'/name)
for name in ['boundary_fixtures.py','boundary_reference.py','boundary_cases.py','boundary_sweep.py']:shutil.copyfile(scratch/name,root/'Benchmarks/Tools'/name)
shutil.copyfile(scratch/'boundary_workloads.py',root/'Benchmarks/Python/boundary_workloads.py')
p=root/'Benchmarks/Tests/test_boundary.py';s=(scratch/'test_boundary.py').read_text();s='from pathlib import Path\nimport sys\nsys.path.insert(0,str(Path(__file__).resolve().parents[1]/"Tools"))\nsys.path.insert(0,str(Path(__file__).resolve().parents[1]/"Python"))\n'+s;p.write_text(s)
def edit(name,old,new):
 p=root/name;s=p.read_text();assert old in s,(name,old);p.write_text(s.replace(old,new))
edit('Benchmarks/Tools/contracts.py','WORKLOADS = {','WORKLOADS = {\n    "dataframe-model", "dataframe-model-sweep",')
edit('Benchmarks/Tools/contracts.py','            "vision-conformance",','            "boundary-conformance", "boundary-cpu-conformance", "boundary-sweep",\n            "vision-conformance",')
edit('Benchmarks/Tools/numerical_fixtures.py','OPERATIONS = {','from boundary_fixtures import validate_input as validate_boundary, output_count as boundary_output_count\nfrom boundary_sweep import validate_descriptor, reference as sweep_reference, output_count as sweep_output_count\nfrom contracts import digest\nimport struct\n\nOPERATIONS = {"dataframe-model", "dataframe-model-sweep", ')
edit('Benchmarks/Tools/numerical_fixtures.py','    vision = manifest.get','    for operation, basis in [("dataframe-model", "boundary-reference-v1"),("dataframe-model-sweep", "sweep-reference-v1")]:\n        require((manifest.get("operation") == operation) == (manifest.get("reference_basis") == basis), "Boundary reference basis mismatch")\n        if manifest.get("operation") == operation:\n            require(manifest.get("tolerances") in ({"atol":2e-5,"rtol":0},{"atol":1e-12,"rtol":0}), "Boundary tolerance contract mismatch")\n    vision = manifest.get')
edit('Benchmarks/Tools/numerical_fixtures.py','"vision-reference-v1"), "Unknown reference basis"','"vision-reference-v1", "boundary-reference-v1", "sweep-reference-v1"), "Unknown reference basis"')
edit('Benchmarks/Tools/numerical_fixtures.py','    if operation == "vision-letterbox-cpu":','    if operation == "dataframe-model":\n        return validate_boundary(payload, operation, rows)\n    if operation == "dataframe-model-sweep":\n        return validate_descriptor(payload, operation, rows)\n    if operation == "vision-letterbox-cpu":')
edit('Benchmarks/Tools/numerical_fixtures.py','in ("decoder-fixed-f32", "vision-letterbox-cpu"):', 'in ("decoder-fixed-f32", "vision-letterbox-cpu", "dataframe-model", "dataframe-model-sweep"):')
edit('Benchmarks/Tools/numerical_fixtures.py','    if manifest["reference_basis"] == "vision-reference-v1":','''    if manifest["reference_basis"] in ("boundary-reference-v1", "sweep-reference-v1"):
        require(reference["operation"] == manifest["operation"], "Reference operation mismatch")
        if manifest["operation"] == "dataframe-model-sweep":
            values = sweep_reference(payload)
            raw = struct.pack('<' + 'd'*len(values), *values)
            require(len(values) == reference["independentReference"]["count"] == sweep_output_count(payload), "Sweep reference count mismatch")
            require(digest(raw) == reference["independentReference"]["binary64_sha256"], "Sweep reference digest mismatch")
        else:
            values = reference["independentReference"]["values"]
            require(len(values) == boundary_output_count(payload), "Boundary reference count mismatch")
        finite_vector(values, "boundary answers")
        return values
    if manifest["reference_basis"] == "vision-reference-v1":''')
edit('Benchmarks/Worker/NumericalWorkloads.swift','  case visionLetterbox(', '  case boundary(BoundaryInput)\n  case boundarySweep(BoundarySweepInput)\n  case visionLetterbox(')
edit('Benchmarks/Worker/NumericalWorkloads.swift','let isNumerical = [','let isNumerical = ["dataframe-model", "dataframe-model-sweep", ')
edit('Benchmarks/Worker/NumericalWorkloads.swift','    case "vision-letterbox-cpu":','    case "dataframe-model": return .boundary(try BoundaryInput.decode(data, rows: rows))\n    case "dataframe-model-sweep": return .boundarySweep(try BoundarySweepInput.decode(data, rows: rows))\n    case "vision-letterbox-cpu":')
edit('Benchmarks/Worker/NumericalWorkloads.swift','    case .visionLetterbox(', '    case .boundary(let input): return try executeBoundary(input)\n    case .boundarySweep(let input): return try executeBoundarySweep(input)\n    case .visionLetterbox(')
edit('Benchmarks/Python/standard_worker.py','from vision_workloads import','from boundary_workloads import prepare as prepare_boundary, execute as execute_boundary\nfrom boundary_sweep import prepare as prepare_sweep, execute as execute_sweep\nfrom vision_workloads import')
edit('Benchmarks/Python/standard_worker.py','        if op == "vision-letterbox-cpu":\n            controlled_input', '        if op == "dataframe-model":\n            controlled_input = prepare_boundary(numerical)\n        elif op == "dataframe-model-sweep":\n            controlled_input = prepare_sweep(numerical)\n        elif op == "vision-letterbox-cpu":\n            controlled_input')
edit('Benchmarks/Python/standard_worker.py','        if op == "vision-letterbox-cpu":\n            return', '        if op == "dataframe-model":\n            return execute_boundary(controlled_input)\n        if op == "dataframe-model-sweep":\n            return execute_sweep(controlled_input)\n        if op == "vision-letterbox-cpu":\n            return')
edit('Benchmarks/Tools/runner.py','"vision_reference.py"]','"vision_reference.py", "boundary_fixtures.py", "boundary_reference.py", "boundary_sweep.py"]')
for name in ('dataset','workload'):
 p=root/f'Benchmarks/Specs/schemas/{name}.json';d=json.loads(p.read_text());d['properties']['operation']['enum']+=['vision-letterbox-cpu','dataframe-model','dataframe-model-sweep']
 if name=='dataset':d['properties']['reference_basis']['enum']+=['boundary-reference-v1','sweep-reference-v1']
 p.write_text(json.dumps(d,indent=2)+'\n')
p=root/'Benchmarks/Specs/acceptance.json';d=json.loads(p.read_text());d['profiles'] += [dict(profile=name,tier=tier,purpose=purpose) for name,tier,purpose in [('boundary-cpu-conformance','cpu','CPU dataframe to tensor values, alignment, dtype and isolation'),('boundary-conformance','apple','CPU and Metal dataframe to tensor conformance'),('boundary-sweep','sweep','Bounded size and stage sweeps, not a formal performance baseline')]];p.write_text(json.dumps(d,indent=2)+'\n')
