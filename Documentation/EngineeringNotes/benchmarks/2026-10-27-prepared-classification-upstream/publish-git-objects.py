"""Publish exact local Git objects through authenticated GitHub API, without force."""
from pathlib import Path
import argparse, base64, concurrent.futures, datetime, hashlib, json, re, subprocess
p = argparse.ArgumentParser()
p.add_argument('--checkout', type=Path, required=True)
p.add_argument('--repo', required=True)
p.add_argument('--base', required=True)
p.add_argument('--branch', required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--publish', action='store_true')
a = p.parse_args()
a.output.mkdir(exist_ok=False)
git = lambda *args: subprocess.check_output(['git', *args], cwd=a.checkout)
head = git('rev-parse', 'HEAD').decode().strip()
assert git('status', '--porcelain') == b''
subprocess.run(['git', 'merge-base', '--is-ancestor', a.base, head], cwd=a.checkout, check=True)
objects = git('rev-list', '--objects', '--no-object-names', a.base + '..' + head).decode().splitlines()
types = {oid: git('cat-file', '-t', oid).decode().strip() for oid in objects}
assert all(kind in ['blob', 'tree', 'commit'] for kind in types.values())
prefix = 'repos/' + a.repo + '/git/'
def api(endpoint, body=None, missing=False):
    command = ['gh', 'api', prefix + endpoint]
    if body is not None:
        command += ['--method', 'PATCH' if endpoint.startswith('refs/heads/') else 'POST', '--input', '-']
    result = subprocess.run(command, input=json.dumps(body) if body is not None else None, text=True, capture_output=True)
    if result.returncode:
        if missing and 'HTTP 404' in result.stderr:
            return None
        raise RuntimeError(endpoint + ': ' + result.stderr[:1000])
    return json.loads(result.stdout)
remote = api('ref/heads/' + a.branch, missing=True)
remote_head = remote['object']['sha'] if remote else None
assert remote_head in [None, a.base, head], ('Unexpected destination branch', remote_head)
assert api('commits/' + a.base)['sha'] == a.base
report = dict(repository=a.repo, branch=a.branch, head=head, base=a.base, initial_remote=remote_head, object_counts={kind:sum(value==kind for value in types.values()) for kind in ['blob','tree','commit']}, mode='publish' if a.publish else 'dry-run', uploaded=[], controller_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
def save():
    (a.output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
save()
if not a.publish:
    print(json.dumps(report, indent=2))
    raise SystemExit(0)
done = set()
def upload_blob(oid):
    raw = git('cat-file', 'blob', oid)
    result = api('blobs', dict(content=base64.b64encode(raw).decode(), encoding='base64'))
    assert result['sha'] == oid, ('Blob identity mismatch', oid, result['sha'])
    return dict(sha=oid, type='blob', bytes=len(raw))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(upload_blob, oid):oid for oid, kind in types.items() if kind == 'blob'}
    for future in concurrent.futures.as_completed(futures):
        record = future.result(); done.add(record['sha']); report['uploaded'].append(record); save()
def identity(raw):
    match = re.fullmatch(rb'(.*) <([^>]*)> ([0-9]+) ([+-][0-9]{4})', raw)
    assert match, raw
    name, email, seconds, offset = match.groups()
    zone = offset.decode()
    minutes = (int(zone[1:3]) * 60 + int(zone[3:])) * (1 if zone[0] == '+' else -1)
    date = datetime.datetime.fromtimestamp(int(seconds), datetime.timezone(datetime.timedelta(minutes=minutes)))
    return dict(name=name.decode(), email=email.decode(), date=date.isoformat(timespec='seconds'))
def upload(oid):
    if oid not in types or oid in done:
        return
    kind = types[oid]
    if kind == 'tree':
        entries = []
        for row in git('ls-tree', '-z', oid).split(b'\0'):
            if not row: continue
            meta, path = row.split(b'\t', 1)
            mode, child_kind, child = meta.decode().split()
            upload(child)
            entries.append(dict(path=path.decode(), mode=mode, type=child_kind, sha=child))
        result = api('trees', dict(tree=entries))
    elif kind == 'commit':
        raw = git('cat-file', 'commit', oid)
        headers, message = raw.split(b'\n\n', 1)
        fields = {}
        for row in headers.splitlines():
            name, value = row.split(b' ', 1)
            assert name in [b'tree', b'parent', b'author', b'committer'], ('Unsupported signed/encoded commit header', name)
            fields.setdefault(name, []).append(value)
        tree = fields[b'tree'][0].decode(); parents = [parent.decode() for parent in fields.get(b'parent', [])]
        upload(tree)
        for parent in parents: upload(parent)
        result = api('commits', dict(message=message.decode(), tree=tree, parents=parents, author=identity(fields[b'author'][0]), committer=identity(fields[b'committer'][0])))
    else:
        raise AssertionError(('Unuploaded blob', oid))
    assert result['sha'] == oid, ('Exact Git object identity mismatch; branch was not changed', kind, oid, result['sha'])
    done.add(oid); report['uploaded'].append(dict(sha=oid, type=kind)); save()
upload(head)
assert done == set(types)
current = api('ref/heads/' + a.branch, missing=True)
assert (current['object']['sha'] if current else None) == remote_head, 'Concurrent destination change'
if remote_head is None:
    api('refs', dict(ref='refs/heads/' + a.branch, sha=head))
elif remote_head != head:
    api('refs/heads/' + a.branch, dict(sha=head, force=False))
assert api('ref/heads/' + a.branch)['object']['sha'] == head
assert git('rev-parse', 'HEAD').decode().strip() == head and git('status', '--porcelain') == b''
report.update(status='passed', final_remote=head)
save()
print(json.dumps(dict(status='passed', head=head, objects=len(done), branch=a.branch)))
