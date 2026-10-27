# Independent Core ML export audit

reviewed by gpt-6-astra

No source or qualification blocker found for `bdf2b57a66330c331bb870a4d762bb94f7dae0a9`. All required local checks are now complete. This audit reads retained evidence and actual result bundles; I did not change source, build, run numerical tests, publish, or create a PR. The assembled publication package remains a separate gate.

Reviewed qualification SHA-256: `1e8dcd401caed890b2b14007fd9adebcb1a574b65973cc8132c0a3dd521821e2`. Canonical decision snapshot: `fad1836cb131e61a5c635754c08eaec1798c4c1bdfef2431711f9b711108067f`. The 541-line current-turn transcript has SHA-256 `737c5604b19bbcb81a6f8c5ce1fa5162d9c5b47ce4b6becde09101a29dbc1066` and contains no malformed records.

## Source and numerical evidence

The clean candidate has upstream `e19db7dda4567c425b7eb002da82e234e6c7980f` as its direct parent. Its complete diff matches `production.patch` and changes exactly three serialization files and one test file. All four match prior correction `a1e234d25677d91ce5914062603c41233fe13c09` byte for byte. That identity establishes reuse of the implementation, not reuse of its qualification.

I independently checked Apple's [Core ML format reference](https://apple.github.io/coremltools/mlmodel/Format/NeuralNetwork.html#softmaxndlayerparams). SoftmaxND is layer field 950, its axis is int64 field 1, and it normalizes along the selected dimension. The source retains specification version 4 and exact-array mapping. Encoding signed -1 through its two's-complement UInt64 representation is appropriate for the existing protobuf varint writer. The output's last dimension is its class dimension. Existing sigmoid, relu, tanh, and fallback activation field encodings are unchanged; public defaults and signatures remain unchanged.

The actual baseline xcresult contains two failures after a successful build, with zero skips. Both failures are Core ML's `Nonlinearity type INVALID` compilation error. Red source fingerprints match upstream production plus the unchanged new regression suite, and the bound receipt/log hashes match. The actual corrected focused xcresult passes both definitions. Final native Debug and Release xcresult summaries each independently report 1,658 passed, zero failed, and zero skipped tests. Their saved summaries and final source fingerprints agree with actual files.

The supplied-weight regression computes an independent stable softmax from known logits. It checks every probability, normalization, finite/range constraints, selected and repeated row identities, packing/copy accounting, and reservation release across both batch sizes. The public fitted-model regression exercises actual fitting, export, compilation, and prepared prediction against native probabilities. The tested extreme finite logits and unchanged 1e-6 bound support these fixtures. They do not establish general model quality, performance, or Neural Engine execution.

## Final checks and cache recovery

Main passes all eight steps and benchmarks pass all 19, including public worker challenges and three MLX CPU profiles. All inspected workflow/controller hashes, source fingerprints, and hashed step logs match. The acceptance report has 404 executions, 400 strict passes, and four retained pandas Wampler failures; its hash matches the regression-policy receipt. The actual benchmark executable matches its recorded binary hash, and all 502 worker-source hashes match the final source.

The first Swift 6.3.3 compatibility build failed because copied precompiled Clang modules retained their old absolute ModuleCache path. The original failure receipt and log remain in `compatibility-cache-path-failure`, and the old generated scratch remains in `swift633-relocated`. `cache-recovery.json` binds the original receipt hash. The transcript shows a fresh scratch directory received only dependency checkout/repository/artifact and workspace state. Recovery completed at 13:47:40 UTC, before the new build log was created at 13:47:44. No source/compiler change or hidden successful reinterpretation of the failed run occurred.

The complete compatibility rerun passes Debug build, safe tests with all-test compilation, the two focused Core ML runtime tests, and Release build. The focused log identifies Testing Library 6.3.3 and both test names, and reports two tests passed. This is actual older-compiler runtime execution, not just compilation.

Python SARIF reports zero findings and successful execution. Swift database creation and analysis both complete successfully with the matching Swift 6.3.3 compiler/extractor and unchanged selected Xcode. Its controller and logs match their receipt hashes. Among 348 successfully extracted files, all three changed serialization files are present. Their archived bytes and the flagged database file match final source. One unsuppressed `swift/weak-password-hashing` result remains at unchanged DatabaseConnection.swift line 606.

The 14:06:16 final qualification checkpoint truthfully supersedes earlier pending rows. The cache failure and recovery remain explicit. Current README and draft PR validation claims agree with the completed receipts. The PR records-link placeholder remains an intentional prepublication dependency.

## Attention

reviewed by gpt-6-astra

No new source or qualification flags. Preserve these limits:

- Hosted safe tests skip SwiftMLTests and Codecov excludes SwiftML source. Native tests supply the actual export/inference proof. The unchanged documentation checker still prints an inaccurate 100% claim; this delivery does not certify documentation coverage.
- Four strict comparator failures and one pre-existing MD5 security finding remain. A passing policy or completed analysis is not a clean result.
- Native execution covers the current Apple silicon host. Older-compiler execution does not by itself establish behavior on every older macOS runtime. No acceleration, throughput, or general predictive-quality claim is supported.
- Before publication, verify the assembled package bytes, archive members, compression/redaction mappings, and private-data scan. Replace and verify the PR records link after publishing the reviewed records. This audit does not claim those future delivery actions are complete.
