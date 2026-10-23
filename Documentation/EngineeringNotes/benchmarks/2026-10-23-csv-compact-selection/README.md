# Compact storage through row selection

Row selection now reuses `CompactNumericColumn.gathered(at:)` for compact Double columns. The change avoids exporting the entire source column as optional values and keeps the selected result compact. It adds three dispatch lines to `TypedColumn<Double>.vGather(at:)`. The optional-backed path, gather kernel, sort algorithm and worker scheduling remain unchanged.

This is a child experiment of [compact numerical consumers](../2026-10-23-csv-compact-consumers/README.md). It does not promote a production default.

## Comparison versions

- Original is the qualified optional-array CSV reader at `5d1f89a961106104757f2d8d0b8faba79487d100`.
- Prior is the compact reader with specialized exports and direct numerical consumers at `5a3523aaff`.
- Current is `codex/csv-compact-selection` at `9c329614adddfc48f87a31a84214b5737a6d6851`.
- Twin runs the exact current executable again to check measurement variability.

## Complete workflows on reference data

The table reports the 2,075,259-row household dataset with serial column conversion. Each entry lists original, prior and current medians. CPU includes CSV construction, the requested operation and release. Held heap includes the complete selected frame and requested numerical output. Peak RSS captures the process peak before fingerprint validation. All three measure different costs.

| Workflow | CPU original / prior / current, ms | Held heap original / prior / current, MiB | Peak RSS original / prior / current, MiB |
|---|---:|---:|---:|
| read | 237.39 / 243.96 / 246.96 | 285.15 / 176.11 / 176.11 | 420.58 / 312.36 / 312.38 |
| materialize | 240.51 / 288.59 / 288.63 | 285.15 / 397.81 / 397.81 | 420.58 / 407.36 / 407.40 |
| filter-matrix | 265.72 / 319.75 / 270.72 | 25.33 / 25.33 / 18.65 | 420.59 / 431.68 / 312.39 |
| gather-matrix | 258.52 / 308.22 / 263.14 | 23.51 / 23.51 / 17.06 | 420.58 / 431.08 / 312.39 |
| sort-matrix | 456.86 / 530.73 / 447.49 | 396.00 / 396.00 / 310.30 | 737.50 / 851.03 / 511.39 |
| join-matrix | 721.63 / 1805.58 / 1823.77 | 427.67 / 427.67 / 427.67 | 753.28 / 676.75 / 676.77 |
| row-scan | 371.06 / 378.58 / 376.59 | 285.15 / 176.11 / 176.11 | 420.58 / 312.34 / 312.38 |
| lag-matrix | 394.79 / 402.50 / 399.08 | 443.50 / 334.45 / 334.45 | 452.19 / 343.97 / 344.00 |
| matrix | 259.83 / 281.56 / 280.90 | 396.00 / 286.95 / 286.95 | 420.58 / 312.34 / 312.39 |
| batch | 257.73 / 252.04 / 252.20 | 397.81 / 176.11 / 176.11 | 420.58 / 312.34 / 312.38 |

[The full table](results.md) includes both reference datasets, serial and parallel conversion, and all ten workflows. The household data uses the same eleven null tokens for every version, including `?`. The air-quality data uses the same default ten tokens. Both use explicit native schemas. No worker cap or dataset-specific optimization was added.

## What the results support

Across all twelve filtering, gathering and sorting combinations, current uses **8.1% to 20.0% less CPU** and **19.6% to 27.4% less held heap** than prior. Peak RSS savings range from 0.7% to 39.9%, so a smaller retained payload does not imply a large peak reduction in every workflow.

Against the original optional-array reader, current nearly recovers household filtering and gathering CPU while retaining lower memory use. Household sorting uses less CPU in both conversion modes. The original reader remains cheaper for some other workflows, and joining is still approximately 2.5 times its CPU cost. This patch is a useful integration step, not evidence that the compact prototype is ready for general promotion.

The sort case's held malloc bytes differ between the current and twin medians despite identical executables. Those values cover allocator live bytes beyond the logical payload. This experiment does not isolate the reason for that variation. Both control labels pass the fixed CPU and peak-RSS checks, and the raw records retain the difference.

## Operation CPU within the same workers

These medians use the operation stage recorded by each worker. They are not differences between unrelated workflow medians. CSV reading and output release are outside this stage.

| Workflow | Operation CPU original / prior / current, ms |
|---|---:|
| read | 0.01 / 0.00 / 0.00 |
| materialize | 0.03 / 36.13 / 36.09 |
| filter-matrix | 33.00 / 77.34 / 30.29 |
| gather-matrix | 35.13 / 76.96 / 27.32 |
| sort-matrix | 215.60 / 271.64 / 188.56 |
| join-matrix | 482.91 / 1559.09 / 1578.67 |
| row-scan | 135.42 / 132.22 / 132.49 |
| lag-matrix | 161.02 / 155.87 / 155.64 |
| matrix | 19.42 / 24.46 / 24.39 |
| batch | 15.17 / 0.04 / 0.03 |

## Correctness and measurement checks

Three focused regression tests failed before the patch because the selected Double column no longer used compact storage. All three pass afterward. They check empty selections, repeated and unordered rows, bitmap boundaries through 261 output rows, all-missing and all-present columns, NaN payload bits, signed zero and infinities. Public frame filtering, gathering and both sort directions match optional-backed results. Selected Double buffers pass directly to prepared batches, and native Int64 values above 2^53 remain exact.

Release, Debug and Address Sanitizer each pass all 406 dataframe tests, with no failures or skips. Fourteen eager reference checks and fourteen streaming checks pass their pinned types, values, null positions and order. All 160 workflow preflights and 1,280 measured processes match the original output fingerprints. Derived-workflow equivalence is a regression check against the original implementation, not independent mathematical certification.

Eight balanced orders give every label every position twice and every ordered adjacent pair twice. The current and twin labels run the same executable. The fixed policy flags more than 10% median CPU difference or peak-memory differences beyond 5% plus 8 MiB. Flags are retained and disqualify the affected comparison. The audit records `quality_passed=True` and these flags: `[]`.

Tests and builds finished before measurements. AC power was checked at both ends. All comparator clients use identical source compiled against their matching module interfaces and objects. Build receipts verify the imported module paths. Validation fingerprints run outside timing.

## Limits and next work

The change addresses ordinary row gathering. It does not implement compact-aware nullable join gathering or remove materialization from every numeric predicate and sorting helper. The join workflow remains in the panel so its regression stays visible. Read-only, export, matrix and batch workflows remain as controls against collateral changes.

CPU is process user plus system time. RSS and malloc live bytes describe different memory properties. These results do not measure energy, cache activity or FLOPs. No cache mechanism or universal leak-freedom claim follows from them. This experiment has not been pushed or submitted for production integration.

## Evidence and reproduction

- [Full resource results](results.md).
- [Independent audit](audit.json).
- [Comparator source provenance](comparator-provenance.json).
- [Exact experimental patch](changes.patch.gz).
- [Scripts, raw outputs, source snapshots and receipts](experiments.tar.gz).
- [Artifact hashes](artifact-sha256.json).

Restore the recorded prior commit, decompress and apply the patch, restore its pinned dependencies, and update the scripts' machine-specific paths. `verify.py` runs dataframe tests. `validate.py` runs three configurations and builds the module and clients. `measure.py` runs streaming checks, exact preflights, measurements and the audit. The archive excludes executables, caches, result bundles and large reference CSVs. Engineering records stay on `codex/engineering-notes`; only implementation and tests belong to the experiment branch.
