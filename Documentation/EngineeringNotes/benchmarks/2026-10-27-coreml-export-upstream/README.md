# Independent multiclass Core ML export correction

This delivery isolates the existing correction from `a1e234d25677d91ce5914062603c41233fe13c09` directly on upstream main `e19db7dda4567c425b7eb002da82e234e6c7980f`. Frozen candidate `bdf2b57a66330c331bb870a4d762bb94f7dae0a9` changes three serialization files and one regression suite. All four files match the prior correction byte for byte. It is independent of prepared PCA PR #89 and GPU gradient PR #90.

## Failure and correction

The public multiclass MLP exporter requested softmax but encoded an empty generic activation. Core ML rejected the exported artifact with `Nonlinearity type INVALID`. Both analytical regression definitions compile and fail on actual upstream without skips. Their baseline source and exact logs are bound by `red-source-binding.json`. Both definitions pass after correction.

The corrected serializer emits SoftmaxND, field 950, with int64 `axis = -1`, applying normalization along the output dimension. Apple's [format reference](https://apple.github.io/coremltools/mlmodel/Format/NeuralNetwork.html#softmaxndlayerparams) defines this distinct layer. The unused legacy softmax constant is replaced. No new public abstraction is added.

The supplied-weight test compares every probability to independently calculated max-shifted softmax, including logits of magnitude 1000, reordered and repeated rows, both batch sizes, row provenance, packing/copy accounting and reservation release. The fitted-classifier test exercises public fitting, class order, export, actual Core ML compilation and prepared inference. Its outputs agree with native public probabilities at the unchanged 1e-6 bound.

Specification version 4, existing rank-one probability shapes, public signatures/default output name, class-label compatibility argument, binary sigmoid, hidden activations, regression, dependencies and device policy remain unchanged. Documentation clarifies the existing probability output. This fix makes multiclass artifacts loadable; no speed, model-quality or Neural Engine placement claim follows.

## Verification

`qualification.json` reports passed after `verify-qualification.py` checked original artifacts, source hashes, actual security extraction/archive bytes and worker identity. Native Debug and Release each pass 1,658 definitions without failures or skips. Focused corrected tests pass both definitions; the actual upstream baseline compiled and failed both. The complete local main workflow passes eight steps and benchmark workflow passes all 19, including three MLX CPU panels. All four Swift 6.3.3 compatibility steps pass, including both new runtime regressions. Python CodeQL reports zero findings. Swift CodeQL completes with one unchanged, unsuppressed PostgreSQL MD5 finding at `Sources/SwiftDatabase/DatabaseConnection.swift:606`. Earlier broad study results remain historical evidence, not fresh runs on this head.

Hosted safe tests skip SwiftMLTests and the existing Codecov configuration excludes SwiftML source. The fresh native tests execute actual compilation and inference. The main workflow's original documentation checker still prints an inaccurate 100% claim; this delivery does not change that checker or claim a coverage percentage. The local controller additionally validates actual SwiftDataFrame LCOV records with Python's standard library.

Swift 6.3.3 compatibility uses the installed compiler and SDK 26.5 per command, leaving Xcode 27 selected. The runner builds both configurations, compiles all test targets, runs the safe suite and additionally executes the two Core ML regressions. Matching-compiler Swift CodeQL analyzes the actual changed serialization source. Its retained legacy database MD5 finding must remain visible. Passing analysis is separate from clean security.

The benchmark workflow preserves all tolerances and the four known strict Python Wampler comparator failures. A passing regression policy does not make those cases strict passes. Native execution covers one Apple silicon host, not every supported OS/runtime.

## Tooling state

Isolated APFS cache copies retain earlier study state. The first compatibility build rejected copied Clang precompiled modules because they retained the previous workspace's absolute ModuleCache path. `compatibility-cache-path-failure` and `cache-recovery.json` preserve that failure. The retry regenerates compilation state in a fresh scratch directory, copying only pinned dependency checkout/repository/artifact state. Source and compiler are unchanged. Copied native caches may produce stale-path warnings; logs retain them. Existing build/dependency/documentation warnings are not presented as warning-free results.

`controller-derivation.json` records only local cache-path substitutions and the extra older-compiler runtime tests. The workflow controllers reuse the previously corrected standard-library LCOV gate. Production workflows, coverage exclusions and numerical policies are unchanged.

## Independent reviews

### Standards

No findings against documented standards or the reviewed smell baseline. The serializer remains the owner of field selection, and the unused constant is replaced. [Full report](standards-review.md).

### Spec

No missing requirements, scope changes or incorrect implementation found. The independent tests and axis encoding match the fixed spec. [Full report](spec-review.md). These reviews have zero findings on each axis.

## Inspect and replay

The exact four-file patch, spec, independent standards/spec reviews, controllers, source hashes, exit codes and logs are retained. `verify-qualification.py` validates original raw artifacts and frozen source. Native result bundles, generated caches and the CodeQL database remain local. Published logs and comparisons are compressed, with original-to-published hashes. Machine hostname and native hardware identifier are redacted; authorized filesystem paths remain. Raw chat transcripts are excluded.

Run `python3 verify-publication.py --records PATH` to check a downloaded evidence package. This checks integrity rather than rerunning numerical work. Local workflow replay excludes service uploads, deployment and GitHub-hosted operating systems. The earlier [representative legacy Core ML study](https://github.com/crabel99/SwiftSci/blob/codex/engineering-notes/Documentation/EngineeringNotes/benchmarks/2026-10-26-coreml-representative/README.md) retains its distinct source fingerprint, strict comparisons and observed CPU placement. No placement result is imported into this new correction's qualification.
