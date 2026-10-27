# Complete numerical workflow example

Source qualification records for the complete numerical workflow example.

The example reads a bundled or user-supplied CSV, selects training and held-out
rows together with their targets, fits mean imputation, scaling and CPU PCA on
training rows, then trains the existing prepared CPU logistic classifier. It
exports held-out labels and class probabilities alongside original data-row
positions, plus a JSON stage report and accuracy.

One executable is registered in the existing package. The existing dependency
graph, library code, Swift tests, benchmark policy, numerical tolerances, safe-test
skips, workflows and Codecov settings remain unchanged. A standard-library Python
checker independently calculates the bundled fixture's preprocessing, closed-form
PCA and scalar logistic updates, then checks both exports at the existing
1e-12 absolute and relative tolerance.

The bundled sample is an integration fixture. Its ordered split and accuracy do
not establish statistical quality, speed, memory bounds or hardware placement.
The command requests CPU execution, while the linked MLX dependency still needs
an accessible Metal environment.

## Review corrections and execution identity

The specification review found that entirely empty feature columns cannot be
inferred as numeric by the CSV reader. The corrected documentation requires a
numeric value in each feature's first 1,000 data rows and explains rejection of
empty columns before imputation. Forcing numeric overrides would silently turn
invalid text into missing values, so the example retains inference and rejects
invalid text. Actual boundary controls cover all-empty columns, a first numeric
cell after the inference sample and invalid text.

The initial commit subject also needed the repository's Conventional Commit
prefix. Local CI records preserve their original execution commit. The final
documentation and subject correction changes only the example README bytes.
The verifier compares every recorded compiled input against the final source;
it does not relabel earlier receipts. The documented Release command and actual
Debug/Release example checks execute again on the final commit. The initial
cached SwiftPM run worked, but the fresh compatibility runtimes exposed the
missing Metal resource. The guide now uses the dependency's supported Xcode
build command. Two local coverage-export attempts also returned more source
records than their positional filters requested. Their raw outputs are retained;
the final exporter selects the example record explicitly from complete LCOV.
The first final receipt check also caught a Release relink after its earlier
execution. Its failure is retained; Release controls were rerun after the
documented build finished, then the stable executable was checked again.

## Qualification scope

Native Debug and Release each pass 1,713 definitions with zero failures or skips.
All eight main workflow run steps pass. All 19 benchmark checks pass under the
unchanged policy, with 404 engine cases, 400 strict passes and four known strict
pandas Wampler failures. Swift 6.3.3 passes Debug and Release builds, all-test
compilation and safe tests. Python CodeQL has zero findings. Matching Swift
analysis verifies 351 extracted repository files against the actual source
archive, with zero unresolved AST nodes and one unchanged unsuppressed MD5 finding.

The final supported Xcode command builds and runs successfully. The independent
checker verifies both exports. Native Debug and Release each pass all 23 controls,
including repeatability, held-out feature and target perturbations, malformed
inputs and altered-output rejection. Three additional controls verify the CSV
inference restriction. Local CLI coverage executes 153 of LLVM's 156 reported
executable lines, 98.08 percent, separately from hosted Codecov.

The original workflow's positional LLVM coverage export is inherited from the
base and remains separate from pending PR #97. Its original export and failing
extra local Agent guard are retained. A supplemental export passes all XCTest
objects explicitly to supply local evidence. It does not repair the hosted
workflow. Native CLI execution coverage is also retained separately and is not
uploaded as a substitute for hosted Codecov acceptance.

Xcode 27 remains selected. Swift 6.3.3 with SDK 26.5 compiles all tests and runs
the inherited safe-suite selection. The plain SwiftPM compatibility runtime attempts fail because their build directories lack
the required MLX Metal resource; those failures are retained. The supported
Xcode numerical example runs on the selected current toolchain.
Matching-compiler Swift CodeQL uses that compatibility compiler and extractor.
Local workflow replay executes applicable run steps and separate security
analyses. Hosted actions, uploads and service acceptance remain separate.

## Retained evidence

`FILES.sha256` and `verify-publication.py` verify every published payload,
decompressed log and benchmark archive member. Original-to-published mappings
record hostname and native-device redactions. Authorized filesystem paths remain.
Raw transcript/account telemetry, process inventories, build caches, binary
executables, native result bundles and full security databases stay local. Parsed
native trees, logs, source and worker fingerprints, SARIF, extracted-source checks,
example inputs/outputs, independent verifier results and review findings remain.

The source-bound verifier uses the real local result bundles, binaries, profiles
and CodeQL source archive. The standalone publication verifier checks retained
bytes; it does not rerun scientific calculations or native tests.

Four known strict pandas Wampler failures and one unchanged unsuppressed legacy
MD5 finding remain in the full-repository checks. No upstream merge, comment, review request or
automation restart is part of this delivery.
