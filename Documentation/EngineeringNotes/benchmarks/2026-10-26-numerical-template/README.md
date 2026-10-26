# Public numerical workflow qualification

The copyable [template](template/README.md) runs public Imputer → StandardScaler → prepared PCA → prepared LogisticRegression. Its fixture selects features and targets together before fitting. Only eight training rows enter learned stages. Held-out rows `[10,8,10,9,11]` transform and predict with retained source-row identity.

The authoritative result is [final-run-qualified/verification.json](final-run-qualified/verification.json), against SwiftSci `0e1635199654ac6a20b32ea53eea0ffdfa39e747`. Both external public-import probes exited 0. Independent scalar preprocessing, a closed-form 2×2 PCA eigensystem and 64 scalar logistic updates agree within `abs(error) <= 1e-12 + 1e-12 * abs(reference)`. The largest observed absolute difference is `4.440892098500626e-16`. Separate legacy API results agree exactly. Predictions are `[1,0,1,1,0]` in the held-out selection order.

This is a toy integration check. It establishes no statistical-quality, speed, memory-bound or hardware-routing result. No production API was added. The template uses public Imputer and StandardScaler because StandardPreprocessingPlan has no public general transform operation.

The native executable package build passed in [package-build.log.gz](package-build.log.gz) in packaged records, or `package-build.log` in the original workspace. Its Swift source bytes match the public template and qualified prepared probe. Its JSON output equals the qualified prepared output. [package-source-binding.json](package-source-binding.json) and [local-manifest.diff](local-manifest.diff) record the sole dependency transport substitution: the public manifest's exact remote revision became the verified local checkout. That local substitution remains separately preserved as historical transport evidence.

A later [remote package check](remote-package/receipt.json) resolved the unchanged public manifest from GitHub, checked out the exact qualified revision, built into a fresh native output directory, and ran successfully. Resolve, build and run all exited 0. The remote checkout's tracked production source and package manifest match the qualified source bytes. The seven resolved dependency pins are preserved in `template/Package.resolved`. The executable's output equals the independently checked prepared result exactly. `qualification.json` binds the controller, manifest, consumer, resolved pins, checkout files, step logs, executable and output. The checkout's origin is SwiftPM's local mirror; qualification also checks that mirror's origin URL against the GitHub dependency. The [remote review](remote-package-review.md) describes this additional proof.

The current [standards review](standards-review.md) has no open findings. The original P2 concerned an evidence runner that could stamp old probes with a newer source identity. The corrected runner binds the probes' input-build-log path and SHA, restricts objects to the selected build products, and verifies object, binary and consumer source hashes. [mismatched-build-rejection-final.json](mismatched-build-rejection-final.json) records the old probes' rejection before execution. The [spec review](spec-review.md) covers the public workflow and independent oracle. Those earlier reviews preceded the later remote package check; their original local-only transport conclusions remain historical evidence.

Qualification requires an exact source HEAD, an empty source Git status and matching source file hashes. Generated or untracked source-checkout files must be cleaned up before qualification. The original checkout, remote checkouts, probes and retained build products are needed for local receipt verification. The publication verifier needs only the packaged records.

Preserved failures are labelled separately:

- `ScientificWorkflow-before-compile-correction.swift` and `public-probe/compile.log` retain the initial unsupported matrix `rowValues` calls. Removing the unnecessary matrix conversion corrected the template. `prepared-run.log` records the subsequent attempt to launch a binary that the failed compile never produced.
- `final-run-bound/prepared.json` contains an MLX no-Metal-device diagnostic from a sandbox launch. That file is diagnostic text despite its extension. It is not a numerical result, and the attempt has no passing verdict. The successful qualified run had device access even though PCA and logistic explicitly request CPU execution.
- `run-template-before-binding-fix.py` retains the runner that preceded the resolved build-binding finding. Only the current `run-template.py` and `final-run-qualified` support the final receipt.

To verify the retained local evidence without building or launching Swift, run:

```sh
python3 verify-qualification.py
```

The script checks source, build, probe and artifact bindings, recomputes the scalar oracle from saved JSON, and writes `qualification.json`. It does not repeat model training or numerical consumers. To create a new immutable records directory after review, run:

```sh
python3 package-records.py --output records
python3 verify-publication.py --records records
```

The packager refuses an existing output directory. It includes only the named source, scripts, reviews, receipts and logs. It excludes caches, binaries and unrelated transcripts, compresses both native package build logs deterministically, and replaces hostnames and native device identifiers. `publication-records.json` binds original and published bytes, including decompressed payloads. `FILES.sha256` binds the complete file set. These are integrity checks, not an independent certification of the claims in each record.
