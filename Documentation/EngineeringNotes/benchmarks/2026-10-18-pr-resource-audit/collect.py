"""Freeze authored PR metadata and complete first-parent merge changes for review."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--snapshot', type=Path, required=True)
p.add_argument('--repo', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)

def git(*args):
    return subprocess.check_output(['git', *args], cwd=a.repo)

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')

notes_root = a.repo / 'Documentation/EngineeringNotes'
notes = [(str(f.relative_to(a.repo)), f.read_text()) for f in notes_root.rglob('*.md')
         if '2026-10-18-pr-resource-audit' not in str(f)]
inventory = []
for pr in sorted(json.loads(a.snapshot.read_text()), key=lambda pr: pr['number']):
    number = pr['number']
    target = a.output / str(number)
    target.mkdir(exist_ok=True)
    merge = pr['mergeCommit']['oid'] if pr.get('mergeCommit') else None
    if pr['state'] != 'MERGED' or not merge:
        inventory.append(dict(number=number, url=pr['url'], state=pr['state'], review_status='needs_separate_unmerged_comparison'))
        continue
    assert re.fullmatch('[0-9a-f]{40}', merge), merge
    parents = git('show', '-s', '--format=%P', merge).decode().strip().split()
    base = parents[0]
    names = git('diff', '--no-renames', '--name-only', '-z', base, merge).decode().split('\0')[:-1]
    sources = [name for name in names if name.startswith('Sources/') and '.docc/' not in name and not name.endswith('.md')]
    dependency = [name for name in names if name in ['Package.swift', 'Package.resolved']]
    patch = git('diff', '--no-ext-diff', '--no-renames', '--unified=12', base, merge, '--', 'Sources/', 'Package.swift', 'Package.resolved')
    (target / 'production.patch').write_bytes(patch)
    (target / 'pr-body.md').write_text(pr['body'] + '\n')
    note_pattern = re.compile(r'\bPR\s*#?\s*' + str(number) + r'\b', re.I)
    candidates = [path for path, body in notes if pr['url'] in body or note_pattern.search(body)]
    record = dict(number=number, title=pr['title'], url=pr['url'], state=pr['state'], merged_at=pr['mergedAt'],
                  head=pr['headRefOid'], merge=merge, first_parent=base, merge_parent_count=len(parents),
                  abbreviated_api_file_count=len(pr['files']), introduced_file_count=len(names),
                  introduced_source_count=len(sources), source_paths=sources, dependency_paths=dependency,
                  benchmark_paths=[s for s in names if s.startswith('Benchmarks/')],
                  test_paths=[s for s in names if s.startswith('Tests/')],
                  ci_paths=[s for s in names if s.startswith('.github/')], candidate_notes=candidates,
                  production_patch_sha256=hashlib.sha256(patch).hexdigest(), all_introduced_paths=names)
    write_json(target / 'record.json', record)
    inventory.append(record)
write_json(a.output / 'inventory.json', dict(repository='Nodibell/SwiftSci', author='crabel99',
           snapshot_sha256=hashlib.sha256(a.snapshot.read_bytes()).hexdigest(),
           comparison='Each merged commit against its first parent; complete Git paths, not truncated PR file lists.',
           pull_requests=inventory))
lines = ['# Authored PR inventory', '', '| PR | Sources introduced | Dependency | Title |', '| --- | ---: | --- | --- |']
for pr in inventory:
    lines.append(f"| [#{pr['number']}]({pr['url']}) | {pr.get('introduced_source_count', '?')} | {'yes' if pr.get('dependency_paths') else 'no'} | {pr.get('title', pr['state'])} |")
(a.output / 'inventory.md').write_text('\n'.join(lines) + '\n')
print('Collected', len(inventory), 'PRs;', sum(bool(pr.get('introduced_source_count') or pr.get('dependency_paths')) for pr in inventory), 'with runtime or dependency changes')
for pr in inventory:
    print(pr['number'], pr.get('introduced_source_count'), pr.get('introduced_file_count'), pr.get('title'))
