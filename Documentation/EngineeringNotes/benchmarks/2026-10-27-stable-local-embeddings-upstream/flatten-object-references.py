from pathlib import Path
import hashlib, json
r = Path(__file__).resolve().parent
source_objects = r / 'source/.git/objects'
target = source_objects / 'info/alternates'
original = target.read_bytes()
ordered = []
seen = {source_objects.resolve()}
def visit(store):
    store = store.resolve()
    if store in seen:
        return
    seen.add(store)
    assert store.is_dir(), store
    pointers = store / 'info/alternates'
    if pointers.exists():
        for line in pointers.read_text().splitlines():
            path = Path(line)
            visit(path if path.is_absolute() else store / path)
    ordered.append(store)
for line in original.decode().splitlines():
    path = Path(line)
    visit(path if path.is_absolute() else source_objects / path)
flattened = ''.join(str(store) + '\n' for store in ordered).encode()
target.write_bytes(flattened)
(r / 'object-reference-repair.json').write_text(json.dumps(dict(original=original.decode(), original_sha256=hashlib.sha256(original).hexdigest(), flattened=flattened.decode(), flattened_sha256=hashlib.sha256(flattened).hexdigest(), referenced_stores=len(ordered), reason='Proactively flatten inherited shared-clone references before isolated benchmark clones; no setup failure occurred in this unit'), indent=2) + '\n')
print('Flattened local object references:', len(ordered))
