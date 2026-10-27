# Stable local embeddings and PR94 safe-test failure

PR94 updates certifi, filelock and setuptools in two Python requirements files. Its safe Swift tests failed at ZeroShotTextClassifierTests.testZeroShotWithLocalEmbeddingEngine: food was returned where technology was expected. All other substantive hosted checks passed. The changed Python requirements are not used by that Swift job, and PR94's NLP source/test bytes equal upstream main.

The underlying LocalEmbeddingEngine used Swift String.hashValue for word and character n-gram projection. That hash is randomized between processes despite the engine's documented deterministic behavior. Forty fresh processes produced 40 distinct vectors for identical text. An additional bounded run reproduced the exact food misclassification on process 55. Existing same-process equality tests could not detect this.

Source 3012a6e52d70306a9437fb8cd8af4343a41560dd replaces those randomized hashes with the existing shared fnv1aTokenHash, computes each once, and uses unsigned magnitude for bucket selection. Dimensions, tokenization, n-gram traversal, weights, normalization, batch APIs and public signatures stay unchanged. This deliberately changes coordinates: users must regenerate stored vectors and indexes from the earlier implementation.

The engine is a hash projection with no trained semantic model. The local classifier integration test now uses input identical to its technology label hypothesis, checking supported literal overlap while retaining its predicted-label and probability-sum assertions. The original unrelated-words fixture remains in the process probe as observed historical failure input; it is not promoted into a semantic quality guarantee.

## Regression evidence

The actual five-test XCTest source builds and runs against old production code: the new independent ASCII/UTF8 golden coordinate test fails with seven assertions, while its four neighbors pass. The same five tests pass after correction. Actual compiler commands, source/test hashes and logs are retained. Initial standalone setup attempts failed for an inaccessible compiler cache and missing XCTest framework/Swift overlay arguments; those attempts are preserved separately and are not counted as regression failures.

The final committed head is exercised by 100 fresh probe processes with one identical vector, 100 matching ASCII golden results and 100 technology predictions for the original text. The probe compiles actual production engine/classifier/provider/error source plus the existing FNV helper extracted verbatim from Tokenizer.swift to avoid unrelated tokenizer dependencies. Full-package qualification is separate from this focused compile. Precommit fixed-process evidence correctly retains its earlier HEAD label and final source-byte hashes; it is not relabeled as committed-head qualification.

## Qualification and integration

Completed final results and exact bindings are generated in qualification.json by verify-qualification.py. Native Debug and Release each pass 1,673 definitions, including all 161 NLP definitions. Final qualification also binds the actual main workflow, 19 benchmark checks, Swift 6.3.3 compatibility with SDK 26.5 and Python/Swift CodeQL before PR submission. Xcode 27 remains selected. Known four pandas Wampler strict failures, unsuppressed legacy PostgreSQL MD5 finding and separate MLX concurrent cold-start limitation remain open.

The initial full-check launch lacked required sandbox escalation. Five jobs stopped before tests for compiler-cache/Xcode/network access; their original logs/receipts are retained under setup-failures. They are separate from corrected-access qualification. Python CodeQL completed on its initial launch and is retained without an unnecessary rerun.

The extra local coverage guard inherited from the preceding unit still exposes the unchanged hosted positional-export defect. Original main workflow steps and that failed additional guard remain distinct. All eight workflow run steps pass; the separate export covers all eight changed executable NLP lines. A separate explicit-object export of the same test profile measures changed LocalEmbeddingEngine executable-line coverage. This is local evidence, not a Codecov service result, branch coverage guarantee or workflow repair. Workflow files and coverage thresholds/exclusions do not change here.

The actual Git three-way merge with PR94 head a9732e04f5c5ca16fc6aadf39d0707fe85721246 is clean at tree 232731e39d0491fe9bd069b34bd15f23b43999c4. Its only differences from qualified source are PR94's two exact updated requirements files. Swift production/tests, workflows, package pins, Codecov and comparison requirements are byte-identical. This is source integration proof, not a separate full runtime or GGUF/LLM-model qualification of the merged tree. Upstream permissions are read-only, so the focused correction is delivered from our fork for upstream review. PR94 will need the correction merged/applied and its branch updated before its failed CI can be considered resolved.

## Retained publication

FILES.sha256 covers the full package. verify-publication.py verifies stored files, decoded gzip hashes and all benchmark archive members. Hostname/native-device identifiers are redacted with original/published mappings; authorized filesystem paths remain. Raw task transcripts, build caches, probe binaries, native result bundles and full CodeQL databases are excluded. Native trees, logs, regression fixtures/controllers, source patches and exact source/archive checks remain reviewable. Later PR/tracker observations and final publication audits stay outside this immutable package. Hosted outcomes must be read independently of local qualification.
