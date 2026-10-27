# Qualification controller audit

The proposed documentation-only amend is reasonable. `verify-qualification.py:29` requires the complete execution-to-final file diff to contain only the example README, and `recorded_match` compares recorded hashes with the original execution commit. The verifier also protects library sources, tests, package pins, workflows, benchmark policy and Codecov configuration. A commit-subject correction changes metadata. Neither change requires repeating the full scientific test matrix when these guards pass. Keep the original CI commit visible and describe the final example runs separately.

This review covers controller logic before completion, not successful execution. The draft evidence README correctly blocks publication with a pending-verifier notice. The three new malformed-column cases test real rejection and a specific diagnostic; they support documenting the CSV inference limit. They do not establish support for arbitrary missing-column inputs.

## Attention

reviewed by gpt-6-astra

- Validate the retained execution identity files. The verifier hardcodes the original SHA at line 11 but never reads `execution-head.txt`, `execution-reconciliation.json` or `execution.patch`, although the publication packager includes them. Compare their identities and hashes with the original Git objects and original base-to-execution diff. Otherwise publication can carry stale identity artifacts while qualification passes.

- Bind each example configuration to its build. The loop at `verify-qualification.py:157` checks source and binary hashes, but accepts whatever binary path each receipt names. It does not enforce that `native-debug`, `native-release`, `swift633-debug`, `swift633-release` and `documented-release` identify the corresponding build outputs. A repeated invocation of one binary could satisfy all five labels. Require the expected resolved paths and match configuration/compiler evidence, including the documented run's binary hash. The empty-column receipt's `binary_sha256` also needs comparison with one of those qualified binaries; lines 176 onward currently omit that comparison.

- Bind coverage to the precise recorded executions. `export-example-coverage.py:11` merges every raw profile in the native-debug directory without comparing that set to the controls receipt's `profile_files`. The final verifier validates each control profile and the merged profile independently, but never joins those identities. Require exact profile-set/hash equality. Recompute the single-source LCOV record's `LF`, `LH` and resulting percentage when verifying the final coverage receipt, rather than checking only positive, ordered counts at line 191. This makes the reported coverage traceable to the retained 23 controls.

- Label extraction identity explicitly. `verify-qualification.py:145` writes `security-extraction.json` with `source=head`, although CodeQL executed on the earlier commit. The byte comparison establishes applicability to final source, and `qualification.json` discloses the relationship, but this smaller artifact is ambiguous when read alone. Include both execution and verified-final source identities.

These are verification and reporting gaps, not findings that the planned receipts are wrong. Preserve this preliminary audit and resolve its items in the final audit after the actual verifier and frozen package checks finish.

## Controller follow-up

Re-inspection of the revised verifier resolves the first three items at the code level. It now validates the three original execution artifacts against Git and checks the clarification receipt. It maps each configuration to its expected resolved binary path and binds the empty-column controls to the native Debug binary. It also requires the coverage raw-profile set and hashes to equal the native Debug control receipt, and recomputes the LCOV line counts and percentage. Existing native and compatibility build controllers establish the configuration-specific output paths. Supplemental Agent coverage now checks all 15 binary identities, the merged profile, main CI receipt and export log.

The extraction identity label remains open at this checkpoint. No completed-run or publication claim follows from this static follow-up.
