from pathlib import Path
p=Path('Benchmarks/Tools/acceptance.py');s=p.read_text().replace('from collections import Counter\n','').replace('from runner import source_identity','from runner import source_identity\nfrom datasets import cache_path, reference, binary, load_manifest, resolve_workload\nfrom contracts import load_workload, verified_file')
s=s.replace('def inspect_run(directory, profile, source, engines):','''def contract_identity(root):
    names = subprocess.check_output(['git', '-C', str(root), 'ls-files'], text=True).splitlines()
    return identity({name: digest((root / name).read_bytes()) for name in names
                     if name.startswith(('Benchmarks/Specs/', 'Benchmarks/Fixtures/')) and (root / name).is_file()})


def inspect_run(directory, profile, source, engines, root):''')
s=s.replace("    for c in cases:\n        require(c['case_key']", "    for c in cases:\n        dataset = load_manifest(root, c['case']['dataset'])\n        workload = resolve_workload(dataset, load_workload(root, c['case']['workload']))\n        require(c['dataset'] == dataset and c['workload'] == workload, 'Resolved contract differs')\n        require(c['case_key']")
s=s.replace("        require(request['case_key'] == expected[key] and request['samples'] == profile['samples'], 'Request identity differs')",'''        case = next(c for c in cases if c['case']['id'] == key[0])
        dataset, workload = case['dataset'], case['workload']
        input_path = cache_path(root, dataset)
        verified_file(input_path, dataset['sha256'], dataset['size_bytes'])
        expected_path = directory / (key[0] + '.expected.f64')
        expected_bytes = binary(reference(root, dataset, workload))
        require(expected_path.read_bytes() == expected_bytes, 'Independent expected output differs')
        expected_request = dict(schema_version=1, case_key=expected[key], operation=workload['operation'],
            dataset_kind=dataset['kind'], input_path=str(input_path), input_sha256=dataset['sha256'],
            input_bytes=dataset['size_bytes'], expected_path=str(expected_path), expected_sha256=digest(expected_bytes),
            rows=dataset['rows'], warmups=profile['warmups'], samples=profile['samples'],
            atol=workload['atol'], rtol=workload['rtol'])
        if dataset['kind'] == 'nist-univariate-v1': expected_request['input_skip_rows'] = dataset['data_start_line'] - 1
        require(request == expected_request, 'Request contract differs')''')
s=s.replace("                require(response['status'] == 'failed'", "                fields(response, ['schema_version','case_key','status','samples','peak_rss_bytes','engine_version','error'])\n                require(response['schema_version'] == 1 and response['samples'] == [] and\n                        type(response['peak_rss_bytes']) is int and response['peak_rss_bytes'] > 0 and\n                        isinstance(response['engine_version'],str) and response['engine_version'], 'Invalid failed response fields')\n                require(event.get('failed_result') == response, 'Failed response differs from event')\n                require(response['status'] == 'failed'")
s=s.replace('    source = source_identity(root)','    source = source_identity(root)\n    frozen_contract = contract_identity(root)',1)
s=s.replace("tier=tier, profiles=[]", "contract_sha256=frozen_contract, tier=tier, profiles=[]")
s=s.replace("require(source_identity(root) == source, 'Source changed during acceptance')", "require(source_identity(root) == source and contract_identity(root) == frozen_contract, 'Source or contract changed during acceptance')")
s=s.replace("            base = [python", "            profile = load_profile(root, name)\n            base = [python")
s=s.replace("cwd=root, stdout=log, stderr=subprocess.STDOUT)\n            require(prepared", "cwd=root, stdout=log, stderr=subprocess.STDOUT, timeout=600)\n            require(prepared")
s=s.replace("cwd=root, stdout=log, stderr=subprocess.STDOUT)\n            record.update(inspect_run", "cwd=root, stdout=log, stderr=subprocess.STDOUT, timeout=600 + len(profile['cases'])*profile['batches']*2*profile['timeout_seconds'])\n            record.update(inspect_run")
s=s.replace("source, ['swiftsci', 'pandas']))", "source, ['swiftsci', 'pandas'], root))")
s=s.replace('except (OSError, ValueError, KeyError) as error:\n            record.update', 'except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:\n            record.update')
p.write_text(s)
p=Path('Benchmarks/Tools/runner.py');s=p.read_text();s=s.replace('                    event["error"] = str(error)','''                    event["error"] = str(error)
                    if response_path.is_file():
                        try:
                            event["failed_result"] = read_json(response_path)
                        except (OSError, ValueError):
                            pass''');p.write_text(s)
