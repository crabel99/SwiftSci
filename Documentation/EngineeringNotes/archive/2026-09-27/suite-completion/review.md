# SwiftSci suite completion review

## Verdict

No blocking finding remains. The testing branch completes the declared vision, dataframe-to-MLX boundary, bounded sweep, and suite-acceptance scope without changing production source files. The final evidence is internally consistent, preserves 30 known failures, and reports complete coverage rather than treating those failures as passes.

This is an artifact-only review. No full run transcript was available. I reviewed commit ab7aa2f1dab7256eed5de177fb5060a25740c643, the repository artifacts, and the private evidence under /private/tmp/swiftsci-suite-finish. I did not edit the repository.

## Acceptance integrity

The initial acceptance implementation had four material gaps: it did not bind the full worker request, did not freeze fixture and specification content, accepted weak failed-response evidence, and lacked outer controller timeouts. The final implementation resolves all four:

- It reconstructs every request from the authoritative profile, dataset, and workload.
- It verifies pinned input bytes and independently regenerated expected bytes.
- It freezes every tracked file under Benchmarks/Specs and Benchmarks/Fixtures, then checks that identity before and after every profile.
- It requires exact event/response equality, strict failed-response fields, the expected case identity, empty samples, and a nonempty engine version and error before counting a worker failure as complete evidence.
- It bounds preparation and profile execution and continues to later profiles after a failure or timeout.

The first all-tier run exposed one audit-contract error: the Python worker deliberately records peak_rss_bytes as zero when it fails before a successful measurement, while acceptance required a positive value. Commit ab7aa2f1da changes only the failed-response rule to accept a nonnegative integer. Zero remains failure metadata, not a sample or a pass. Negative integers, Booleans, floats, strings, and missing values are rejected. Passed results still use validate_worker, which requires positive RSS. A focused regression failed before the correction and the final controller suite records 135 passing tests.

## Final evidence

The Release worker and every profile bind to the same committed source:

- commit: ab7aa2f1dab7256eed5de177fb5060a25740c643
- source tree: dfdc1bc7facd9e1aea483897ddaa534991f44f1e32a9b4a25fd09e3a464b8146
- worker binary: 3863c0cdc295b5b0099748c1909a269c131e0c04a7afa6b5be5905c9bd450601
- suite contract: 7f4c969ba78bd6bf2c2068f5eadac2fa3fe0dd0ccf912a3b4893c114cf4ef0f8
- acceptance report: 42060e498758e4d82ded8ba39ebedb2223026c105fc2d6bee4369eaa867acb72

The build verification checked 359 source files. All 22 profile plans contain the same source tree, worker binary, and pandas environment record. Their individual contract hashes differ as expected because each profile resolves a different case set.

The final all-tier run records 1,132 engine executions: 1,102 passed and 30 failed. Every profile has complete evidence and there are no infrastructure errors. The 30 failures remain failed numerical or API results in controlled, model, neural, neural-loader, and numerical profiles. None was converted into a pass. Every per-profile run status, certificate status, event count, source identity, and contract hash agrees with the top-level acceptance record.

All new profiles pass:

- boundary sweep: 108 of 108 engine executions;
- bounded vision preprocessing: 16 of 16;
- CPU and GPU dataframe-to-MLX boundary: 12 of 12;
- CPU-only dataframe-to-MLX boundary: 8 of 8; and
- supervised conformance: 12 of 12.

The 84 negative-control executions cover six representative vision, boundary, and sweep cases on both engines. Twelve unchanged controls pass. Seventy-two wrong-output or malformed-input variants fail with errors, including first, middle, and last output changes, embedded answers, unsupported devices, and invalid shapes.

The sweep report contains 108 passing results: 54 per engine, 36 per stage, 36 per supported device/precision pair, all three row counts, and both widths. It labels RSS as whole-process lifetime high-water memory, keeps logical payload sizes separate, describes the stage timing boundaries, and sets formal_performance_baseline to false.

## Scope and claims

The vision contract uses the public ImageDataset and YOLOPreprocessor on explicit MLX CPU. Spatially varying fixtures avoid resize; constant-plane resize fixtures have analytic answers. The documentation limits the result to layout, grayscale expansion, dimension rounding, constant preservation, and padding. It does not claim arbitrary interpolation, raw-byte normalization, production input safety, or model quality.

The boundary contracts exercise public dataframe filtering and stable sorting, flat and nested exports, CPU Float32 and Float64, GPU Float32, affine computation, complete readback, row alignment, and tested mutation isolation. Their scalar oracle does not use pandas, NumPy, or MLX. GPU Float64 remains explicitly unsupported.

The 54 sweep cases expand deterministic descriptors before timing and return actual outputs from conversion, prepared computation, or the full pipeline. The report does not call process RSS an operation allocation measure and does not present these diagnostics as a formal performance baseline.

No tracked production file under Sources changed in the reviewed range. The Package.swift change only adds MLX dependencies to the benchmark worker target. Repository whitespace checks pass. Existing unrelated untracked duplicate files are outside the reviewed commits and acceptance source identities.

## Attention

reviewed by gpt-5.6-sol

- No full transcript was available, so this verdict is limited to the committed files and supplied build, run, audit, negative-control, sweep, and decision-trail artifacts.
- The final archive and its hash manifest were not yet present when this review was written. The archive should retain both all-tier runs, the top-level acceptance hash, the worker build record, the source verification, the controller log, the negative-control summary, the sweep report, this review, and the decision trail.
