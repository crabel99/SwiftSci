# Independent substantive and trail audit

Reviewed by gpt-6-astra on 2026-10-27. No blocking finding for the focused draft under its stated limits. The observed MLX concurrent-initialization hazard remains material open Attention; passing serial compatibility tests do not resolve it. Publication/privacy and eventual remote delivery require separate checks.

## Source and dependency boundaries

The clean frozen source is `3fd462155a10fa78a1cf6b98b56ea926d43ef112`, directly above the exact GPU prerequisite `506204920a5a073b1e7bc316476875860bacfda0`, whose parent is upstream `e19db7dda4567c425b7eb002da82e234e6c7980f`. Both retained patches match their actual Git comparisons. The classification commit changes exactly 11 files; the full upstream diff has 13 files across two commits. Ten feature files exactly match `8926829bf2952a8f981a8be199be9ee9c3f7c458`, and the corrected logistic regression test file exactly matches `c4de6cc866fff6f52100535dbcb38dd708558200`. Recorded hashes agree.

The source follows the bounded spec and independent standards/spec reviews: prepared requirements preserve legacy dispatch, native logistic operations read compact columns, CPU scratch is reused without changing update order, and complete fitted state is published after successful work and cancellation checks. Pipeline locks cover short lifecycle transitions without suspension; concurrent predictions are allowed while fits exclude competing operations. The corrected PR wording reflects that distinction. Schema, provenance, snapshots, strict thresholds, soft targets, positional legacy behavior and failed-fit recovery have focused tests. No unrelated PCA implementation, serialization, agent, workflow, package-pin, Codecov or numerical-policy change enters this feature.

## Actual qualification

I queried the actual native xcresult summaries. Debug and Release each contain 1,683 passes, zero failures and zero skips, matching their saved summaries and source-bound build receipts. The eight main steps, 19 benchmark steps and Python security steps pass, with matching step-log, controller, workflow and source hashes. The benchmark worker binary and all 503 recorded source-file hashes agree with this unit. The unchanged policy retains four strict Python Wampler failures; its acceptance does not turn them into passes.

The actual Swift 6.3.3 final receipt has four successful steps: production Debug build, safe suite/all-test compilation, focused runtime and production Release build. The focused log shows 27 tests across all five intended suites, including prepared logistic numerical/GPU tests and the BCE prerequisite. It explicitly uses `--no-parallel`; the pipeline tests retain their own concurrent tasks. The copied Metal resource matches its native source digest, and both dependency checkouts are clean at the same pinned MLX revision. This is Swift host-code compatibility on the current Mac using an Xcode 27 Metal resource, not older-Xcode Metal compilation or older-OS qualification.

Python CodeQL reports zero findings. Swift database creation and analysis complete using matching Swift 6.3.3 compiler/extractor. The actual SARIF retains one `swift/weak-password-hashing` finding in unchanged `Sources/SwiftDatabase/DatabaseConnection.swift:606`. I independently enumerated successful extraction notifications and checked all 348 archived repository files against current bytes: 288 library files, 59 benchmark files and Package.swift. All four changed production Swift files are included. This is the observed static-analysis set, not a claim that all Swift test sources were extracted.

The final evidence verifier actually executed with exit 0 in the scoped transcript. Its output log agrees with `qualification.json`; the verifier digest, evidence-record digests and current Swift fingerprints match. No earlier historical qualification is relabeled as this execution.

## Public workflow and provenance

The retained public controller runs nine fresh processes: baseline legacy, candidate legacy and candidate prepared, each at 0, 1 and 32 epochs. I inspected the probe and independent reference code, verified fixture/output hashes and independently recalculated the small reference comparison from the saved inputs and outputs without rerunning a Swift probe. The 569 rows partition exactly into disjoint 328/115/126 training/validation/test sets. Scaling is fitted only on training rows, and the reference follows the public Float learning-rate conversion with Double CPU arithmetic.

All 10,521 numerical fields match exactly across the baseline/candidate variants. Labels and row positions match exactly. Independent maximum absolute deviations are 0, 2.220446049250313e-16 and 1.1102230246251565e-15 at the three epoch counts, within the declared unchanged 1e-8 absolute/1e-9 relative comparison. These are complete finite-step CPU outputs, not a GPU-equivalence, predictive-quality, statistical-repeatability or performance result.

Both probe binaries, shared probe source, input build logs, link lists and all 28 linked objects per probe match their proof records. The baseline build receipt is an exact copy of the prior GPU-prerequisite Release receipt; all 660 recorded source hashes match that historical commit. The baseline probe is freshly compiled, linked and executed using retained qualified library objects. The baseline library build itself is historical. Candidate objects come from the current source-bound benchmark build. The README and PR body preserve this distinction.

## PCA integration and preserved failures

The qualification-only PCA commit `826dbb95dae9830ac1e693a79b158b72ce1ab238` has the recorded merge tree `d26ffe0243144efdfb5e85f9987e1bf5cae17ec4` and a clean checkout. Both prepared-batch helpers survive. Its actual xcresult has 33 passes with no failures or skips, and the test-tree identifiers match all eight requested suites, including both prepared PCA routes, overflow/workspace regressions and classification/lifecycle tests. This focused integration check does not add PCA to the delivery source or constitute full-package qualification of the combined tree.

Three failed attempts remain distinct: PCA checkout creation failed before building because of nested Git alternates; the first older-compiler focused runtime failed for a missing Metal library; the combined five-suite cold-start invocation blocked and its sampled helper was deliberately terminated. Original receipts/logs/controllers, the Git-reference repair and the stack sample remain retained. The subsequent serial probe and complete four-step compatibility run passed without source or tolerance changes.

**Attention: observed concurrent cold-start runtime hazard.** The sample and unchanged pinned MLX implementation support a lock inversion: BCE evaluation holds the evaluation lock while waiting for global stream initialization; another thread owns that initialization and waits for the evaluation lock. Both baseline and candidate use the same dependency revision, and the baseline CPU path also constructs MLX parameter representations. There was no baseline reproduction of this hang. The reason full native runs avoided it was not established. Serial starts validate the intended numerical/lifecycle tests but do not establish concurrent cold-start safety. The README and PR body disclose the hazard explicitly; it remains open rather than fixed by this contribution.

## Trail and pending delivery

The 676-line scoped transcript is parseable and contains the actual qualification exit, failed attempts, targeted helper termination, and subsequent recovery. The append-only decisions distinguish source reconciliation, public evidence, PCA runtime integration, compatibility limitation and final qualification. Two Git transport attempts failed DNS resolution; those failures are preserved. Subsequent API reads confirmed the expected upstream state.

I inspected the pending API publication controller and its read-only dry run. The plan contains 11 blobs, 10 trees and one commit, with no uploaded objects and no branch write. The controller checks exact returned object identities before changing a ref, rejects unsupported commit headers, uses no force update, and rechecks destination state and final head. This review is not proof that GitHub will preserve the requested commit metadata; actual identity checks and remote readback must pass during publication. A mismatch must not be described as publication success. No API fallback publication is claimed here.

Package/privacy review, verified source/notes publication and the final records URL remain delivery gates. GPU prerequisite ordering and current PR metadata must be checked when preparing the actual draft. No source edits, builds, heavy test reruns or remote writes were performed during this audit.

## Reviewed snapshot

- `qualification.json` SHA-256 `7d5d595b67c4ebbb052a8b17dce7103cfb3cf3398cd15bfcb4bf9d09f7b36249`
- `qualification-verifier.log` SHA-256 `8de0d5528c898004a050952a7b75c1c2fb35c5c94aab5345e0c0b7ed9df2a000`
- `verify-qualification.py` SHA-256 `f1757998b8e751c6ea28eb83401c869fdbcf8a404ec5185dba15e47cd654a4d7`
- `source-reconciliation.json` SHA-256 `f5e5ff7e4170c4450145d8d139b661d29ac497f07f1bfa68443355a2d2cc015e`
- `decisions.tsv` SHA-256 `59b5422057d37b9daea502285f09b46618546e709d56ed3eeb9441db7b17577e`
- `task-transcript.jsonl` SHA-256 `cab7fbee421236e102cee47d74e4f0a40a4baed732c5fc5a2619ce91d36bc854`
- `README.md` SHA-256 `10272a31f16223e4b1b5f96d65782cc8491daccf4b312b91eea15fa3af551f53`
- `pr-body.md` SHA-256 `655946cf77f2e4f15ac0b21da53b9c467bb87ca1cbf571b03b3ce4f3358a8417`
- `compatibility/result.json` SHA-256 `f6c9015eef143cf15663826d8e1f096f957c57f08d6c74de98b862729b3ebff2`
- `check-swift633.py` SHA-256 `1eba182c92b3a58dce88a6cd3575b69ac522a06655e1ba1fb6696361de657b4a`
- `verification/public-workflow/summary.json` SHA-256 `d63550b1b1b836bb3f917d78a7237a2ac6606b68dee170bc39d1e2cc17cf126f`
- `verification/baseline-provenance.json` SHA-256 `f8dd4bd23a2090862490d64902328d3988009d80c27b105d23c8ace1f480b71c`
- `pca-integration/result.json` SHA-256 `93bf6efaefde5ffd907116563050ea0cb29d18861e6887285dbbd71b0807eb0d`
- `cold-start-assessment.json` SHA-256 `4196250fbbf48029a3e9a8f214800555d6ddff234bd99ffb45fac4b1244d30e2`
- `compatibility-combined-cold-start/focused-helper-sample.txt` SHA-256 `8d040ed58ca644e22ea981d24e7bb18df2db36408795a3bdd3fe66eb92ebbe1c`
- `publish-git-objects.py` SHA-256 `aa0c851c02cc65cc6157530fcef4d3efb123d11753d2775e25667a7920aedffc`
- `source-api-dry-run/result.json` SHA-256 `30d9eb66560aa15f2701991729e26c3ae0a9e76e7b58ede037348910be5d8e58`
