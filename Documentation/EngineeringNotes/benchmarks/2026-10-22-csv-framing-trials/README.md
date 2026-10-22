# CSV framing and coordinate-allocation experiments

No production change is promoted from this investigation. The implementation remains at `9c067c6c5116d78c0849073acea7fb150404efab` on `codex/csv-column-concurrency`. Its serial and parallel conversion options remain available.

Three trials targeted the existing field-coordinate builder. None produced a consistent CPU improvement in full public reads. The results favor keeping the current storage and its cached field count until another design has stronger evidence.

## What was tested

| Trial | Change | Decision |
|---|---|---|
| Consume block list | Consume the builder and append its final block directly to the existing list | Reject. Two small allocations disappear, but full-read CPU time does not improve consistently. |
| Smaller header storage | Start coordinate storage empty for scans limited to one row | Reject. Allocation volume falls, but allocation count rises and larger reads do not consistently benefit. |
| Derive field count | Replace the stored field count with the full-block count times block capacity plus the current block length | Reject. Allocation behavior is unchanged and larger framing cases become slower. |

The trials preserve the 16,384-row internal batch limit, native optional columns, inference rules, original-token fallback, explicit conversion errors as null, and the public scheduling choice. They do not introduce a custom allocator, cache, or larger retained index.

## Native allocation evidence

One validated public read of the Aotizhongxin reference file ran in serial conversion mode for each variant. `malloc_history` recorded full allocation history with `MallocStackLogging=full` and `MallocStackLoggingNoCompact=1`. `-noContent` excluded memory contents. Only allocations whose backtrace includes the scanner are counted below. This attribution can include runtime initialization triggered by the scanner.

| Variant | Scanner-attributed allocation calls | Sum of reported allocation sizes, bytes | Difference from parent |
|---|---:|---:|---:|
| Parent | 63 | 5,603,080 | Reference |
| Consume block list | 61 | 5,602,440 | 2 fewer calls, 640 fewer bytes |
| Smaller header storage | 67 | 5,472,624 | 4 more calls, 130,456 fewer bytes |
| Derive field count | 63 | 5,603,080 | No difference |

These are cumulative allocation events and reported sizes, not peak memory, live memory, or energy measurements. One observed read does not establish the allocation distribution of all files. The full reports retain allocation and free events. CPU timings come from separate uninstrumented runs.

An earlier attempt used `MallocStackLogging=1`. The installed allocator's manual states that this selects lite mode, which records current allocations without history. Those reports contained no free records and could not answer the question. They are retained as provisional evidence, not used for the table.

The Instruments Allocations recording failed to attach before the program ran. That recording was stopped, and its target exited. The standalone full-history probe succeeded without changing machine settings.

## Full public-read comparisons

The first matrix contains 576 workers for the consume and header trials. The second contains 768 workers for the derived-count trial. Every worker validates native types, all values, null positions, row and column order against the same independent input contract.

Both serial and parallel modes are measured. Inputs include bike sharing, two Beijing air-quality stations, household power consumption with inferred and explicit schemas, date-format handling, late Boolean and text fallback, and generated files from 1 to 64 columns. Elapsed time and peak resident memory remain separate metrics in [the full summary](public-read-summary.json).

| Input, schema, scheduling | Parent A CPU ms | Consume CPU ms | Header CPU ms | Parent B CPU ms | Derived count CPU ms |
|---|---:|---:|---:|---:|---:|
| bike-day, known, parallel | 0.682 | 0.800 | 0.832 | 0.701 | 0.725 |
| bike-day, known, serial | 0.413 | 0.424 | 0.418 | 0.406 | 0.401 |
| bike-hour, known, parallel | 5.513 | 5.410 | 5.483 | 5.393 | 5.324 |
| bike-hour, known, serial | 3.882 | 3.907 | 3.906 | 3.616 | 3.627 |
| Aotizhongxin, known, parallel | 12.431 | 12.073 | 12.175 | 12.572 | 12.611 |
| Aotizhongxin, known, serial | 9.761 | 9.773 | 9.698 | 9.142 | 9.128 |
| Wanliu, known, parallel | 12.630 | 12.568 | 12.483 | 12.390 | 12.533 |
| Wanliu, known, serial | 9.705 | 9.634 | 9.658 | 9.059 | 9.114 |
| energy, known, parallel | 357.765 | 359.965 | 358.513 | 349.837 | 357.885 |
| energy, known, serial | 304.196 | 314.074 | 311.954 | 305.269 | 317.424 |
| energy, infer, parallel | 363.158 | 357.611 | 362.020 | 354.200 | 372.628 |
| energy, infer, serial | 326.332 | 326.948 | 326.979 | 309.265 | 318.661 |
| energy-date-full, known, parallel | 370.359 | 379.731 | 367.805 | 366.851 | 375.065 |
| energy-date-full, known, serial | 326.063 | 328.218 | 327.434 | 323.897 | 329.793 |
| late-bool, infer, parallel | 6.710 | 6.646 | 6.659 | 6.680 | 6.970 |
| late-bool, infer, serial | 6.567 | 6.811 | 6.569 | 6.605 | 6.816 |
| late-text, infer, parallel | 9.132 | 8.983 | 8.958 | 8.694 | 8.878 |
| late-text, infer, serial | 9.060 | 8.944 | 8.924 | 8.611 | 8.848 |

Parent A is measured alongside the consume and header trials. Parent B is measured alongside the derived-count trial. Compare each trial with its contemporaneous parent. Full per-case elapsed and memory results remain in the machine-readable summary.

All observations are retained. There is no weighted score or removal of outliers. Small differences in these short reads are not proof of improvement. In particular, the consume trial's small positive results on some inputs are not consistent across file shapes or scheduling modes.

The initial console summary accidentally pooled the 257-row and 32,769-row width fixtures under the same width label. The raw worker records preserve the distinct native input IDs. The summary above uses those IDs to separate cohorts. The second controller uses unique labels from the start. No timing record was relabeled or discarded in the saved raw files.

## Framing-only checks

The corrected standalone probe uses the production compiler's optimization, Swift language version, deployment target, SDK, and related options. It scans the first record separately, then bounded record batches. Coordinate destruction is included in timing. File mapping and the complete coordinate digest are excluded.

| Input | Parent CPU ms | Consume list CPU ms | Smaller header CPU ms | Derived count CPU ms |
|---|---:|---:|---:|---:|
| wide | 2.730 | 2.816 | 2.740 | 2.824 |
| bike | 1.158 | 1.163 | 1.180 | 1.224 |
| energy-prefix | 3.528 | 3.539 | 3.538 | 3.699 |
| small | 0.056 | 0.058 | 0.051 | 0.054 |

All four variants produce identical row counts, field counts, batch counts, and complete coordinate digests. The corrected matrix contains 128 workers. The energy case here is a documented 100,001-record prefix, including the header. The full public-read matrices use the complete reference file.

The derived-count trial increases framing CPU time by roughly 3–6% on the larger inputs. The stored count behaves as a useful cache in these measurements. This result does not isolate register allocation, instruction count, or a cache-level mechanism. Compiler code generation can contribute to the observed difference.

These isolated builds contain the parser and record-index files, not the complete production module. Matching compiler options removes one known mismatch but does not guarantee identical code generation. Full public reads determine whether to promote a change.

## The benchmark correction is enforced

The first standalone probe omitted whole-module optimization and used the compiler's default deployment target. Its timings do not represent the production build and are excluded from the framing table. The provisional results and build receipts remain available.

[The matched builder](build-matched-scan.py) now inherits compiler options from the production module's recorded build command. [The controller](scan-matched.py) refuses to run if a probe's recorded options differ or if the executable hash does not match. It also checks AC power and absent coverage instrumentation before measurement. The previous matching mistake is recorded as a failed method, rather than accepted as evidence about the library.

## Evidence and reproduction

[The artifact manifest](artifact-sha256.json) hashes every saved artifact except the manifest itself. [The public-read summary](public-read-summary.json) separates input, schema, scheduling mode, variant, and sample count. [The allocation summary](allocation-full-summary.json) retains the relevant stack frames and event counts.

[The experiment archive](experiments.tar.gz) contains the exact parent parser sources, trial patches, trial source files, and the energy-prefix input contract. Each executable's build receipt records source and binary hashes. Full public-read module receipts are in [build receipts](build-receipts/).

Large raw JSON and allocation logs are compressed with their bytes preserved. The controllers reference the original local input and executable paths. Restore the matching sources and build receipts when reproducing a historical trial, and use a fresh output directory.

No library source or tests changed in this segment, so the full library test suite was not rerun. The previous commit's completed validation remains attached to that commit. This experiment adds 1,344 full-output-validated public reads and 128 coordinate-differential checks under corrected compiler settings. It does not add a new certification claim.

## Next experiment

The results do not justify redesigning storage around bulk allocation or header reservation. The next useful measurement is a production-build CPU profile of the per-field framing loop. That profile should distinguish structural-byte dispatch, coordinate writes, and ownership work before introducing a raw or managed buffer implementation. Any candidate must then improve complete reads across the reference inputs while preserving the current memory bound and both scheduling modes.
