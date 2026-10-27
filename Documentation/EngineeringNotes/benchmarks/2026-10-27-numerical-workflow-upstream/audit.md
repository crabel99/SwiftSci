# Final evidence audit

Reviewed the current-turn trail, completed qualification receipts and their source bindings for final commit `4731043d964244051c398475966f2e36967a8d13`. Git confirms that only the example README differs from CI execution commit `c676a0acfca0274fe05e2dc72bf7a0b45ab9f5c9`. The source checkout is clean. The completed `qualification.json` reports passed and matches the current verifier hash.

The native receipts report 1,713 passing definitions per configuration, with no failures or skips. Main workflow receipts retain eight passing steps and the failing extra Agent coverage guard. Benchmark, compatibility-build and security receipts match the stated outcomes. The documented Xcode command and both native configurations pass; each native configuration has 23 controls. Current binary and control-log hashes reconcile. The selected example coverage record reports 153 of 156 executable lines.

The trail records the material corrections: CSV inference restrictions, the switch to the supported Xcode command after fresh SwiftPM runtime failures, two unsuccessful coverage filters, and rerunning Release controls after the documented build relinked its binary. Earlier attempts remain separate. The final verifier checks original execution identity artifacts, configuration-specific binaries, profile identities and the final source mapping. `security-extraction.json` now names both execution and final source identities, resolving the controller audit's remaining disclosure item.

## Attention

reviewed by gpt-6-astra

- Correct one stale qualification limit before publication. `qualification.json` still says Swift 6.3.3 runs "safe suites and the actual example". Its Debug and Release example attempts instead failed to load MLX's Metal resource. The README and retained runtime-limit report describe this correctly. The supported numerical execution is the Xcode build; compatibility evidence covers builds, all-test compilation and safe suites.

- Preserve the disclosed limits in delivery. The inherited Agent coverage-export issue remains separate in PR #97; local supplemental coverage does not repair hosted CI. Four known strict pandas failures and one unchanged unsuppressed MD5 finding remain. The toy fixture establishes workflow behavior, not statistical model quality.

- The user asked to stop the CI tangent. The trail acknowledges that verification expanded too far. Close this example and return to the requested functionality; these known limits do not call for another workstream here.

Frozen publication integrity and privacy review will follow on the existing package. No new source correctness issue was found in this evidence review.

## Scope correction verified

The sole factual flag above is resolved. The current `qualification.json` reports passed for `4731043d964244051c398475966f2e36967a8d13`, matches the current verifier hash, and explicitly distinguishes passing Swift 6.3.3 builds and safe tests from its failed plain SwiftPM example runtimes. It identifies Xcode as the qualified numerical runtime. The earlier wording and receipt remain retained separately. The disclosed coverage, benchmark and security limits still apply; no further CI work is requested by this audit.
