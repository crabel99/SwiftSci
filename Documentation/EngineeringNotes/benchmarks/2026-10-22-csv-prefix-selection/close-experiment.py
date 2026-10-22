from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip();assert head=='167d9a4e6f8cb923342dea3236721c8722015bf3';assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
for label in ['selected-release','selected-debug','selected-asan']:
 d=json.loads((R/(label+'-summary.json')).read_text());assert (d['passedTests'],d['failedTests'],d['skippedTests'])==(394,0,0)
 inputs=json.loads((R/(label+'-command.json')).read_text())['source_sha256'];assert all(hashlib.sha256((S/p).read_bytes()).hexdigest()==h for p,h in inputs.items())
counts={}
for n in ['acceptance','mode-controls','text-controls','long-key-controls','crossover','setup','preflight-screen','steady-boundaries']:
 records=[json.loads(l) for l in (R/n/'workers.jsonl').read_text().splitlines()];assert all(x['validated'] for x in records);counts[n]=len(records)
 assert (R/n/'summary.json').exists() and (R/n/'review-flags.json').exists()
assert sum(counts.values())==12152
assert len(list((R/'standardized').glob('*.response.json')))==190
state=dict(commit=head,branch='codex/csv-prepared-string-membership',parent='c906c3fbbb0baf1357438a7079921a6448e0c9e5',cleanup='f9a99ce54c77909bdd6f95fadd5fa3b5d15490f2',resource_workers=counts,semantic_suites={k:394 for k in ['Release','Debug','AddressSanitizer']},grammar_cases=30720,unicode_cells_per_policy=3336243,standard_responses=190,source_clean=True,promotion_allowed=False,decision='Keep cleanup independently reviewable. Preserve the selected decoder as an experimental local commit. Metadata-preflight remains a snapshot trial. Neither admission policy meets resource acceptance across boundary controls; no tolerances changed and no flags waived. No push or PR.',next_step='Isolate preparation and unchanged fallback-loop costs separately on recurring boundary cases. Do not tune a row cutoff or assume metadata admission resolves the measured CPU differences.')
(R/'decision.json').write_text(json.dumps(state,indent=2)+'\n');(R/'todo.json').write_text(json.dumps(dict(ground='complete',sketch='complete',agree='complete',implement='complete; experimental commit',verify='complete; semantic checks pass, boundary resource acceptance fails',scrap_if_needed='Neither selected policy promoted; preserve trials and all flags'),indent=2)+'\n')
(R/'cleanup.patch').write_bytes(subprocess.check_output(['git','show','--format=fuller','f9a99ce54c'],cwd=S));(R/'selected.patch').write_bytes(subprocess.check_output(['git','show','--format=fuller',head],cwd=S))
(R/'source-state.json').write_text(json.dumps(dict(commit=head,branch=state['branch'],status='clean',diff_stat=subprocess.check_output(['git','diff','--stat',state['parent']+'...HEAD'],cwd=S,text=True)),indent=2)+'\n')
print(json.dumps(counts));print('Experimental candidate retained; promotion blocked by resource evidence.')
