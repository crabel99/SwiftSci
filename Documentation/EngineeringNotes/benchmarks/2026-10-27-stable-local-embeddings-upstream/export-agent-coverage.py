from pathlib import Path
import hashlib,json,subprocess,time
r=Path(__file__).resolve().parent;s=r/'source';o=r/'coverage-supplement';o.mkdir(exist_ok=True)
build=Path(subprocess.check_output(['swift','build','--show-bin-path','-c','debug'],cwd=s,text=True).strip())
bins=sorted(p/'Contents/MacOS'/p.stem for p in build.glob('*.xctest'))
assert len(bins)>1 and all(p.is_file() for p in bins)
profile=s/'.build/debug/codecov/default.profdata'; assert profile.is_file()
command=['xcrun','llvm-cov','export','-format=lcov','-instr-profile='+str(profile),str(bins[0])]
for binary in bins[1:]:command+=['-object',str(binary)]
with (o/'coverage.lcov').open('w') as output,(o/'export.log').open('w') as log:
 result=subprocess.run(command,cwd=s,stdout=output,stderr=log)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=dict(exit_code=result.returncode,command=command,source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=s,text=True).strip(),controller_sha256=sha(Path(__file__)),llvm_cov_version=subprocess.check_output(['xcrun','llvm-cov','--version'],text=True).strip(),main_receipt_sha256=sha(r/'ci-main/main-result.json'),safe_test_log_sha256=sha(r/'ci-main/main-03-run-safe-unit-tests.log'),production_patch_sha256=sha(r/'production.patch'),profile_sha256=sha(profile),objects={str(p):sha(p) for p in bins},coverage_sha256=sha(o/'coverage.lcov'),log_sha256=sha(o/'export.log'),reason='Supplement the unchanged CI positional export with explicit -object arguments for every test binary. The original failed extra guard and workflow export remain retained.')
(o/'result.json').write_text(json.dumps(receipt,indent=2)+'\n');assert result.returncode==0
text=(o/'coverage.lcov').read_text();assert 'Sources/SwiftAgent/ReActAgent.swift' in text
print(json.dumps(receipt,indent=2))
