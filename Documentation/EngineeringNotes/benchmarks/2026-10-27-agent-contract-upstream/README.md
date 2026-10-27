# Agent completion reporting and consumer cancellation qualification

Source `3a9482122cd91a3d18467a9d7005416242b1c203` contains two commits on upstream main `01d48cbcd940c886546b2bb8d6b177d9b7a0e277`. All seven changed files reuse the previously reviewed agent implementation byte for byte. This delivery is independent of prepared classification PR93.

A capable native model must finish its response normally with exactly one terminal metadata record reporting `.stop` before the agent can parse an action or answer. Truncated or malformed responses cannot trigger tools or become assistant memory for that response. Accepted trace steps retain producer token counts. Existing text-only models, String closures and the original AgentStep initializer retain their behavior.

Consumer cancellation now cancels the stream producer and checks cancellation around generation, tools and answers. Cancellation remains cooperative. A tool that ignores cancellation cannot be forcibly interrupted, and completed side effects cannot be rolled back. Independent tool CancellationError behavior remains ordinary tool observation behavior.

## Source and regression evidence

`source-reconciliation.json` and three patches bind the exact two commits and seven files. `spec-review.md` and `standards-review.md` report no findings. `verify-qualification.py` re-reads source, result bundles, red failures, workflow logs, coverage, security extraction and benchmark provenance.

Both regressions reproduced after successful builds. The completion reproduction uses current upstream ReActAgent with an explicit additive completion-capability overlay and one regression fixture, so the new mock compiles. It is not a pristine upstream checkout. The old consumer executed the truncated action, producing two issues. The completion-only parent plus final cancellation tests produced 17 issues across seven definitions; the ordinary lifetime and independent-tool-error controls passed. Exact overlays, fixtures and logs are retained under `red-completion` and `red-cancellation`.

## Qualification

Final counts and bindings are in `qualification.json`, generated from the actual artifacts. Native Debug and Release use strict ONNX execution and contain 1,688 definitions each, including 62 agent tests: 20 XCTest and 42 Swift Testing definitions. The 16 new definitions cover the completion and cancellation contracts. Older Swift 6.3.3 compatibility runs Debug/Release builds, safe tests and the complete agent target with SDK 26.5 while Xcode 27 remains selected.

All eight unchanged main workflow run steps passed. The added ninth local guard failed because the original positional llvm-cov export omitted agent coverage. That failed guard and original LCOV are retained. A separate explicit-object export of the same safe-test profile includes every test binary. It measured hits on all 80 added executable ReActAgent lines and executed the rich-response function. This is local line coverage evidence, not a Codecov result, branch coverage guarantee, workflow repair or threshold change. Existing Codecov exclusions remain unchanged. The hosted export needs a separate fix.

The benchmark workflow retains all 19 checks and the existing acceptance policy. The 404 engine cases retain 400 strict passes and four pandas Wampler strict failures; numerical tolerances are unchanged. Python CodeQL has no findings. Swift CodeQL uses the installed Swift 6.3.3 extractor with complete extraction of 350 repository Swift files: 290 Sources, 59 Benchmarks and Package.swift. The unchanged unsuppressed PostgreSQL MD5 finding remains at DatabaseConnection.swift:606. The separately observed concurrent MLX cold-start hazard remains open.

## Published evidence

`FILES.sha256` covers the complete package; `verify-publication.py --records PATH` checks every payload, compressed file and benchmark archive member. `publication-transforms.json` records hostname/device identifier redactions. Authorized filesystem paths are retained. Raw task transcripts, build caches, native result bundles, binaries and CodeQL databases are excluded. Local qualification verifies actual native bundles and all 350 archived CodeQL source files before packaging; their exported trees and receipts are retained here.

This immutable evidence package does not include subsequent PR or tracker observations. Those are separate delivery records. Hosted checks must be read independently of local results.
