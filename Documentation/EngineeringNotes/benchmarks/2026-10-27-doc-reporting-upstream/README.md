# Independent documentation reporting correction

Frozen candidate `84aa7c59e80d8282c7daf0ce8e9dfc4871308b60` is directly on upstream `e19db7dda4567c425b7eb002da82e234e6c7980f`. Its three files match the existing correction `c4de6cc866fff6f52100535dbcb38dd708558200` byte for byte. It is independent of PR #89, PR #90 and PR #91. All Swift library/test files, package pins, numerical policies and Codecov settings are unchanged from upstream.

## What the checker actually proves

On this upstream source, the old checker reported 98.66% from 2,431 documented declarations out of 2,464 matches. It then printed an unconditional 100% DocC coverage success message because it found no Xcode placeholders. Finding no placeholders does not establish that every API has documentation. Four of the five reporting regressions fail on that actual baseline; the existing placeholder-failure regression already passes.

The correction prints the actual matched-declaration ratio, labels its existing heuristic, and reports N/A when no declarations match. The success line now says only that unresolved placeholders were not found. It does not introduce a coverage threshold. Missing comments remain reporting-only; unresolved Xcode placeholders still exit 1. Declaration/comment matching and placeholder scanning are unchanged. The five standard-library tests cover documented, undocumented, mixed, no-matching-declaration and placeholder cases. All five pass with the correction on pinned Python 3.13 and installed system Python 3.9.6. Both runtimes produce identical real-source scan output.

The workflow executes these regressions before running the checker and replaces its misleading 100% step label. Real DocC generation remains a separate existing step. The scanner is not a Swift parser or DocC symbol-graph calculation. The displayed ratio is not executable-code/Codecov coverage, a claim that every public API was counted, or a measure of documentation quality.

## Qualification

`qualification.json` reports passed after `verify-qualification.py` checked original artifacts and frozen source. Native Debug and Release each pass 1,656 definitions with no failures or skips. The actual main workflow passes nine steps, including all five reporting regressions and the exact corrected scan output. All 19 benchmark steps and three Swift 6.3.3 compatibility steps pass. Python CodeQL reports zero findings. Matching-compiler Swift CodeQL completes with one unchanged PostgreSQL MD5 finding. All 348 extracted repository Swift files are verified against archived/current bytes: 288 library files, 59 benchmark files and Package.swift. Worker binary and all 502 source hashes match. Earlier results remain historical rather than being relabeled as fresh qualification.

Keep Xcode 27 selected. Installed Swift 6.3.3 with SDK 26.5 is used per command for compatibility and matching CodeQL extraction. Native checks execute with Metal/ONNX/tokenizer prerequisites. Hosted safe tests and Codecov retain their SwiftML exclusions; this reporting correction does not alter those policies. No numerical or performance improvement is claimed.

The benchmark policy retains four strict Python Wampler comparator failures and unchanged tolerances. Swift security analysis retains the existing unsuppressed PostgreSQL MD5 finding rather than suppressing it. Completed analyses and passing regression policy are separate from clean numerical/security results. Runtime qualification is on one Apple silicon host, not every supported OS.

## Cache preparation and replay

`prepare-ci-caches.py` copies isolated APFS cache state. Compatibility and CodeQL receive only dependency checkout/repository/artifact/workspace state; generated Clang module caches are rebuilt at their actual destination. This structurally avoids the relocated-module failure preserved in the prior Core ML unit. The traced CodeQL build owns its own copied dependency state. `cache-preparation.json` and `controller-derivation.json` record exact paths and controller hashes. Copied native state can emit stale-path warnings, and dependency/documentation warnings remain in logs. No warning-free build claim is made.

The local workflow controllers execute actual run steps and additionally validate nonempty SwiftDataFrame LCOV records. Local replay excludes service uploads, deployment and GitHub-hosted operating systems. Retained controllers, source hashes, commands, exit codes, original logs and actual native result bundles establish their own outcomes. Raw transcript, build caches, native bundles and full CodeQL database remain local.

The initial evidence verifier incorrectly expected all 348 extracted files to be under Sources. It failed after finding 288 library files; the other 60 files were benchmarks and the package manifest. The original verifier and failure record remain in `verify-qualification-before-extraction-fix.py` and `qualification-verifier-failure.json`. The correction keeps the exact total of 348 and verifies every extracted file, including benchmarks and the manifest. It does not reduce an extraction requirement or change the tested source.

## Independent reviews

### Standards

No findings. The change stays within the existing checker/workflow and uses standard-library tests. [Full report](standards-review.md).

### Spec

No findings. Matching behavior, exit statuses, placeholder enforcement and reporting-only policy remain unchanged. [Full report](spec-review.md). Findings are zero on each axis.

## Published integrity record

Publication is separate from qualification. Compressed logs and comparison archives retain original-to-published hashes. Machine hostname and native hardware identifier are redacted; authorized filesystem paths remain. Run `python3 verify-publication.py --records PATH` to verify a downloaded package. This checks retained-byte integrity, not a fresh numerical run. The independent substantive and publication audits bind their reviewed snapshots; later PR/tracker observations remain outside the frozen qualification manifest.
