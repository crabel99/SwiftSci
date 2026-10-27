"""Bind actual supplemental LCOV hits to added LocalEmbeddingEngine executable lines."""
from pathlib import Path
import hashlib, json, re, subprocess
r = Path(__file__).resolve().parent
s = r / 'source'
target = 'Sources/SwiftNLP/Core/LocalEmbeddingEngine.swift'
base = '01d48cbcd940c886546b2bb8d6b177d9b7a0e277'
coverage = r / 'coverage-supplement/coverage.lcov'
records = []
for record in coverage.read_text().split('end_of_record'):
    lines = record.splitlines()
    paths = [line[3:] for line in lines if line.startswith('SF:')]
    if paths and paths[0].endswith('/' + target):
        hits = {}
        functions = []
        for line in lines:
            if line.startswith('DA:'):
                number, count, *_ = line[3:].split(',')
                hits[int(number)] = max(hits.get(int(number), 0), int(count))
            elif line.startswith('FNDA:'):
                count, name = line[5:].split(',', 1)
                functions.append(dict(name=name, count=int(count)))
        records.append(dict(path=paths[0], hits=hits, functions=functions))
assert records, 'No actual SwiftAgent source coverage record'
hits = {}
functions = []
for record in records:
    for number, count in record['hits'].items(): hits[number] = max(hits.get(number, 0), count)
    functions.extend(record['functions'])
diff = subprocess.check_output(['git','diff','--unified=0',base,'HEAD','--',target],cwd=s,text=True)
added = set(); line = None
for row in diff.splitlines():
    match = re.match(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@', row)
    if match: line = int(match.group(1)); continue
    if row.startswith(('+++','---')) or line is None: continue
    if row.startswith('+'): added.add(line); line += 1
    elif not row.startswith(('-', '\\')): line += 1
executable = sorted(added & hits.keys())
covered = [number for number in executable if hits[number] > 0]
uncovered = [number for number in executable if hits[number] == 0]
assert executable and covered
executed_response_functions = [function for function in functions if function['count'] > 0 and 'embed' in function['name']]
assert executed_response_functions, 'Embedding boundary did not execute in main safe tests'
report = dict(status='passed', source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=s,text=True).strip(), base=base, path=target,
    coverage_sha256=hashlib.sha256(coverage.read_bytes()).hexdigest(), source_sha256=hashlib.sha256((s/target).read_bytes()).hexdigest(), controller_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    matched_records=len(records), added_executable_lines=len(executable), covered_added_executable_lines=len(covered), uncovered_added_executable_lines=uncovered,
    measured_added_line_percent=100*len(covered)/len(executable), executed_embedding_functions=len(executed_response_functions), added_line_hits={number:hits[number] for number in executable},
    scope='Actual supplemental multi-object export of local main safe-test LCOV on LocalEmbeddingEngine added executable lines only; not a Codecov service result, branch coverage guarantee or workflow repair.')
(r/'nlp-coverage.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({key:value for key,value in report.items() if key!='added_line_hits'},indent=2))
