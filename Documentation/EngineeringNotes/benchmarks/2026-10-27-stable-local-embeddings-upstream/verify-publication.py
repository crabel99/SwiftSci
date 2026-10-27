from pathlib import Path
import argparse, gzip, hashlib, json, tarfile
p=argparse.ArgumentParser();p.add_argument('--records',type=Path,default=Path(__file__).resolve().parent);a=p.parse_args();r=a.records.resolve()
sha=lambda data:hashlib.sha256(data).hexdigest()
files={}
for line in (r/'FILES.sha256').read_text().splitlines():
    digest,name=line.split('  ',1);path=(r/name).resolve()
    assert path.is_relative_to(r) and sha(path.read_bytes())==digest,name
    files[name]=digest
assert set(files)=={str(p.relative_to(r)) for p in r.rglob('*') if p.is_file() and p.name!='FILES.sha256'}
compression=json.loads((r/'compression-map.json').read_text())
for name,meta in compression.items():
    data=gzip.decompress((r/name).read_bytes());assert sha(data)==meta['published_uncompressed_sha256'] and len(data)==meta['published_uncompressed_size_bytes'],name
for name,meta in json.loads((r/'publication-transforms.json').read_text()).items():
    assert sha((r/name).read_bytes())==meta['published_sha256'],name
members=json.loads((r/'archive-members.json').read_text())
with tarfile.open(r/'ci-comparisons.tar.gz','r:gz') as archive:
    assert set(archive.getnames())==set(members)
    for member in archive:
        assert member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
        data=archive.extractfile(member).read();meta=members[member.name]
        assert sha(data)==meta['published_sha256'] and len(data)==meta['bytes'],member.name
# Every declared failed-attempt payload must remain present after publication transforms.
transforms=json.loads((r/'publication-transforms.json').read_text())
for name,digest in json.loads((r/'setup-failures.json').read_text())['files'].items():
    if name+'.gz' in compression:
        assert compression[name+'.gz']['original_sha256']==digest,name
    else:
        assert name in files and transforms.get(name,{}).get('original_sha256',files.get(name))==digest,name
qualification=json.loads((r/'qualification.json').read_text());assert qualification['status']=='passed'
print(json.dumps(dict(status='passed',manifest_files=len(files),compressed_payloads=len(compression),archive_members=len(members),source=qualification['source']),indent=2))
