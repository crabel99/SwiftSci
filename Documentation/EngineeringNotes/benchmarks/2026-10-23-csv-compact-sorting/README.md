# Sorting compact Double columns without optional-array expansion

Compact Double columns now pass their values and validity bits directly to the existing Double sort. The prior implementation first materialized an input-sized `[Double?]` array. The same private collection view now supports both filtering and sorting, and the existing comparison and radix helpers accept either representation.

This experiment follows [compact predicate filtering](../2026-10-23-csv-compact-filtering/README.md). The public CSV storage choice remains unchanged. Optional arrays remain the default, and compact storage remains an explicit caller choice.

## Scope and contracts

The patch changes the input representation supplied to the sort helpers. It preserves adaptive run detection, sparse-column decisions, radix key construction, digit skipping, comparison fallback, scheduling and existing thresholds. It adds no sorting algorithm, cache or worker policy.

Four new test functions check both sort directions across empty inputs, bitmap boundaries, sparse and uniform columns, stable ties, signed zero, infinities and random finite values. Independently ordered row indices check stable finite permutations. NaN cases check exact compatibility with the existing optional-array fallback, without claiming that NaNs define a strict total order. Public sorting checks exact value bits, native Int64 identifiers above 2^53, missing rows, source snapshots and shared numerical-batch buffers.

These checks pass before and after the optimization. They protect unchanged behavior rather than reproduce an incorrect result. Filtering retains its existing regression coverage after the shared view is renamed.

## Matched reference comparison

Prior is `3f850cb4ccbc2ef32e4645b5c3b49492596b1d18`. Current is `91c0ff09b7810b57cabdd953f8bc67791b1008f5` on `codex/csv-compact-sorting`. Both honor the same optional or compact storage choice in every case. Original is the historical fixed optional reader at `5d1f89a961106104757f2d8d0b8faba79487d100`. It supplies context rather than a matched compact-storage comparison. Twin repeats the exact current executable.

All clients use identical workload source and compiler optimization settings. Only the historical client omits the conditional assignment to the storage option that its interface lacks. That assignment occurs before timing. Each client imports the module interface matching its linked object. Receipts record source, object, module and executable hashes.

The panel covers household electricity observations with 2,075,259 rows and Aotizhongxin air-quality observations with 35,064 rows. Explicit native schemas, source bytes and null tokens match across versions. Integer columns remain Int64. Serial and native parallel CSV conversion each run with optional and compact Double storage. Three workflows measure the ascending sort of `Global_active_power` or `PM2.5`:

- `sort-indices` retains the CSV frame and the complete sorted index array.
- `sort-matrix` sorts the complete frame and prepares all declared numeric features as a matrix.
- `sort-materialize` sorts the complete frame and retains optional exports for every Double column.

Every worker checks all output rows, native types, value bits, null positions, row ordering and consumer outputs. All permutations and full outputs match the historical implementation. The reference datasets provide regression evidence; unit tests independently check the stated ordering rules.

## Household results with serial CSV conversion

Each cell gives prior and current medians. Total CPU includes CSV construction, requested operations and release. Operation CPU excludes construction and release. Held heap includes retained outputs. Peak RSS covers the process peak through the measured work. Complete output validation runs outside timing.

| Choice and workflow | Total CPU prior / current, ms | Operation CPU prior / current, ms | Held heap prior / current, MiB | Peak RSS prior / current, MiB |
|---|---:|---:|---:|---:|
| optional / sort-indices | 284.09 / 274.98 | 46.09 / 45.97 | 301.00 / 301.00 | 420.69 / 420.61 |
| optional / sort-matrix | 431.28 / 424.68 | 193.39 / 193.26 | 396.00 / 396.00 | 737.52 / 737.53 |
| optional / sort-materialize | 418.01 / 409.99 | 179.23 / 179.47 | 285.16 / 285.16 | 626.67 / 626.66 |
| compact / sort-indices | 298.91 / 288.65 | 51.32 / 51.45 | 191.95 / 191.95 | 312.48 / 312.41 |
| compact / sort-matrix | 419.65 / 411.28 | 169.79 / 169.60 | 318.22 / 302.39 | 519.10 / 503.41 |
| compact / sort-materialize | 445.44 / 435.48 | 189.07 / 184.83 | 429.08 / 413.25 | 566.80 / 551.02 |

[All 24 resource cases](results.md) cover both datasets and conversion modes. Removing a temporary allocation need not change retained memory. These process peaks do not isolate a sort-only allocation peak. Small full-workflow differences require caution, especially when CSV construction dominates the measured CPU.

## Interpretation and buffer-capacity diagnostic

The candidate does not demonstrate a sorting-CPU improvement. Household compact index sorting uses 51.32 versus 51.45 ms with serial CSV conversion and 52.78 versus 52.91 ms with parallel conversion. Complete-operation CPU changes are small and mixed. Differences in total CPU also include CSV construction, so they cannot all be attributed to the sort.

The matched panel records 15.828 MiB less held heap in both household sort-and-consume workflows, with roughly the same reduction in peak RSS. Index-only sorting and the smaller air-quality dataset show little memory change.

Eighteen separate diagnostic processes inspect numeric output-buffer capacities after recording memory. They use the same module objects and matching interfaces, but different clients. Their timings are excluded from the accepted panel. Every diagnostic output still matches its expected fingerprint.

For all three matrix diagnostic pairs, the prior version retains two oversized numeric buffers and the candidate retains one. One prior output column has capacity for 4,151,292 Doubles, compared with 2,076,668 in the candidate. Both contain 2,075,259 values. The capacity difference accounts for exactly 16,596,992 bytes, or 15.828125 MiB. Logical value counts and validity buffers match. This is lower spare allocation capacity in those runs, not a smaller logical column layout.

The export diagnostics show why that result needs a limit. In two of three pairs, both versions retain one oversized buffer and have equal held heap. In the remaining pair, the prior retains an additional oversized buffer and the candidate saves the same 15.828 MiB. The main panel's export-memory saving is therefore allocation-sensitive, not a guaranteed property of every call.

The output-capacity observations explain the measured heap difference. They do not trace which freed allocation supplies each buffer. Allocation reuse is a plausible explanation for the excess capacity, and proving its precise origin requires an allocation trace. Both versions still retain another oversized buffer in the larger consumed outputs. This remains an opportunity for follow-up work.

The candidate stays on its local experiment branch. The source removes an unnecessary conversion and shares existing helpers, but these results support neither a general sorting-speed claim nor a universal memory-saving claim.

## Validation and measurement controls

Release, Debug and Address Sanitizer each pass all 420 dataframe test functions without failures or skips. Twenty-eight eager and twenty-eight streamed reference checks verify native types, values, nulls and ordering. All 96 workflow preflights and 768 measured fresh processes match their complete output fingerprints.

Each of the 24 cases has eight fresh processes per label. Eight balanced orders place each label in each position twice and each ordered adjacent pair twice. The frozen quality policy flags current/twin median CPU differences above 10%, or peak RSS differences above 5% plus 8 MiB. Flagged comparisons remain unqualified. The audit records `quality_passed=true` with these flags: `[]`.

Builds and tests finish before accepted resource measurements. AC power is checked at both ends. The independent audit recomputes medians and checks balanced ordering, effective storage choices, exact outputs, source provenance and matching module imports. Identical-binary controls check repeatability within this panel; they do not remove every source of machine variation.

CPU means process user plus system time. CPU, elapsed time, held heap and peak RSS remain separate measures. These results do not measure energy, FLOPs, cache misses or SRAM activity. Address Sanitizer does not establish universal leak freedom. The work remains local, with no push or PR.

## Evidence and reproduction

- [Resource results](results.md).
- [Independent audit](audit.json).
- [Comparator provenance](comparator-provenance.json).
- [Patch from the prior branch](changes.patch.gz).
- [Scripts, sources, raw records and receipts](experiments.tar.gz).
- [Artifact hashes](artifact-sha256.json).

Restore the recorded commits and pinned dependencies. Build the historical modules from their recorded commits and compiler receipts. Decompress and apply the candidate patch to the prior commit. Update machine-specific paths. Run `verify.py Release --label final-release`, followed by `validate.py` for Debug, Address Sanitizer and client builds. Run `strict-check.py`, `run-panel.py preflight`, `run-panel.py measurement`, `capacity-diagnostic.py`, and `audit.py` in sequence.

The archive excludes executables, dependency caches, result bundles and large input CSVs. Source and tests stay on the experiment branch. This report and its evidence stay on `codex/engineering-notes`.
