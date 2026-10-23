# Filtering compact Double columns without optional-array expansion

`TypedColumn<Double>.filteredIndices(matching:)` now reads compact Double values and their validity bits directly. It previously materialized an input-sized `[Double?]` array before evaluating the predicate. The new private collection view reuses the existing floating comparison implementation. It adds no public API, alternative comparison algorithm, parallel worker policy or size threshold.

This experiment follows [the explicit CSV storage choice](../2026-10-23-csv-double-storage-choice/README.md). Optional storage remains the default. Compact storage remains an explicit caller choice, and optional-array exports still materialize when requested. The change removes an internal conversion that the predicate does not need.

## Scope and preserved behavior

The same helper evaluates optional Double arrays, Float arrays and the compact view. It retains integer-threshold normalization above 2^53, IEEE comparisons for valid NaNs and infinities, signed zero, missing-value exclusion and existing null-count shortcuts. Integer and string dispatch remain unchanged. DataFrame filtering already gathers selected rows into compact output columns, so no gather implementation changed.

The direct `AnyColumn.filtered(by:)` method, sorting, unique values and other APIs that explicitly use `.values` are outside this patch. The patch does not claim that every compact-column operation avoids materialization.

The three new test functions pass before the optimization. They establish unchanged comparison results rather than reproduce a wrong answer. They also pass afterward across parameterized bitmap boundaries, empty and uniform columns, random Double bit patterns, mixed integer thresholds, normal and fast public filtering, exact selected value bits, and shared numerical-batch buffers.

## Matched reference workloads

Prior is `2c18d9833a7567c8b2ef6480f4a2467302d7d453`. Current is `3f850cb4ccbc2ef32e4645b5c3b49492596b1d18` on `codex/csv-compact-filtering`. Both versions honor the same optional or compact storage choice for every case. Original is the historical optional reader at `5d1f89a961106104757f2d8d0b8faba79487d100`; it has no compact option and is contextual evidence only. Twin repeats the exact current executable.

The clients use identical source and compiler optimization settings. The historical original lacks the storage option, so its client omits only the conditional code that assigns that option before timing. Each client imports the module interface that matches its linked object. Source, object, interface and executable provenance are recorded in the evidence.

The panel covers the household electricity dataset with 2,075,259 rows and the Aotizhongxin air-quality dataset with 35,064 rows. Each version receives identical explicit schemas, null tokens, source bytes and predicate thresholds. Native integer columns remain Int64. Both serial and native parallel CSV conversion run under both storage choices. There are three workflows:

- `filter-indices` retains the CSV frame and the complete selected index array.
- `filter-matrix` filters the frame and prepares every declared numeric feature as a matrix.
- `filter-materialize` filters the frame and retains optional exports for every Double column.

All predicates use the existing public `greaterThan(3.0)` condition. The datasets have different selection densities. No threshold was selected to improve the candidate's timing. Full row, column, type, value, null, order, index and consumer-output fingerprints match across every worker. This establishes regression equivalence to the qualified reader; unit tests independently check comparison semantics.

## Household results with serial CSV conversion

Each cell gives prior and current medians. Total CPU includes CSV construction, the requested operation and release. Operation CPU excludes CSV construction and release. Held heap includes outputs and any retained representations. Peak RSS includes the process peak through the measured work. The full validation hashes run outside timing.

| Choice and workflow | Total CPU prior / current, ms | Operation CPU prior / current, ms | Held heap prior / current, MiB | Peak RSS prior / current, MiB |
|---|---:|---:|---:|---:|
| optional / filter-indices | 252.03 / 245.51 | 1.03 / 1.03 | 293.08 / 293.08 | 420.61 / 420.62 |
| optional / filter-matrix | 263.16 / 260.71 | 27.30 / 26.66 | 25.33 / 25.33 | 422.00 / 422.05 |
| optional / filter-materialize | 262.35 / 265.45 | 25.77 / 26.43 | 17.41 / 17.41 | 422.00 / 420.64 |
| compact / filter-indices | 255.73 / 256.47 | 5.92 / 1.59 | 184.03 / 184.03 | 312.39 / 312.44 |
| compact / filter-matrix | 259.30 / 254.09 | 28.59 / 23.36 | 18.66 / 18.66 | 312.39 / 312.44 |
| compact / filter-materialize | 265.10 / 260.41 | 28.56 / 23.74 | 24.19 / 24.19 | 312.39 / 312.44 |

[All 24 resource cases](results.md) include both datasets and both conversion modes. A removed temporary need not reduce held memory after the operation. CSV construction can dominate process peak RSS, and small operation-time differences need more caution than large total-CPU changes. CPU, held heap, peak RSS and elapsed time remain separate measurements.

## Interpretation

For the household compact predicate, operation CPU falls from 5.92 to 1.59 ms with serial CSV conversion and from 5.98 to 1.46 ms with parallel conversion. That is 73% to 76% less predicate CPU. The complete filter-and-matrix operation uses about 17% to 18% less CPU after parsing, while the full CSV-to-matrix workflow uses about 1.5% to 2% less CPU in this panel.

Air-quality predicates use about 43% to 45% less operation CPU. Their complete matrix operations improve by about 3% to 6%. Optional exports on that smaller dataset show little whole-workflow change. Optional-storage controls move in both directions by small amounts, so small full-workflow differences are not a portable guarantee.

Held heap is unchanged between prior and current in every matched case. Peak RSS is essentially unchanged. The removed optional array was temporary. Similar process peaks are consistent with CSV construction dominating memory, but this panel does not record a separate predicate-only peak. The measured benefit is lower CPU for compact predicates without a new retained representation. This supports keeping the local change, but does not establish a broad parsing or process-memory improvement.

## Validation and measurement controls

Release, Debug and Address Sanitizer each pass all 416 dataframe test functions without failures or skips. Twenty-eight eager and twenty-eight streamed reference reads pass exact native-type, value, null and ordering checks. All 96 workflow preflights and 768 measured fresh processes match their complete output fingerprints.

Each of the 24 cases has eight fresh processes for every label. Eight balanced orders place each label in each position twice and each ordered adjacent pair twice. The frozen quality policy flags current/twin median CPU differences above 10%, or peak RSS differences above 5% plus 8 MiB. Affected comparisons remain unqualified. The audit records `quality_passed=True` and these flags: `[]`.

Builds and tests finish before accepted resource measurements. AC power is checked at both ends. The audit recomputes medians from raw records and verifies balanced ordering, exact outputs, effective storage choices, executable hashes, module imports and source hashes. Identical-binary controls check repeatability within this panel; they do not eliminate every source of machine variation.

CPU means process user plus system time. These data do not measure energy, FLOPs, cache misses or SRAM use. Address Sanitizer does not prove universal leak freedom. This experiment remains local, with no push or PR.

## Evidence and reproduction

- [Resource results](results.md).
- [Independent audit](audit.json).
- [Comparator provenance](comparator-provenance.json).
- [Exact patch from the prior branch](changes.patch.gz).
- [Scripts, sources, raw records and receipts](experiments.tar.gz).
- [Artifact hashes](artifact-sha256.json).

Restore the recorded prior commit, decompress and apply the patch, and restore pinned dependencies. Update machine-specific paths in the scripts. Run `verify.py Release --label final-release`, then `validate.py` for Debug, Address Sanitizer and matched-client builds. Run `strict-check.py`, `run-panel.py preflight`, `run-panel.py measurement`, and `audit.py` in that order. The archive excludes executables, dependency caches, result bundles and large reference CSVs.

Source and tests stay on the experiment branch. This report and its evidence stay on `codex/engineering-notes`.
