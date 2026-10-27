# Independent substantive and trail audit

Reviewed by gpt-6-astra. Completed 2026-10-27T18:39:10.916510+00:00.

No substantive blocker found in the completed local qualification. The exact clean source remains `3012a6e52d70306a9437fb8cd8af4343a41560dd`, one three-file commit directly on `01d48cbcd940c886546b2bb8d6b177d9b7a0e277`. The initial source and regression findings in `audit-initial.md` remain valid. This review inspected actual artifacts without running builds/tests, changing source or making remote writes. Package privacy and delivery are later gates.

## Completed evidence

Both actual native xcresult summaries and full test trees contain 1,673 passing definitions, zero failures and zero skips. Each contains 161 passing NLP definitions, including the new stable-coordinate regression and the local zero-shot integration test. Build/source fingerprints, strict ONNX execution receipts and exported trees agree with the actual bundles.

The final main receipt records eight successful workflow steps and the retained failed ninth local guard. All 19 benchmark steps, four compatibility steps and two Python-security steps have matching controller, workflow, source and log bindings. The Swift 6.3.3 focused NLP log contains 12 passing XCTest methods and 149 Swift Testing definitions across 24 suites. Compatibility includes Debug/Release builds and safe tests on the recorded host with SDK 26.5; Xcode 27 remains selected. It does not establish support on an older operating system or GPU compiler.

The supplemental coverage export binds the same safe-test profile, original main receipt, safe-test log, export controller and all 15 actual test binaries. Independently intersecting the final source diff with the actual LocalEmbeddingEngine LCOV record produces eight added executable lines, all with positive counts. Lines 69–72 have 62 hits each and lines 79–82 have 539 each. The original coverage-export omission remains a separate failed guard. This is local line evidence, not a Codecov result, branch-coverage proof or workflow repair.

Benchmark acceptance retains 404 executions, 400 strict passes and four known pandas Wampler failures. The passing regression policy binds that exact acceptance file and still reports failed strict conformance. I verified the worker binary and all 505 recorded source files against this final head.

Python CodeQL has zero findings. Swift database creation and analysis completed with matching Swift 6.3.3 compiler/extractor and exact source/controller/log/SARIF bindings. Actual successful-extraction notifications list 350 files, comprising 290 Sources, 59 Benchmarks and Package.swift. Every extracted archive file equals the current source bytes, including the changed LocalEmbeddingEngine. Analysis reports zero unresolved AST nodes. The sole finding is the unchanged unsuppressed weak-password-hashing result at DatabaseConnection.swift:606.

The final qualification verifier ran directly at 18:37:02Z and exited zero in the scoped transcript. Its complete log parses to the exact same object as `qualification.json`; the current verifier hash matches the receipt. No failed earlier command or trailing log-read exit status is substituted for this success.

## Regression and scope limits

The hosted PR94 failure remains diagnosed as the unchanged Swift local-embedding path, independently of its two Python requirements edits. Initial review verified the actual 40-process variability, exact food misclassification on the separate attempt 55, and final-head 100-process outputs with one vector and 100 matching ASCII goldens. The precommit fixed-process receipt retains the baseline HEAD label alongside final source-byte hashes; it is not relabeled as a committed-head run.

Actual XCTest red evidence is one new test producing seven assertion failures among five executed tests, followed by all five passing after correction. Literal ASCII/UTF-8 expectations were checked independently of the production hash helper. The fixture adjustment tests explicit label-hypothesis overlap and retains predicted-label and probability-sum assertions. It makes no learned semantic-accuracy claim.

The clean PR94 merge tree preserves both exact dependency-update blobs and candidate Swift/test/workflow bytes. This is source integration evidence, not full runtime qualification of the combined Python dependency tree. Upstream access remains read-only. Publishing this separate correction will not itself repair PR94's branch or rerun its failed hosted check; upstream application and a branch update remain necessary.

## Trail and retained failures

The five append-only decision rows agree with the 590-line scoped current-turn transcript and actual artifacts. The intermediate checkpoint explicitly kept Release/security/benchmark checks pending, and the final checkpoint follows their completion and direct verifier success. Five failed initial full-check attempts remain bound by `setup-failures.json`; their compiler-cache/Xcode/network failures occurred before test execution. Initial probe module-cache and XCTest framework/overlay setup failures are also retained separately from regression failures. Python security completed on its initial launch and was not unnecessarily rerun. No source or tolerance change conceals these setup problems.

The current README and draft PR preserve the distinctions above. `EVIDENCE_LINK` is intentionally still pending the later verified records commit. There is no supported source-publication, PR-creation or new hosted-success claim at this snapshot.

## Attention

Reviewed by gpt-6-astra.

- Applications must regenerate earlier LocalEmbeddingEngine vectors and indexes. Coordinates intentionally change; this remains an untrained overlap-based projection.
- PR94 still needs upstream application of the correction and an updated branch/check run. The clean merge-tree proof does not replace combined dependency runtime qualification.
- The hosted coverage exporter remains unfixed. Four strict comparator failures, the legacy MD5 finding and the separate MLX cold-start hazard remain open.
- Publication privacy/integrity, the pinned evidence link and subsequent remote delivery checks remain outstanding. No new substantive blocker was found.

## Bound snapshot

| Artifact | SHA-256 |
| --- | --- |
| `qualification.json` | `368137a85b2758eb3fc5891f9a8b5842295c2515ee3c1ae9475d63fe6cfb88cd` |
| `verify-qualification.py` | `3c2acb67b5e236a14f5753d2605e7518f738bc3b2943fd05f44c21795dceff2b` |
| `qualification-verifier.log` | `368137a85b2758eb3fc5891f9a8b5842295c2515ee3c1ae9475d63fe6cfb88cd` |
| `decisions.tsv` | `6d68270692cbe9f7d5a370bc5856f2e0707a56ab5ca156ca47f9fc175be0295d` |
| `task-transcript.jsonl` | `2e6ac113d70cd1a028f0272b79c12c7e57aee498a737800e1dce4015d7f57b63` |
| `README.md` | `a0ec3fefc6538577bda5ba8e0a869161386d4c91342ee255ca63408298c6350e` |
| `pr-body.md` | `d33bc9fb9dd341f9f92f66385c38080e59b6436fc62f83e1dcb7af9e35464d5a` |
| `setup-failures.json` | `19e1c688926bd675fc38a543e530fbc82770a51918f57b980bfb27b245f9090b` |
| `fixed-final-processes/result.json` | `e97a75a15f709025e4b068562e87801ae8505932505e12a0a96d4128f723479a` |
| `pr94-integration.json` | `188818ee6c54b041188fbadec372037fe8006717293793b14a47007b3786758c` |
