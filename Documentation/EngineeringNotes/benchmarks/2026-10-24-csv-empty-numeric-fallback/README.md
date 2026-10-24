# Empty numeric CSV fields avoid the string fallback

Retain the shared-fallback implementation locally as `31c0f958c843cb60279a74aff2b55427ba39abec` on `codex/csv-empty-numeric-fallback`, based on the [retained structural-scanner change](../2026-10-24-csv-structural-mask/README.md) at `2a8f1230667eaa86cd72a67b5e78b2b3830f2c23`. No branch was pushed and no PR was opened. Engineering evidence remains on `codex/engineering-notes`.

The demonstrated benefit is narrow and substantial. Raw empty numeric fields with a custom null list containing only `?` use about 98% less CPU in the matched diagnostic. Ordinary real-data workflows are close to neutral, with nominal aggregate CPU reductions of about 1% in one qualified panel. No universal CSV speedup or new memory reduction is established.

## Remove unnecessary work without changing null policy

A custom null list replaces the defaults. If it excludes the empty string, a raw empty field is an invalid numeric value. An explicit numeric schema converts it to nil. Inference must reject that numeric candidate and preserve the original text when it falls back to a String column. Calling it missing unconditionally would change the API contract.

Previously, both numeric decoders could construct a String and invoke whitespace trimming before arriving at nil. A private generic function now handles this fallback for Int64 and Double. It returns nil for a zero-length field before constructing a String. The existing decoder performs null matching first and maps nil to invalid for inference. Recognized missing fields keep their existing classification.

`@inline(never)` keeps this conversion outside the inlined numeric decoders. Successful byte parsing still returns directly. The compiler emits two specialized fallback functions. Quoted-empty and whitespace-only fields retain their original conversion behavior; their performance is not optimized here. No public API, storage default, package minimum, framing rule, numerical parser, or concurrency policy changes.

## Targeted mixed queue

Six fixed cases use 1,003 rows and 16 numeric columns. They cover empty Int64 and Double fields, mixed valid/empty/custom-null/quoted/whitespace numeric fields, valid Doubles, and recognized empty defaults. Each queue has 384 reads and four concurrent callers. Eight rotated rounds include an identical-binary twin for each build and storage mode, for 24,576 completed reads and 48 full-output checks.

| Case | Storage | Parent CPU ms/read | Candidate CPU ms/read | CPU change |
| --- | --- | ---: | ---: | ---: |
| empty-double | optional | 47.827 | 0.567 | -98.82% |
| empty-double | compact | 49.542 | 0.578 | -98.83% |
| empty-int | optional | 27.961 | 0.522 | -98.13% |
| empty-int | compact | 27.530 | 0.524 | -98.10% |
| mixed-double | optional | 3.914 | 0.605 | -84.55% |
| mixed-double | compact | 3.849 | 0.600 | -84.41% |
| mixed-int | optional | 3.020 | 0.513 | -83.01% |
| mixed-int | compact | 3.079 | 0.501 | -83.74% |

These are operation CPU costs inside the mixed queue. Valid-only/default-null jobs also appear cheaper while running alongside the repaired empty-field jobs. That observation does not establish faster numeric parsing. Separate isolated controls remove those expensive neighbors.

| Isolated control | Storage | Operation CPU change |
| --- | --- | ---: |
| valid-double | optional | +0.19% |
| valid-int | optional | +0.56% |
| empty-default | optional | +0.16% |
| valid-double | compact | -1.58% |
| valid-int | compact | -0.41% |
| empty-default | compact | -1.30% |

The isolated panel completes 49,152 reads and 24 full-output checks. CPU is close to the parent across these controls. All fixtures and expected native-bit fingerprints reproduce exactly with `generate-fixtures.py`.

## Complete real-data workflows

The reference panel completes 8,192 jobs in 64 queues, with four callers, 128 jobs per queue, and 32 full-output checks. It uses 35,064 Aotizhongxin observations and 2,075,259 household electricity records. Each input is read alone or read, stably sorted, and converted to its numeric matrix.

| Storage | Parent CPU ms/job | Candidate CPU ms/job | CPU change | Throughput change | Peak RSS MiB, parent → candidate |
| --- | ---: | ---: | ---: | ---: | ---: |
| optional | 189.75 | 188.21 | -0.81% | +0.30% | 3501.0 → 3500.7 |
| compact | 186.66 | 184.87 | -0.96% | +0.62% | 2511.0 → 2510.3 |

Both reference null lists include the empty string, so raw empty fields already exit through recognized-null handling. This panel is primarily a regression check for the changed decoder code, not direct evidence that bypassing empty-string conversion accelerates these inputs. Some individual cases move slightly in either direction. One panel does not establish a general 1% gain.

The final diagnostic, isolated-control, and reference panels pass the unchanged 10% twin CPU/wall limits and 5% plus 8 MiB-per-caller RSS limits. Every conservative sum of kernel-reported worker peaks remains below 4 GiB. RSS is effectively unchanged. Raw accounting is recomputed independently of the reported medians.

## The first implementation remains in the record

The first candidate put four empty checks directly in the inlined decoders. Its qualified diagnostic also removes most empty-field CPU work. Its real-data panel, however, measures 1.52% more charged CPU with optional storage and 1.10% more with compact storage. That version is not retained.

A first short diagnostic fails repeatability, with three twin CPU/wall flags. It is preserved as unqualified. A conservative cost forecast allows a longer diagnostic; no tolerance changes were made. The forecast is an estimate, not a runtime guarantee.

Fifteen matched append/appendRows specializations have symbol-to-next-symbol extents totaling 37,404 bytes in the parent, 37,040 in the direct-guard candidate, and 35,140 in the shared-fallback candidate. The first candidate's functions did not simply grow. These code-size observations do not prove why its timing differs, measure instruction-cache utilization, or establish a causal cache explanation.

## Correctness, build identity, and scope

The three new semantic test functions pass against the unchanged parent before implementation. They protect missing-versus-invalid classification, explicit-schema nil values, quoted-empty and whitespace behavior, both Double storage modes, and preservation of late empty text after the inference sample. There is no failing-before semantic test because the original results were correct. The reproduced defect is unnecessary resource consumption.

All 440 dataframe tests pass in Debug and all 440 pass in Release, with no failures or skips. The baseline build succeeded; an initial local runner path replacement failed before test execution, then the corrected runner executed the focused suite successfully. Both runner records are preserved. No full MLX suite, hosted CI, or coverage result is claimed.

Independent fingerprints check every output column's type, values, native numeric bits, null counts, and matrix output before and after each qualified panel. Timed work receives shape/type checks; hashing is outside timing. All workers use a complete explicit schema. Inference semantics are tested, but inference speed is not measured.

All 51 parent source hashes match the scanner commit. Both candidates have the same dependency hashes and reviewed worker source; only `CSVColumnConversion.swift` differs among measured library sources. The final local commit maps to the exact source hashes recorded during compilation. Historical build heads and dirty-source receipts remain unchanged.

Timing panels run sequentially, without experiment compilation, tests, or native sampling. Native test builds start after timing completes. AC power and recorded power settings are unchanged within each panel. CPU parallelism is native; the four callers are not four pinned cores. CPU measures summed worker user/system time plus measured controller CPU, including cleanup. It is not FLOPs, normalized P/E-core work, or energy. Sampled RSS can miss short peaks and double-count shared pages. No GPU, Neural Engine, cold disk, or cache efficiency claim follows.

## Reproduce and inspect

[Summary](summary.json), [artifact hashes](artifact-sha256.json), and [experiment archive](experiment.tar.gz) preserve source snapshots, source patches, compiler receipts, fixture generation, independent fingerprints, all seven panels including the unqualified short panel, raw job/CPU/RSS records, code-size inspection, and test summaries/logs. Executables, objects, module caches, raw CSVs, and xcresult bundles are excluded.

Restore the recorded source and matching dependencies, remap absolute paths, regenerate diagnostic inputs, and obtain the reference files matching the recorded SHA256 values. Build immutable workers with `Benchmarks/CPUThroughput/build.py`. Run `fallback-diagnostics.py`, `fallback-controls.py`, and `fallback-reference.py` sequentially in fresh directories, then recompute each with `audit-workflows.py`. Run the preserved native validation script separately from timing. The measured host/compiler/deployment settings are in the receipts; no other host or older runtime result is implied.
