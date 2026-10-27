# Initial independent evidence and trail audit

Reviewed by gpt-6-astra. Completed 2026-10-27T18:24:23.673198+00:00.

No initial source or evidence blocker found. Full qualification is still pending, so this is not final sign-off. I inspected existing source, logs, receipts, recorded process outputs and the current 305-line scoped transcript. I ran no builds or tests and made no source or remote changes.

The clean candidate `3012a6e52d70306a9437fb8cd8af4343a41560dd` is directly on `01d48cbcd940c886546b2bb8d6b177d9b7a0e277`, with exactly the engine and two relevant test files changed. The actual patch matches those Git objects. PR94 head `a9732e04f5c5ca16fc6aadf39d0707fe85721246` differs from that same base only in two Python requirements files; its NLP source and tests are byte-identical to base.

The hosted snapshot has one failed check, eleven successful checks and one skipped Pages deployment. The safe-test log has one error, the exact food-versus-technology assertion in the local embedding classifier fixture. Upstream permissions permit reading but not pushing. The evidence supports fixing the pre-existing randomized embedding behavior in a separate fork change; it does not show that the Python dependency changes caused the NLP failure.

I independently recomputed the saved output statistics. The baseline records contain 40 distinct vectors in 40 processes. A separate bounded reproduction with the same verified baseline binary records its first food classification at attempt 55. Final-head records contain 100 outputs, one distinct vector, 100 technology predictions and 100 ASCII golden passes. Source fingerprints match the respective baseline/final Git objects; controller, probe and binary hashes match actual files. The extracted hash helper equals the existing tokenizer helper verbatim. The earlier precommit fixed receipt is source-byte evidence and is not relabeled as a final-head run.

Actual isolated XCTest logs and source/controller bindings show five executed tests, with seven assertions failing in the single new coordinate test before the production change, followed by five passing tests after it. This must not be described as five separate failing test definitions. Independent UTF-8 FNV arithmetic confirms abc's negative bucket 5, café's negative bucket 9, caf's negative bucket 3 and afé's positive bucket 6. The resulting normalized literal vectors match the test. The test does not call the production hash helper to construct its expected values.

The source reuses the existing deterministic helper, computes each word/ngram hash once and uses unsigned magnitude rather than trapping signed absolute value. Existing dimensions, normalization and interfaces remain unchanged. The classifier fixture retains classification and score-sum assertions but now exercises explicit hypothesis overlap. That is a defensible integration contract for this untrained projection, not semantic accuracy evidence. Documentation explicitly warns that earlier persisted vectors and indexes must be rebuilt.

The recorded clean merge tree exists and differs from the candidate only by the two expected PR94 requirements files, each equal to PR94's exact blob. This establishes source integration, not completed runtime qualification of the combined dependency tree. No such runtime claim is supported or needed for the narrow source proof.

All retained setup-failure file hashes match. Logs show compiler-cache/manifest/Xcode access and package DNS failures before test execution in the five initial full-check jobs. The trace distinguishes those attempts from the actual failing regression test and retains the earlier probe/XCTest framework setup errors. The three decision rows accurately record diagnosis, red/green correction and the failed full-check launch/restart. Completed qualification receipts must still be inspected after the restarted jobs finish.

## Attention

Reviewed by gpt-6-astra.

- Stored embedding coordinates change. Rebuild old vectors and indexes; do not promise compatibility with previously randomized data or learned semantic classification quality.
- The 100-process result proves consistency of the sampled inputs on this host. Preserve the independent coordinate tests as the lasting regression guard.
- Full native, workflow, benchmark, compatibility and security qualification is pending. Initial environment failures must remain separate from the final results.
- The PR94 merge-tree proof does not qualify its combined Python dependency runtime. Keep that scope explicit.

## Bound initial snapshot

| Artifact | SHA-256 |
| --- | --- |
| `production.patch` | `f3b851f0cc3fa660a04d40870c524f34330b45871c9b859feef17036a1a5cb60` |
| `baseline-repro/result.json` | `f33923dd0b4ced534bddce0eddb2333376c19ca7a347c1df1c075aa10d29dbc3` |
| `classification-failure.json` | `daf3ec9d736d7b6b6cceceba2e30d21ff748aedb45dfa0f857bc321a26b227c1` |
| `red-coordinates-xctest/result.json` | `9f93706ae8cc283218194e3a9a82ea482bee2990ee55894f58d61664d0ff51e8` |
| `green-coordinates-xctest/result.json` | `30ebfd68b0bdafb5e15b0ced2bfec76544888728801ef6024e3772b0cfb048d3` |
| `fixed-final-processes/result.json` | `e97a75a15f709025e4b068562e87801ae8505932505e12a0a96d4128f723479a` |
| `pr94-integration.json` | `188818ee6c54b041188fbadec372037fe8006717293793b14a47007b3786758c` |
| `setup-failures.json` | `19e1c688926bd675fc38a543e530fbc82770a51918f57b980bfb27b245f9090b` |
| `decisions.tsv` | `8b677cb9b6d4d8ca01a395fc174b2875bd211b2001cb9584cf778cbf8719b19a` |
| `task-transcript.jsonl` | `6983a15800f7cf957c39a201190808c9dd7e85b168cf431d923596ec2b402678` |
