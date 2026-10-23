# Compact storage through nullable joins

Nullable gathering and joined-key construction now read compact Double values directly and keep the output compact. The existing numerical conversion initializer delegates to a shared indexed constructor, which owns the same dense values and lazily allocated validity bitmap. Joins use that constructor instead of exporting an optional source array and allocating optional output.

This is a child of [compact row selection](../2026-10-23-csv-compact-selection/README.md). It keeps join matching, key equality, row ordering, native integer storage and worker scheduling unchanged. It does not promote a production default.

## Comparison versions and scope

- Original is the qualified optional-array reader at `5d1f89a961106104757f2d8d0b8faba79487d100`.
- Prior is compact selection at `9c329614adddfc48f87a31a84214b5737a6d6851`.
- Current is `codex/csv-compact-join` at `a95ef036982e91d87dcddf50f972a64a27f20a74`.
- Twin runs the exact current executable again to check measurement variability.

The focused panel covers complete inner, left, right and outer joins, followed by numerical matrix preparation. Read-only and prepared-batch workflows check neighboring behavior. Both reference datasets run with serial and parallel CSV conversion. The lookup includes the same deliberately unmatched right-side key in every version, so right and outer joins must construct missing payloads. It does not change the reference CSV or its schema. These join workloads have different lookup contents from the preceding experiment, and their timings must be compared within this panel.

## Complete workflows on reference data

The table reports the 2,075,259-row household dataset with serial column conversion. Each entry lists original, prior and current medians. CPU includes CSV construction, the requested operation and release. Held heap includes the result frame and requested numerical output. Peak RSS captures the process peak before fingerprint validation.

| Workflow | CPU original / prior / current, ms | Held heap original / prior / current, MiB | Peak RSS original / prior / current, MiB |
|---|---:|---:|---:|
| read | 241.31 / 243.46 / 245.44 | 285.15 / 176.11 / 176.11 | 421.30 / 312.36 / 312.45 |
| join-inner-matrix | 273.60 / 1372.07 / 273.88 | 0.53 / 0.53 / 0.42 | 422.00 / 313.07 / 313.88 |
| join-matrix | 695.52 / 1813.08 / 459.30 | 427.67 / 427.67 / 318.62 | 753.25 / 676.76 / 534.31 |
| join-right-matrix | 266.53 / 1371.26 / 272.11 | 0.53 / 0.53 / 0.42 | 420.58 / 312.36 / 312.45 |
| join-outer-matrix | 696.28 / 1798.23 / 460.40 | 427.67 / 427.67 / 318.62 | 753.25 / 676.75 / 534.31 |
| batch | 253.60 / 245.12 / 243.79 | 397.81 / 176.11 / 176.11 | 420.58 / 312.36 / 312.45 |

[The full table](results.md) includes both datasets and both conversion modes. The household contract uses the same eleven null tokens in every version, including `?`. The air-quality contract uses the same default ten tokens. Both use explicit native schemas. No worker cap, dataset-specific dispatch or tolerance change was added.

## What improved

Across all sixteen join-plus-matrix combinations, current uses **66.7% to 80.2% less CPU** and **19.4% to 25.5% less held heap** than prior. The household inner and right joins return small subsets and now use roughly the original reader's CPU. Household left and outer joins use about one third less CPU than the original reader while retaining less memory.

These results support preserving compact storage through the join and numerical consumer. They do not establish an unconditional memory win for every consumer, as the compatibility check below shows.

## Retaining optional exports changes the memory result

A second panel measures a left join with the frame retained, first alone and then alongside optional Double arrays requested through `.values`. Every version uses the same client and lookup. The table lists original, prior and current medians for household data with serial conversion.

| Workflow | CPU original / prior / current, ms | Held heap original / prior / current, MiB | Peak RSS original / prior / current, MiB |
|---|---:|---:|---:|
| join-only | 686.21 / 1799.37 / 440.51 | 316.83 / 316.83 / 207.78 | 642.39 / 565.91 / 423.41 |
| join-materialize | 682.12 / 1796.98 / 477.23 | 316.83 / 316.83 / 429.48 | 642.40 / 565.94 / 550.17 |

With only the joined frame retained, current held heap is about **208 MiB**, compared with the original reader's **317 MiB**. Retaining the compact frame and optional exports together raises current held heap to about **429 MiB**, while original remains near **317 MiB** because its exported arrays share existing optional storage. Current still uses less CPU and lower peak RSS in this workload. Its held heap is worse when the caller retains both representations.

This is a real consumer-dependent tradeoff. Numerical consumers can use the compact buffers directly. General promotion still needs an explicit storage and export policy for callers that retain optional arrays. Repeated materialization also remains a compatibility cost. [Full compatibility results](compatibility-results.md) cover both datasets and conversion modes.

All 32 additional preflights and 256 measured processes match their original outputs. The compatibility panel reuses the same tested source and object files. Its three clients were rebuilt only after the first panel finished. Its [audit](compatibility-audit.json) records `quality_passed=True` with these flags: `[]`. Across both panels, 128 workflow preflights and 1,024 measured processes match exactly.

## Operation CPU within the same workers

These medians use each worker's operation stage. They are not differences between unrelated workflow medians. CSV reading and output release are outside this stage.

| Workflow | Operation CPU original / prior / current, ms |
|---|---:|
| read | 0.01 / 0.00 / 0.00 |
| join-inner-matrix | 45.77 / 1140.91 / 45.57 |
| join-matrix | 457.35 / 1567.07 / 216.26 |
| join-right-matrix | 45.26 / 1143.26 / 45.33 |
| join-outer-matrix | 456.34 / 1553.03 / 215.56 |
| batch | 13.60 / 0.03 / 0.03 |

## Correctness and ownership

Two focused regression tests fail before the patch because nullable gathering and coalesced keys lose compact storage. Both pass afterward. They cover empty output and empty sources, missing indices, missing values, repeated and unordered rows, bitmap boundaries, NaN payload bits, signed zero and infinities. A mapped left row has priority even when its value is missing. Either input may use optional or compact storage.

The public join test compares all four join kinds against optional-backed frames, including duplicate, missing and unmatched keys. It checks column order, native types, exact values and null counts, and Int64 identifiers above 2^53. Matrix results agree bit for bit. Joined key buffers pass directly to prepared batches, and subsequent batch mutations preserve the joined frame.

Release, Debug and Address Sanitizer each pass all 409 dataframe tests with no failures or skips. Fourteen eager CSV and fourteen streaming checks pass pinned native types, value and null hashes and ordering. All 96 workflow preflights and 768 measured processes match the original output fingerprints. These derived-workflow checks establish equivalence to the original implementation, not independent mathematical certification.

## Measurement checks and limits

Eight balanced orders give each label each position twice and each ordered adjacent pair twice. The fixed policy flags more than 10% current/twin median CPU difference or peak-memory differences beyond 5% plus 8 MiB. Flags are retained and disqualify affected comparisons. The audit records `quality_passed=True` and these flags: `[]`.

Tests and builds finished before measurements. AC power was checked at both ends. Every comparator client uses identical source compiled against its matching module interface and object. Build receipts verify imported module paths. Full output fingerprints run outside timing. The audit recomputes medians and checks source and binary fingerprints.

CPU means process user plus system time. Malloc live bytes, RSS and logical column payload describe different costs. This panel does not measure energy, FLOPs or cache activity. Address Sanitizer checks do not establish universal leak freedom. Float-key matching still uses the existing join implementation, and optional-array exports remain a compatibility cost. This branch has not been pushed or submitted for production integration.

## Evidence and reproduction

- [Full resource results](results.md).
- [Independent audit](audit.json).
- [Comparator source provenance](comparator-provenance.json).
- [Exact experimental patch](changes.patch.gz).
- [Scripts, raw outputs, source snapshots and receipts](experiments.tar.gz).
- [Artifact hashes](artifact-sha256.json).

Restore the recorded prior commit, decompress and apply the patch, restore pinned dependencies, and update machine-specific paths. `validate.py` runs the three test configurations and builds matching clients. `measure.py` runs stream checks, exact preflights, the main resource panel and its audit. Then `compatibility/run.py` builds and runs the separate optional-export panel and its audit. The archive excludes executables, caches, result bundles and large reference CSVs. Engineering records stay on `codex/engineering-notes`; source changes and tests stay on the experimental branch.
