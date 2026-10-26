from pathlib import Path
import argparse, collections, hashlib, json, subprocess, xml.etree.ElementTree as E

p = argparse.ArgumentParser()
p.add_argument('--folder', type=Path, required=True)
a = p.parse_args()
folder = a.folder.resolve()
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

def rows(path):
    identifiers = {}
    columns = []
    for _, element in E.iterparse(path, events=['end']):
        if element.tag == 'schema':
            columns = [column.findtext('mnemonic') for column in element.findall('col')]
        if 'id' in element.attrib:
            identifiers[element.attrib['id']] = (element.text or element.get('fmt'), element.get('fmt'))
        if element.tag == 'row':
            cells = [identifiers[child.attrib['ref']] if 'ref' in child.attrib else
                     (child.text or child.get('fmt'), child.get('fmt')) for child in element]
            assert len(columns) == len(cells)
            yield dict(zip(columns, cells))
            element.clear()

recordings = json.loads((folder / 'recordings.json').read_text())
assert len(recordings) == 8
summary = []
for recording in recordings:
    name = recording['name']
    toc = folder / (name + '.toc.xml')
    assert sha(toc) == recording['toc_sha256']
    data = E.parse(toc)
    target = data.find('./run/info/target/process')
    assert target.get('name') == 'ProfileWorker' and target.get('return-exit-status') == '0'
    pid = int(target.get('pid'))
    table = data.find("./run/data/table[@schema='coreml-os-signpost']")
    assert table is not None and table.get('target-pid') == 'SINGLE'
    exports = {}
    for key, schema in [('coreml', 'coreml-os-signpost'), ('intervals', 'OSSignpostIntervals'), ('ane', 'ane-hw-intervals')]:
        path = folder / (name + '.' + key + '.xml')
        assert not path.exists(), 'Choose fresh exports; do not overwrite inspected evidence'
        subprocess.run(['xcrun', 'xctrace', 'export', '--input', str(folder / (name + '.trace')),
            '--xpath', f'/trace-toc/run[@number="1"]/data/table[@schema="{schema}"]',
            '--output', str(path)], check=True, timeout=120)
        exports[key] = path
    intervals = [row for row in rows(exports['intervals']) if row['name'][0] == 'CoreML measurement'
                 and f'({pid})' in row['process'][1]]
    assert len(intervals) == 1 and intervals[0]['subsystem'][0] == 'org.swiftsci.benchmarks'
    start = int(intervals[0]['start'][0])
    end = start + int(intervals[0]['duration'][0])
    events = collections.Counter()
    dispatches = collections.Counter()
    positive = collections.Counter()
    models = collections.Counter()
    examples = []
    for row in rows(exports['coreml']):
        time, duration = int(row['start'][0]), int(row['duration'][0])
        if start <= time and time + duration <= end:
            label = row['event-label'][0]
            events[label] += 1
            if row['event-type'][0] == 'model-dispatch-event':
                dispatches[label] += 1
                models[row['model-name'][0]] += 1
                if duration > 0:
                    positive[label] += 1
                    if len(examples) < 10:
                        examples.append(dict(start_ns=time, duration_ns=duration, device=label,
                            model=row['model-name'][0]))
    record_path = folder / (name + '.json')
    assert sha(record_path) == recording['result_sha256']
    record = json.loads(record_path.read_text())
    expected = sum(caller['latency']['count'] for caller in record['callers'])
    assert expected == recording['completed_requests'] == events['Prediction']
    assert sum(positive.values()) > 0, 'No positive device dispatch evidence'
    hardware_rows = sum(1 for _ in rows(exports['ane']))
    item = dict(name=name, target_pid=pid, model_sha256=record['modelSHA256'],
        measurement_start_ns=start, measurement_end_ns=end, completed_requests=expected,
        event_counts=dict(events), dispatch_counts=dict(dispatches), positive_dispatch_counts=dict(positive),
        models=dict(models), examples=examples, global_ane_hardware_rows=hardware_rows,
        event_exports={key:dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size) for key, path in exports.items()},
        toc_sha256=sha(toc), record_sha256=sha(record_path),
        attribution='Positive target-process Core ML model-dispatch events inside the owned measurement interval. Global ANE hardware rows are corroborating observations only and are not attributed to this model by row count. Instrumented timings are excluded from performance comparisons.')
    summary.append(item)
    (folder / 'inspected-events.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(name, expected, dict(positive), 'global ANE rows', hardware_rows, flush=True)
assert len(summary) == len(recordings)
(folder / 'inspection-completed.json').write_text(json.dumps(dict(cases=len(summary),
    inspector_sha256=sha(Path(__file__).resolve()), recordings_sha256=sha(folder / 'recordings.json'),
    inspected_events_sha256=sha(folder / 'inspected-events.json')), indent=2) + '\n')
