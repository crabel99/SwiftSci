# Complete multi-binary safe-test coverage export

The original workflow passed all XCTest binaries positionally to llvm-cov. Only the first was treated as an object; the remainder were source filters. The workflow then masked the exporter status with `|| true`. Actual retained package artifacts reproduce an LCOV file missing SwiftAgent in the workflow's original filesystem enumeration. Sorting Agent first happens to include its transitive modules, so a sorted historical control does not reproduce that particular omission. It does not establish complete coverage from every object.

Source `08486058190836df0a3b1916aa2cb633450a35fc` is one focused three-file commit on upstream `200d3935cc43396658a315bf4d5f745b6c7b496c`. The base already contains classification #93, agent #95, dependency #94 and stable embeddings #96. The workflow delegates to one Python helper that passes every discovered object explicitly and preserves paths with spaces. Missing profiles, absent/malformed bundles, LLVM failures and missing executed DataFrame/Agent/NLP records fail before LCOV reaches stdout. LLVM diagnostics remain on stderr. The existing Codecov upload-service policy stays unchanged.

Library and Swift test bytes, package/dependency pins, safe-test skips, benchmark policy, numerical tolerances and Codecov thresholds/exclusions are unchanged.

## Regression evidence

Eight actual-workflow controls compile and run real Apple LLVM instrumented fixtures. All eight fail against the untouched upstream export command, then pass with the correction. The five existing documentation checks pass too, including under installed Python 3.9. The fixtures cover multiple bundles, spaces, missing inputs/binaries, LLVM diagnostic/status propagation, missing required modules and unexecuted required modules.

The first fixture attempt used identical main profile symbols across binaries and mismatched absolute/relative diagnostic path spelling. Those fixture errors and their first failing-after log remain retained. Corrected fixtures use distinct source functions with separate runners. Final-fixture red evidence uses those exact final test bytes against the old workflow.

A preliminary historical build-directory lookup stalled and was deliberately stopped. Known artifact paths then reproduced the actual original-order omission. An initial copied benchmark controller still named the prior task cache. Its process group was stopped after contracts/install completed and during the optional-engine check, before the worker/cache build. It was restarted with isolated current-task cache paths. The historical folder name containing stopped-before-first-step predates that observed stop checkpoint; the retained receipt and controller-correction.json show the actual completed first step.

## Final qualification

The final source-bound verifier ran directly with exit zero. Native Debug and Release each pass 1,713 definitions with zero failures/skips, including all 62 Agent and 161 NLP definitions. Actual native result bundles and exported trees agree. All eight main workflow steps and the extra coverage guard pass. The actual final-head safe-test export uses all fifteen XCTest objects and contains 8 Agent, 50 DataFrame and 45 NLP source records with positive executed-line evidence in every required module. No supplemental export substitutes for the workflow result.

All 19 benchmark checks pass under unchanged policy: 404 engine cases, 400 strict passes and four known strict pandas Wampler failures. The current worker binary and all 506 recorded source hashes match. Installed Swift 6.3.3 with SDK 26.5 passes Debug/Release builds, all-test compilation and safe tests while Xcode 27 remains selected. Python CodeQL has zero findings. Matching Swift 6.3.3/extractor analysis verifies all 350 repository files against its actual source archive, with zero unresolved AST nodes and one unchanged unsuppressed MD5 finding at DatabaseConnection.swift606.

Independent controller review caught an overly broad historical minimum native-test count. It was tightened to exactly1,713 before the first final verification. All six local jobs completed and their outputs were drained before publication. These receipts qualify the frozen final source on one Apple silicon host, not all older operating systems or hardware.

## Records and limits

FILES.sha256 and verify-publication.py bind every retained file, decoded gzip and benchmark archive member. Original/published mappings record hostname/native-device redactions; authorized filesystem paths remain. Raw transcript/account telemetry/process inventory, build caches, executable binaries, native result bundles and full security databases are excluded. Parsed native trees, logs, source/worker fingerprints, SARIF and extraction checks remain included. The source-bound verifier reads the actual native bundles and source archive locally; the standalone publication verifier checks retained bytes rather than rerunning the native tests.

Local workflow qualification is separate from hosted checks and Codecov service acceptance. Required executed module records are a guard against omitted reports, not a line or branch coverage guarantee. Four known pandas Wampler strict failures, one unchanged unsuppressed PostgreSQL MD5 finding and concurrent MLX cold-start limitation remain open. Applications using stored vectors from the older randomized local embedding implementation must still regenerate their vectors/indexes.

Next feature work is the upstream complete numerical workflow example using the now-merged prepared classifier API. No upstream merge, comment, review request or automation restart is part of this unit.
