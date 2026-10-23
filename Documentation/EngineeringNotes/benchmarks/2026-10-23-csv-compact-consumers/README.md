# Compact numerical consumers

This experiment addresses the [first compact CSV prototype's](../2026-10-23-csv-compact-double-prototype/README.md) optional-array export penalty and unnecessary numerical conversion. It keeps the dense values and validity bitmap, exposes the existing getter body to client specialization, and lets numerical consumers use the compact buffers directly. No production default or public storage policy is promoted.

## Two changes with separate evidence

### Let the client compiler specialize the export loop

The optional-array getter originally remained generic at a separately compiled call site. The producer already contained a Double specialization, but the client called the generic getter. The archived optimized client SIL records that call. After `@inlinable` exposes the unchanged body, the client calls a concrete Double specialization instead.

The isolated diagnostic changed no loop, schema, storage representation or null policy. On the smaller air-quality export workflow, balanced diagnostic runs measured approximately **42.0 ms CPU before versus 9.9 ms after**, compared with **8.8 ms for the original optional-array reader**. Exact output fingerprints match. These diagnostic timings support the mechanism; use the complete resource panel below for qualification.

Commit `764c01bc6d` contains only this change and the storage metadata visibility required by the optimizer. Its dataframe Release suite passed 399 tests. The attributes do not remove the optional-array allocation or create a compatibility cache. They make the same loop available for concrete client optimization. This is not an ABI compatibility qualification for a separately distributed binary library.

### Remove optional-array conversion from numerical preparation

The next change adds an internal compact view for Double columns and a compact case in the existing private feature-column enum. It reuses `CompactNumericColumn` rather than introducing another numerical storage implementation.

- `prepareNumericBatch` retains existing dense value and validity arrays through Swift copy-on-write.
- Numerical matrix writers read dense values and validity directly. Missing-value rejection still considers the selected rows, with the existing error precedence.
- Full, present single-column matrix and target-vector exports can share the existing value array. Nullable inputs or row selections use the existing packing contract.
- Both matrix orders, duplicate columns, repeated row selections, valid NaNs, nil, signed zero and Int64 conversion behaviour remain covered.

Four focused ownership tests first failed on the copying implementation. They then passed after integration. The tests compare actual backing-buffer addresses, not just equal values, and verify that updating a prepared batch leaves the source dataframe unchanged. They also compare packed values bit for bit with the optional-backed implementation.

The integrated head is `5a3523aaffa06c23acbb0ecfeb5cc118f6727f00` on local branch `codex/csv-compact-consumers`, based on `6af4b8f071443779964ce77ac0856c48127657c6`. The preceding compact prototype and qualified CSV candidate remain separate branch heads. No source work is pushed.

## Complete workflow comparison

The panel compares the original optional-array reader, the first compact prototype, and the integrated code using identical client source. A fourth label runs the exact integrated binary again as a control. Each client imports the interface matching its linked object. Numerical preparation is included in the timed interval, along with CSV reading, the requested operations and release. Full output validation runs outside timing, after held and peak memory counters are captured.

The complete household and Aotizhongxin references retain their recorded schemas, values, null positions, native types and read scope. Household uses eleven declared null tokens including `?`; it is not the ten-token Swift default. Both existing CSV column-conversion policies are tested. Serial does not impose a single-core budget on the rest of the workflow. All comparisons use CPU execution with native scheduling.

Forty input/policy/workflow combinations cover reading, optional-array export, filtering, gathering, sorting, joining, boxed row scanning, lagged matrices, direct matrices and prepared batches. Four labels run in eight balanced orders. Every label occupies each position twice, and the order design balances adjacent label pairs. This gives **1,280 measured fresh processes**, after 160 exact workflow preflights. All final frame, matrix, exported-array, prepared-batch and row-scan bit fingerprints match the original reader.

The same power and quality rules apply throughout. AC power is checked before and after the panel. Builds, tests and profiling do not overlap accepted timings. Control limits remain 10% for median CPU and 5% plus 8 MiB for peak memory. The control result is **passed**. Flagged cases, if any, remain unqualified. Eight repetitions and the balanced four-label design are frozen for this experiment; this is a new panel, not an extension of the previous three-label twelve-repetition run.

## Household serial results

Values in each cell are **original / first compact prototype / integrated**. CPU is process user plus system time, not elapsed time or FLOPs. Held heap is live malloc allocation size. Peak RSS includes clean mapped input and allocator-retained pages, so it is not private retained storage or total system RAM use.

| Workflow | CPU, ms | Held heap, MiB | Peak RSS, MiB |
|---|---:|---:|---:|
| read | 244.26 / 263.01 / 261.42 | 285.15 / 176.11 / 176.11 | 420.58 / 312.41 / 312.39 |
| materialize | 242.65 / 1372.32 / 285.45 | 285.15 / 397.81 / 397.81 | 421.28 / 407.41 / 407.38 |
| matrix | 249.05 / 295.69 / 266.73 | 396.00 / 286.95 / 286.95 | 420.58 / 518.25 / 312.36 |
| batch | 247.94 / 297.80 / 243.37 | 397.81 / 288.76 / 176.11 | 420.58 / 518.41 / 312.36 |
| lag-matrix | 396.04 / 431.02 / 400.52 | 443.50 / 334.45 / 334.45 | 452.22 / 565.81 / 343.98 |
| sort-matrix | 436.84 / 495.77 / 497.89 | 396.00 / 396.00 / 396.00 | 737.48 / 851.06 / 851.03 |
| join-matrix | 709.52 / 1846.36 / 1827.74 | 427.67 / 427.67 / 427.67 | 753.28 / 676.78 / 676.75 |

The measured operation-stage CPU medians below exclude CSV reading and release. They come from each worker's actual stage counters, not subtraction of unrelated case medians. Separate stage medians need not sum to the median total.

| Operation | CPU original / first prototype / integrated, ms |
|---|---:|
| materialize | 0.03 / 1119.23 / 35.01 |
| matrix | 16.07 / 50.07 / 21.91 |
| batch | 13.84 / 47.69 / 0.03 |
| lag-matrix | 156.69 / 182.89 / 155.60 |
| join-matrix | 475.71 / 1591.66 / 1578.79 |

The matrix operation is faster than the first prototype but still costs more CPU than the original optional-backed operation. Prepared-batch construction mostly becomes buffer ownership transfer. Optional-array export still does real allocation and element construction even after specialization removes most of its former CPU cost. Join materialization remains a separate, substantial regression and is not fixed by the new numerical path.

[Complete results](results.md) include both reference datasets and both conversion policies. Small differences are descriptive observations. These results do not establish energy consumption, cache utilization, GPU/NPU performance or a universal cross-library ranking. Python libraries are not rerun in this panel.

## Validation and remaining work

The integrated dataframe suite passes **403 tests each in Release, Debug and Address Sanitizer**, with no failures or skips. Fourteen eager reference reads and fourteen streamed-reference checks preserve the existing exact contracts. The new test file contains four focused cases and remains separate from the preceding prototype tests.

Optional-array export still creates a second representation when the caller retains both. Filter, gather, sort and join outputs can still fall back to optional arrays. Faster export and direct numerical access do not by themselves justify switching every caller to dense storage. Further work must evaluate native selection outputs and make the eventual storage/performance policy explicit.

Keep the two changes as experimental commits. Resource improvements must be assessed by workload against CPU time, held allocations and peak memory separately. A lower retained payload does not automatically imply lower peak memory or less CPU work.

## Evidence and reproduction

- [Full resource results](results.md).
- [Independent audit](audit.json).
- [Experimental patch](changes.patch.gz), compressed without changing its bytes.
- [Specialization proof](specialization-proof.json), with optimized client SIL references and fingerprints.
- [Experiment archive](experiments.tar.gz), including scripts, source snapshots, input contracts, build and test receipts, the red/green test logs and raw outputs.
- [Artifact hashes](artifact-sha256.json).

Restore the recorded prototype base, decompress and apply the patch, rebuild its pinned dependencies, and update the scripts' machine-specific roots. The archive excludes native binaries, caches, result bundles and large reference CSVs. `verify.py` runs the restricted dataframe scheme. `build.py` builds the modified module. `prepare-panel.py` builds all comparator clients against the matching interfaces. `run-panel.py` performs preflights and measurements. `audit.py` recomputes medians, verifies source fingerprints and enforces the original control thresholds. Engineering records remain on `codex/engineering-notes` and source changes remain on the experimental branch.
