# Deferring Double sort-cache allocation

The allocation trace identifies a source of oversized numeric outputs. The adaptive Double sorter reserves a full array of 16-byte row/value tuples before deciding whether to use radix sort. When it switches, that discarded allocation can become an oversized 8-byte key buffer and then an oversized Double output column.

The candidate chooses the path before allocating comparison caches and reuses the existing comparison helper afterward. It reduces allocation capacity and improves some disordered-input CPU measurements. It also adds CPU work on already-ordered inputs. This remains a local trial, not a general replacement for the previous qualified checkpoint.

This study follows [compact Double sorting](../2026-10-23-csv-compact-sorting/README.md).

## Traced allocation reuse

A separate instrumented module records array data addresses, counts, capacities and element strides. The baseline trace has these events at the same data address:

1. The adaptive cache reserves capacity for 2,050,046 tuples of 16 bytes each.
2. It writes only 75,425 tuples before selecting radix sort and releasing the cache.
3. The radix key array reuses that address with capacity for 4,100,092 UInt64 values, although it contains only 2,075,259 keys.
4. A gathered Double column reuses the address again, retaining that capacity for only 2,075,259 values.

The trace establishes that reuse chain in the instrumented process. Logging can affect allocation behavior, so its timings are excluded. Its complete numerical and row-order fingerprints match the uninstrumented baseline. The earlier uninstrumented capacity diagnostics independently found the same oversized output capacity.

## Candidate and contracts

Current is `42f0633fd52e8e6ece961465880050ebc16db60e` on `codex/csv-sort-buffer-allocation`, based on `91c0ff09b7810b57cabdd953f8bc67791b1008f5`. The candidate removes speculative tuple and missing-row cache allocation from the run-detection pass. It retains the sparse-column, run-count and radix-digit policies. Ordered and nearly ordered inputs reuse the existing comparison sorter after detection. NaNs retain the existing comparison fallback, including NaNs encountered after radix dispatch.

The change removes nine production lines overall. Two small test functions exercise stable ordered runs and NaNs before or after dispatch in both optional and compact storage. They pass before and after the change. Existing tests cover signed zero, infinities, missing values, bitmap boundaries, stable ties, both directions, public sorting and numerical handoff.

## Matched real-data comparison

Prior and current both honor the same optional or compact storage choice. Original is the fixed optional reader at `5d1f89a961106104757f2d8d0b8faba79487d100` and supplies historical context. Twin repeats the current executable. All clients use identical workload source and optimization flags, with matching module interfaces and linked objects. Only the historical client omits the unsupported storage-option assignment before timing.

The real-data panel uses household electricity observations with 2,075,259 rows and Aotizhongxin air-quality observations with 35,064 rows. Explicit native schemas, null tokens, input bytes and output order match. Both serial and native parallel CSV conversion run under both storage choices. Sorting indices, sorting into a numerical matrix, and sorting into retained optional exports have separate cases.

The table shows household data with serial CSV conversion. Each cell gives prior and current medians. Total CPU includes construction, operations and release. Operation CPU excludes construction and release. Complete output validation runs outside timing.

| Choice and workflow | Total CPU prior / current, ms | Operation CPU prior / current, ms | Held heap prior / current, MiB | Peak RSS prior / current, MiB |
|---|---:|---:|---:|---:|
| optional / sort-indices | 287.76 / 288.26 | 49.08 / 48.54 | 301.00 / 301.00 | 421.33 / 420.67 |
| optional / sort-matrix | 433.24 / 440.00 | 200.98 / 200.40 | 396.00 / 396.00 | 737.52 / 737.60 |
| optional / sort-materialize | 420.70 / 417.01 | 183.71 / 179.81 | 285.16 / 285.16 | 626.66 / 626.73 |
| compact / sort-indices | 299.12 / 300.92 | 53.98 / 49.04 | 191.95 / 191.95 | 312.42 / 312.47 |
| compact / sort-matrix | 438.84 / 441.64 | 187.66 / 180.20 | 302.39 / 286.95 | 503.98 / 503.56 |
| compact / sort-materialize | 453.12 / 448.47 | 197.65 / 190.74 | 413.25 / 397.81 | 551.51 / 551.28 |

[All 24 real-data cases](results.md) record the full panel. Held heap measures live malloc allocation sizes, including spare capacity. RSS measures resident pages and is a different cost. A smaller allocation capacity does not establish an equal physical-RAM saving. The capacity diagnostics record actual buffer counts and capacities separately from timing.

For compact household data, the matrix and export workflows retain 15.4375 MiB less malloc capacity. The capacity diagnostics find no oversized numeric output buffers in the candidate for these disordered workflows. Peak RSS remains nearly unchanged, so the capacity reduction does not demonstrate the same amount of physical-RAM relief.

Household compact index sorting falls from 53.98 to 49.04 ms of operation CPU, about 9%. Its full CSV-and-sort CPU does not improve in this panel. Matrix and export operation CPU also fall, while full construction-and-consumer results are mixed. These scopes must remain separate.

## Ordered-input controls expose the tradeoff

The second panel measures sorting and index release with the input frame retained. CSV construction and full output validation are excluded. It covers 32,768 and 1,000,000 values in ascending, descending, nearly ordered and pseudorandom arrangements, under both storage choices. Values have repeated ties and exact binary-fraction offsets. Stable expected permutations and value fingerprints come from an independent fixture generator.

For one million ascending values, optional storage rises from 4.503 to 5.318 ms of CPU, about 18%. Compact storage rises from 4.120 to 4.944 ms, about 20%. Nearly ordered cases also use more CPU. Compact pseudorandom sorting improves from 14.590 to 13.978 ms, about 4%, while optional pseudorandom sorting is essentially unchanged.

[All 16 shape-control cases](shape-results.md) preserve the small and large results. These controls prevent the real-data memory result from becoming an unconditional efficiency claim. The separate detection pass has a measurable CPU cost when comparison sorting still follows it.

The candidate is not promoted. A follow-up can use the detector's proof of monotonic order to produce a stable permutation directly, then recheck nearly ordered workloads. That is a separate development step. This trial establishes the allocation cause and the cost of moving detection ahead of cache creation.

## Validation and controls

Release, Debug and Address Sanitizer each pass all 422 dataframe test functions without failures or skips. Twenty-eight eager and twenty-eight streamed reference reads pass exact type, value, null and order checks. The real-data panel has 96 preflights and 768 measured fresh processes. The shape panel has 64 preflights and 512 measured fresh processes. Eighteen separate capacity diagnostics are excluded from accepted timings.

Every measured output matches its complete expected fingerprints. Both panels use eight fresh processes per label and case. Eight balanced orders place each label in each position twice and each ordered adjacent pair twice. The frozen policy flags current/twin median CPU differences above 10%, or peak RSS differences above 5% plus 8 MiB. Flagged results remain unqualified. Real-data quality records `quality_passed=true` with these flags: `[]`. The separate [shape audit](shape-audit.json) records shape-control quality.

Tests, fixture preparation and builds finish before accepted measurements. AC power is checked at both ends. Audits recompute medians, verify balanced ordering, compare exact output fingerprints, check input and executable hashes, and verify matching module imports. No worker caps, tolerance changes or new dataset-specific thresholds are added.

CPU means process user plus system time. These results do not measure energy, FLOPs, cache misses or SRAM activity. Address Sanitizer does not prove universal leak freedom. Small end-to-end differences can include construction variation and must not all be assigned to the sort change.

## Evidence and reproduction

- [Real-data results](results.md).
- [Shape-control results](shape-results.md).
- [Main audit](audit.json) and [shape audit](shape-audit.json).
- [Capacity summaries](capacity-summary.json).
- [Comparator provenance](comparator-provenance.json).
- [Source patch from the prior checkpoint](changes.patch.gz).
- [Scripts, source snapshots, trace, raw records and receipts](experiments.tar.gz).
- [Artifact hashes](artifact-sha256.json).

Restore the recorded commits and pinned dependencies. Build historical modules from their recorded source and compiler receipts. The trace tool was run against the prior checkpoint before the candidate change. Decompress and apply the patch, update machine-specific paths, and run Release validation with `verify.py`. Run `validate.py` for Debug, Address Sanitizer, reference clients and generated shape controls. Run `measure.py` for exact input checks, preflights, both balanced panels, capacity diagnostics and audits.

The archive excludes executables, dependency caches, result bundles and large CSV files. Source and tests remain on the local trial branch. This record remains on `codex/engineering-notes`. Nothing is pushed or submitted as a PR.
