from pathlib import Path
import json, subprocess, time
r = Path(__file__).resolve().parent
prior = Path('/private/tmp/swiftsci-upstream-agent-contract-20261027')
copied = []
def clone(source, destination):
    assert source.exists() and not destination.exists(), (source, destination)
    subprocess.run(['cp', '-cR', str(source), str(destination)], check=True)
    copied.append(dict(source=str(source), destination=str(destination)))
for source, destination in [(prior/'source/.build', r/'source/.build'), (prior/'derived', r/'derived'), (prior/'native-packages', r/'native-packages'), (prior/'ci-bench-cache', r/'ci-bench-cache')]:
    clone(source, destination)
# Generated Clang module caches embed absolute paths. Copy dependency state only.
for source, destination in [(prior/'swift633', r/'swift633'), (prior/'ci-security-swift633/build', r/'codeql-dependencies')]:
    destination.mkdir(exist_ok=False)
    for name in ['checkouts', 'repositories', 'artifacts', 'workspace-state.json']:
        if (source/name).exists():
            clone(source/name, destination/name)
    assert not any(destination.rglob('ModuleCache'))
(r/'cache-preparation.json').write_text(json.dumps(dict(status='passed', completed_unix=time.time(), copies=copied, compatibility_policy='Dependency state only; generated compiler state is rebuilt at its real destination'), indent=2)+'\n')
print('Prepared isolated CI caches without relocated compatibility compiler modules', flush=True)
