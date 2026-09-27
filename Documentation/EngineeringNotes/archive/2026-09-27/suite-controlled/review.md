# Stage 3 cross-model review

Reviewer configuration: gpt-5.6-sol

No blocking error was found in the Stage 3 suite contribution. The controlled fixtures, independent references, worker adapters, retained failures, and scope statements agree with the available evidence.

The controlled run contains 20 engine cases and passes 17. Its only failures are the three reported SwiftSci behaviors: supplied-weight linear prediction requires a fitted model, supplied-weight logistic prediction requires a fitted model, and cosine search returns zero for identical vectors whose norm product falls below its fixed threshold. The run and certificate both have `failed` status, their digests match, and the audit rejects the failed certificate. The existing smoke profile contains 28 passing engine cases with a matching passing certificate and run digest.

The reference contracts are appropriately narrow. Exact or high-precision calculations cover supplied affine inference, strict logistic classification at probability 0.5, one-cluster KMeans, every Kalman filtered state and covariance plus one prediction, cosine identities and scores, and exhaustive two-feature Shapley contributions. Cosine canonicalization validates result count, unique and valid identities, finite scores, and native closest-first order before sorting only mathematically tied rows by input identity. It does not conceal wrong membership or rank. No fixture claims multi-cluster initialization, sampled explanations, zero-vector behavior, model quality, or a formal performance baseline.

Verification is proportionate and consistent. All 75 controller tests pass. The Release worker build completed without coverage instrumentation. Eight real-worker controls pass, while both workers reject 24 deliberately invalid requests covering wrong outputs, malformed family-specific inputs, and leaked expected answers. Fixture regeneration is byte-for-byte checked. The staged patch is clean and modifies no file under production `Sources/` or `Tests/`.

## Attention

- The three discovered production errors remain unfixed by design. They require later work on a separate repair branch, with one commit per error, before a formal performance baseline.
- The decision trail is truthful but two evidence cells are incomplete. The validation row claims the Release build passed while pointing only to `controller-tests.log`; it should also point to `worker.build.json` or `build.log`. The runtime row says the failed certificate was rejected while pointing only to `results.json`; the direct evidence is `failed-certificate-audit.log`. These are traceability gaps, not contradictions in the retained evidence.
- Controlled search uses individually pinned source, input, and reference files but has no family inventory file. This is weaker for discovery than the controlled-model family, though manifests and hashes still bind every executed case.
- The references are independent of both runtime workers, but each fixture family has one reference generator. Regeneration proves determinism and provenance, not agreement between two independently written reference solvers.
- I did not receive the full run transcript. This review checks the trail against the supplied summaries, staged patch, and retained evidence files; it cannot verify unrecorded conversational decisions.
