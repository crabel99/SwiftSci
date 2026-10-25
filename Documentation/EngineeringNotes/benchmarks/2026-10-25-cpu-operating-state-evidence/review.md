# Q4 counter-evidence review

## Verdict

The counter math and audit boundary are sound. For each queue, total-minus-P counters define E work; class CPU time includes user and kernel time; process values are summed before rate division. Workers and controller remain separate, and zero worker P-user time is still enforced by the existing receipt audit. Primary and twin medians remain separate, ratios are twin divided by primary, and zero denominators stay unavailable.

The analyzer preserves the original decision exactly. The retrospective replay retains all 24 queues, eight CPU/elapsed failures, `controls_passed: false`, and `performance_qualified: false`. It adds no threshold, normalization, exclusion, hardware-frequency claim, energy claim, or library ranking. Reusing `compare.audit` through a temporary overlay writes only temporary audit outputs; the integrity check confirms the historical capture bytes were unchanged.

The new `--collect` path is an appropriate frozen protocol for the next full comparison. It creates a method manifest before launch, records the exact child command and method sources, fixes the observer profile and existing limits, and verifies the manifest against the resulting plan before producing diagnostics. The resource overview now pairs both variants’ throughput, charged CPU per job, wall time, sampled peak RSS, and resident byte-seconds with the counter evidence.

## Material findings

1. **Refresh every receipt after the final commit and live smoke.** The current replay report predates the resource overview, `tests-after.log` records five tests rather than the current six, `all-controller-tests.log` records the earlier 274-test suite, and `integrity-verification.json` hashes the prior analyzer. These files do not yet validate the reviewed 228-line source or the unexercised collection path.

2. **Explain large worker-P ratios.** Strict placement permits kernel P-core work, so worker-P counts do not mean application code ran on P cores. Several ratios divide tiny counts—Polars reports about 39.4× instructions against roughly 14,000 primary P instructions versus 5.3 billion E instructions. State that worker-P rows are kernel work and near-zero denominators make their ratios unstable.

3. **Keep retrospective and predeclared provenance distinct.** The documentation now correctly says retrospective hashes bind current files rather than proving a historical baseline. Preserve that wording and record `method_predeclared: true` only for wrapper-launched panels.

No transcript directory was available, and no transcript audit is claimed.
