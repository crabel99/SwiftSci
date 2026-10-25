# Normalized empty CSV fields skip numeric conversion

Retain `575f2f63cbd3c35c0611ba3a977b066b2e4fd390` locally on `codex/csv-normalized-empty-fallback`, based on [the raw-empty optimization](../2026-10-24-csv-empty-numeric-fallback/README.md) at `31c0f958c843cb60279a74aff2b55427ba39abec`. Nothing is pushed and no PR is opened. Engineering records remain on `codex/engineering-notes`.

The change adds an empty check to the existing private numeric fallback after CSV String normalization. Quoted-empty and ASCII space/tab-only fields with custom null tokens use about 94–95% less operation CPU in the targeted panel. Ordinary reference workflows are effectively neutral. Nonempty control timings depend on the tested link layout, so this is not a universal efficiency claim.

## Remove numeric conversion of an already empty String

The raw-empty shortcut stays first. For a nonzero-length field, the existing parser strips outer quotes and ASCII whitespace. If the resulting String is empty, the new guard returns nil before invoking numeric conversion and its whitespace trimming. Nonempty text still uses the original conversion. Unicode whitespace handling and numeric grammar are unchanged.

Null matching still precedes fallback. An explicit numeric schema maps both missing and invalid values to nil. Inference must keep an undeclared normalized empty invalid, then retain a text column. The patch adds no policy, public API, storage change, parallelism change, or new normalization rule.

## Targeted resource result

Four fixed inputs use 1,003 rows and eight numeric columns: quoted-empty and ASCII space/tab-only Int64 and Double fields. Both builds receive the same full schema and custom null set containing only `?`. Eight rotated rounds include a twin for every binary/storage condition, with four callers and 256 reads per queue. The panel completes 16,384 reads and 32 full-output checks.

| Input | Storage | Parent operation CPU ms/read | Candidate operation CPU ms/read | Change |
| --- | --- | ---: | ---: | ---: |
| quoted-double | optional | 6.925 | 0.380 | -94.52% |
| space-double | optional | 7.875 | 0.363 | -95.38% |
| quoted-int | optional | 6.856 | 0.368 | -94.63% |
| space-int | optional | 7.650 | 0.361 | -95.27% |
| quoted-double | compact | 7.485 | 0.390 | -94.79% |
| space-double | compact | 7.996 | 0.376 | -95.30% |
| quoted-int | compact | 6.648 | 0.366 | -94.49% |
| space-int | compact | 7.604 | 0.360 | -95.27% |

A separate mixed panel rotates normalized empties, valid numbers, quoted values and recognized custom nulls. It completes 8,192 reads and 16 full-output checks. Charged queue CPU falls 86.93% with optional storage and 86.54% with compact storage. These queue figures include controller work; the table measures worker operation CPU.

## Nonempty controls expose a layout dependency

The five correctly completing controls cover the retained raw-empty path, ordinary Doubles and Int64 values, long decimals, and Unicode-padded numeric text. Each control panel completes 20,480 reads and 40 full-output checks. A reversed-order repeat investigates increases in the first panel instead of discarding them.

| Input | Storage | Original operation CPU change | Reversed order | Equal stub alignment |
| --- | --- | ---: | ---: | ---: |
| raw-double | optional | -1.12% | +0.03% | +0.93% |
| valid-double | optional | +0.84% | +0.41% | -0.64% |
| valid-int | optional | -1.22% | +1.22% | +0.24% |
| fallback-double | optional | +3.92% | +6.86% | +1.64% |
| unicode-double | optional | +3.52% | +2.28% | -4.19% |
| raw-double | compact | -1.09% | -0.21% | +1.40% |
| valid-double | compact | +0.78% | +0.17% | +0.04% |
| valid-int | compact | -0.91% | +0.34% | +1.81% |
| fallback-double | compact | +2.47% | +5.52% | -0.33% |
| unicode-double | compact | +1.70% | +1.51% | -0.34% |

The long-decimal conversion returns before reaching the changed guard. Disassembly shows the same 131 instructions in its specialization, apart from two runtime-call displacements. Their destination stubs move by 60 bytes in the ordinary links.

A diagnostic reuses the exact library objects and links both binaries with the runtime-stub section aligned to the measured 16 KiB host page size. Both stub sections begin at the same address. The linked long-decimal instruction bytes and call addresses then match exactly. The earlier consistent long-decimal/Unicode penalty does not persist in that link configuration.

The observed penalty is not stable across these two link configurations. Its exact internal cause remains unproven, and the result does not guarantee behavior in other applications. The alignment flags are diagnostic only. No production linker option is changed, and the unfavorable ordinary-link measurements remain in the record.

## Complete reference workflows

The full reference panel completes 8,192 jobs in 64 queues with 32 full-output checks. It reads 35,064 Aotizhongxin observations and 2,075,259 household electricity records, alone or followed by stable sorting and numeric matrix construction. Each queue has 128 jobs and four native CPU callers.

| Storage | Charged CPU change | Throughput change | Peak RSS MiB, parent → candidate |
| --- | ---: | ---: | ---: |
| optional | +0.14% | -0.18% | 3507.7 → 3505.0 |
| compact | -0.51% | +0.06% | 2510.9 → 2513.5 |

These inputs recognize empty strings as null, so their empty fields already exit before this private fallback. The panel checks ordinary-operation regressions. It does not establish that the targeted shortcut accelerates those datasets. No new memory reduction is demonstrated.

## Existing integer crash remains failed conformance

The original sixth control, an out-of-range Int64 token, crashes during the unchanged parent's preflight. It never enters timing. Independent replay confirms the same crash on both builds. A one-cell public CSV reproduction also crashes on valid `Int64.min` and on values just above or below the representable range. `Int64.max` passes.

The fault is in the unchanged `VectorizedByteParsers.parseInt`, which accumulates positive magnitude with checked arithmetic before applying the sign. The magnitude of `Int64.min` cannot fit. Crash traces identify that function. The [defect record](integer-overflow.md) and red-capable process-isolated reproducer preserve the expected results and failures. The case is excluded only from timing, not accepted as passing. Repair belongs in a separate branch and regression commit.

## Validation and reproducibility

All 440 dataframe tests pass in Debug and all 440 pass in Release, with no failures or skips. Existing tests now parameterize raw-empty, quoted-empty and ASCII whitespace forms for missing-versus-invalid classification and late inference fallback. No failing-before semantic claim is made; the original values were correct. The integer boundary reproducer still fails. No full MLX suite, hosted coverage or CI result is claimed.

The first short identical-binary screen fails the unchanged 10% CPU twin limit. A budgeted longer baseline passes. All subsequent completed panels pass the recorded 10% twin CPU/wall and 5% plus 8 MiB-per-caller RSS controls. Every conservative sum of worker kernel peaks stays below 4 GiB. The separate failed integer-control preflight is retained alongside completed panels.

Audits recompute 512 completed queues, 112,640 timed jobs and 264 full-output checks. Independent native-bit hashes include dtypes, values, null counts and matrices. Fixtures and expected fingerprints regenerate exactly. Workers always use full schemas; inference performance is not measured. Both binaries share dependency hashes and worker source, and only `CSVColumnConversion.swift` differs among measured library sources. Build receipts retain their original heads and exact dirty-source hashes, mapped to the later commit.

Panels, diagnostic link builds and native tests run sequentially. AC and recorded power settings remain unchanged within panels. CPU parallelism is native; callers are not pinned cores. Charged CPU is worker user/system time plus measured controller CPU and cleanup, not FLOPs or energy. Sampled RSS can miss brief peaks or count shared pages repeatedly. No GPU or Neural Engine result is implied.

[Summary](summary.json), [hash inventory](artifact-sha256.json), and [experiment archive](experiment.tar.gz) contain source snapshots, normal and diagnostic link receipts, all completed/unqualified/failed outcomes, raw accounting, independent fingerprints, expanded tests, disassembly and the integer reproducer. Binaries, objects, caches, raw CSVs and xcresult bundles are excluded. Restore the recorded source/dependencies/reference-file hashes, remap paths, regenerate fixtures, and run the preserved panel/audit tools in fresh directories. Run native validation separately from timing. The crash reproducer should exit nonzero until its separate repair lands.
