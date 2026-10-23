# Choosing CSV Double storage

CSV callers can now choose the physical representation of native Double columns with `CSVReadOptions.doubleStorage`. The default is `.optional`, preserving the original reader's optional arrays and shared `.values` exports. `.compact` explicitly selects dense Double values and validity bits for direct numerical preparation. Both choices preserve values, nulls and native types. Int64 values are not converted to Double.

This is a child of [compact nullable joins](../2026-10-23-csv-compact-join/README.md), which measured a memory penalty when a caller retained a compact frame alongside optional exports. The choice is explicit because the preferred representation depends on those consumer lifetimes.

## Public interface

```swift
var options = CSVReadOptions()
options.doubleStorage = .optional
let legacy = try await DataFrame(csv: url, options: options)

options.doubleStorage = .compact
let numerical = try await DataFrame(csv: url, options: options)
let batch = try numerical.prepareNumericBatch(["feature"])
```

Optional storage keeps `.values` exports shared through copy-on-write. Compact storage materializes an optional array on each `.values` request. Retaining those exports alongside the compact column retains both representations. Eager and streamed reads honor the same option, with either serial or parallel column conversion. Inference retries retain the policy when a sampled integer column promotes to Double.

## One parser, two existing builders

`CSVValueDecoder` no longer owns a builder type or factory. `CSVColumnAttempt` accepts an independent builder and shares its existing conversion, rejection, reset and finalization loops. The column plan selects the existing optional or compact Double builder once per attempt. Both Double paths use the same decoder and validation loop. No storage-policy branch was added inside the row loop, and no legacy factory or decoder wrapper was retained.

## Matched reference comparison

- Original is the fixed optional-array reader at `5d1f89a961106104757f2d8d0b8faba79487d100`.
- Prior is the fixed compact join prototype at `a95ef036982e91d87dcddf50f972a64a27f20a74`.
- Current is `codex/csv-double-storage-choice` at `2c18d9833a7567c8b2ef6480f4a2467302d7d453` and honors the policy in each case.
- Twin repeats the exact current executable with the same policy.

All versions use identical client source, input contracts, lookup contents and operation scope. Historical interfaces lack the new property, so only the current client enables `CSV_STORAGE_CHOICE`, which sets the option before timing. This flag changes neither compiler optimization settings nor timed workload code. Each worker records its effective storage, including the fixed historical representations. Physical representation is the deliberate variable in this experiment. Input values, null tokens, schema, row order and full output fingerprints remain equal.

The table reports the 2,075,259-row household dataset with serial column conversion. Each entry lists original, prior and current medians. `join-materialize` retains a complete left-joined frame and all requested optional Double exports. `batch` retains the CSV frame and its prepared numerical batch.

| Current choice and workflow | CPU original / prior / current, ms | Held heap original / prior / current, MiB | Peak RSS original / prior / current, MiB |
|---|---:|---:|---:|
| optional / join-materialize | 711.57 / 495.33 / 717.52 | 316.83 / 429.48 / 316.83 | 642.44 / 550.20 / 642.47 |
| optional / batch | 252.59 / 250.04 / 251.83 | 397.81 / 176.11 / 397.81 | 420.61 / 312.41 / 420.64 |
| compact / join-materialize | 701.52 / 478.67 / 476.77 | 316.83 / 429.48 / 429.48 | 642.44 / 550.20 / 550.22 |
| compact / batch | 265.16 / 258.65 / 254.81 | 397.81 / 176.11 / 176.11 | 422.03 / 313.11 / 312.47 |

[Full resource results](results.md) include both reference datasets, both conversion modes and both storage choices. Household parsing uses the same eleven declared null tokens, including `?`, for every version. Air-quality parsing uses the same ten default tokens. Schemas are explicit and identical. Native CPU scheduling is unchanged, and no worker cap or dataset-specific threshold was added.

## The tradeoff in the current implementation

These are both choices in the same current executable, using household data with serial conversion. Each entry reports total CPU, held heap and peak RSS.

| Workflow | Optional CPU / held heap / peak RSS | Compact CPU / held heap / peak RSS |
|---|---:|---:|
| join-materialize | 717.52 ms / 316.83 MiB / 642.47 MiB | 476.77 ms / 429.48 MiB / 550.22 MiB |
| batch | 251.83 ms / 397.81 MiB / 420.64 MiB | 254.81 ms / 176.11 MiB / 312.47 MiB |

For the joined frame plus optional exports, optional storage avoids about 113 MiB of retained heap, but uses about 241 ms more CPU and 92 MiB more peak RSS than compact storage. Compact storage retains both representations in this workload. For the numerical batch, compact storage avoids about 222 MiB of held heap with similar total CPU. These measurements support a caller-visible choice rather than a universal resource score or an automatic size threshold.

## Validation and measurement

The default-export regression fails before the change because the prior prototype retains compact storage and creates separate arrays on repeated `.values` exports. It passes afterward. Public tests check both policies under explicit and inferred schemas, streamed chunks, selections and outer joins. They verify exact integer identifiers above 2^53, missing values, signed zero, valid NaNs and infinities. Optional exports share storage, compact exports have separate arrays, and mutations preserve snapshots. Late integer-to-Double promotion, rejection to text and explicit conversion failures retain their existing semantics and the requested layout.

Release, Debug and Address Sanitizer each pass all 413 dataframe tests with no failures or skips. Twenty-eight eager reference checks and twenty-eight streaming checks cover both policies with pinned native types, value and null hashes and ordering. All 64 workflow preflights and 512 measured processes match the original output fingerprints. Derived-workflow equivalence is a regression check, not independent mathematical certification.

Eight balanced orders give each label each position twice and each ordered adjacent pair twice. The unchanged quality policy flags more than 10% current/twin median CPU difference or peak-memory differences beyond 5% plus 8 MiB. Flags remain disqualifying for affected comparisons. The audit records `quality_passed=True` with these flags: `[]`.

All tests and builds finished before accepted measurements. AC power was checked at both ends. Each comparator client imports the matching module interface for its linked object. Build receipts, source hashes and binary hashes are archived. Full output validation is outside timing. The audit recomputes medians and checks fingerprints, effective storage and power receipts.

CPU means process user plus system time. Held heap measures malloc live bytes, and peak RSS measures a different process memory cost. The experiment does not measure energy, FLOPs or cache activity. Address Sanitizer does not establish universal leak freedom. These changes remain local and have not been pushed or submitted as a PR.

## Evidence and reproduction

- [Full results](results.md).
- [Independent audit](audit.json).
- [Comparator source provenance](comparator-provenance.json).
- [Exact source patch](changes.patch.gz).
- [Scripts, sources, raw records and receipts](experiments.tar.gz).
- [Artifact hashes](artifact-sha256.json).

Restore the recorded prior commit, decompress and apply the patch, restore pinned dependencies, and update machine-specific paths. Run the Release dataframe tests with `verify.py`, then `validate.py` for Debug, Address Sanitizer and client builds. `measure.py` runs both-policy reference checks, workflow preflights, measurements and the audit. The archive excludes executables, caches, result bundles and large reference CSVs. Engineering records stay on `codex/engineering-notes`; source and tests stay on the experiment branch.
