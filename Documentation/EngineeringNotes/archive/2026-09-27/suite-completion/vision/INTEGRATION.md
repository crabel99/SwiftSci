# Integration notes

Copy the candidate `Benchmarks` files into matching repository paths. They do not replace existing files. No production source changes are needed. Regenerate after changing any of the four pinned files.

1. Register `vision-letterbox-cpu` in the Python contracts operation set and the workload and dataset JSON-schema operation enums. Add `vision-reference-v1` to the dataset schema's reference-basis enum. Register `vision-conformance` in the profile allowlist.
2. In `numerical_fixtures.py`, import the vision validator, `output_count` and `TOLERANCES`. Add the operation to `OPERATIONS`. Require operation/basis equivalence and exact tolerance equality in `validate_manifest`, dispatch input validation, and include vision in recursive source-lock verification. In `expected_values`, require matching reference operation, then validate the complete reference length and finite values. The result is `reference['independentReference']['values']`.
3. In `NumericalWorkloads.swift`, add `case visionLetterbox(VisionLetterboxInput)`, recognize the operation as numerical, decode with `VisionLetterboxInput.decode(data, rows: rows)`, and dispatch to `executeVisionLetterbox(input)`. `Package.swift` already lists SwiftVision as a benchmark target dependency.
4. In `standard_worker.py`, import `prepare` and `execute` from `vision_workloads` under distinct names. Prepare validated input outside timing and execute the prepared value in the operation branch.
5. Add `vision_fixtures.py` and `vision_reference.py` to the runner's oracle source provenance list. Confirm worker identity includes the new Swift and Python source files through existing source discovery.
6. Add a worker-boundary negative check for at least truncated pixels, invalid target dimensions, HWC layout, nonconstant resize, boolean dimensions and unknown fields. The candidate unit tests validate the Python boundary. Swift rejection still needs parent integration coverage.
7. Run the existing contract suite, six candidate tests, release build and the eight-case `vision-conformance` profile for both engines. Update any expected inventory/profile counts through the existing mechanism.

The scratch Python suite passed all six tests using the repository's pinned virtual environment. It checks every fixture hash and source-lock entry, complete references, NumPy agreement, repeated execution, hand-computed CHW/RGB and grayscale answers, padding placement, every output index as a negative control, malformed inputs and generator reconstruction.

Swift integration and full public-API execution remain the parent task's responsibility. The Accelerate scratch probe confirms which resampler the current production flag requests; it is not a substitute for running the integrated worker.

Source findings are documented in `Benchmarks/Fixtures/vision/README.md`. Do not report general bilinear/Lanczos correctness or raw-byte normalization as certified. No production discrepancy has been hidden by copying measured Swift answers into references.
