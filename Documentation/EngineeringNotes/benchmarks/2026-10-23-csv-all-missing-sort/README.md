# Stable identity sorting for fully missing keys

The candidate adds one early return to `TypedColumn.sortedIndices`. When `nullCount == count`, every key is missing and the stable permutation is the original row order in either direction. Returning that permutation avoids key scans and sort preparation.

Source is `a74f5c3b5e0e511bf5bb69886a40cbae48b28d99` on `codex/csv-all-missing-sort`, based on `940353d441c5b2b1bcec69344629452b4ac65b7c`. This remains a local candidate. No push or PR is included. The [previous sparse-admission study](../2026-10-23-csv-sparse-key-admission/README.md) and [common-path diagnosis](../2026-10-23-csv-common-path-diagnosis/README.md) retain the earlier decisions and results.

## Use an existing invariant without another policy

`TypedColumn` is immutable and maintains its null count. The shortcut needs no additional metadata, cache, public option, size threshold, worker limit, or precision conversion. It runs before type-specific sorting dispatch and therefore applies to all supported native types, including Bool, String, and Date. Empty columns satisfy the same invariant.

Valid NaNs do not contribute to the null count and still use the existing comparison fallback. Finite values, numeric ties, signed zero, mixed missing values, native integer identities, and public dataframe sorting retain their existing contracts. The implementation adds one source line. The two new test functions occupy a 60-line type.

The semantic result was already correct. Both new tests pass before implementation. Their purpose is to protect the invariant and nearby behavior, not to manufacture a failing-before correctness claim. Resource measurements test the optimization separately.

## Measure the all-missing case across types and sizes

Eighteen cases cover Double, Float, Int64, Int32, Int, String, Date, Bool, and compact Double at one and eight million rows. Input construction is outside timing, and the caller retains the input through index sorting and result release. Optional native columns use their public initializer. Compact Double uses the public CSV reader with a complete Double schema and quoted empty fields. Constructor methods and storage choices match across source versions.

Every worker checks every returned index against identity and verifies its complete byte hash against an independently generated permutation. Timings use ascending order. Correctness tests cover both directions. Process peak RSS can include the earlier constructor peak.

| Native key and row count | CPU parent / candidate, ms | Peak RSS parent / candidate, MiB | Qualified |
|---|---:|---:|---|
| Double/1000000 | 2.335 / 0.655 | 36.922 / 29.281 | False |
| Float/1000000 | 2.312 / 0.731 | 29.312 / 21.672 | False |
| Int64/1000000 | 2.321 / 0.686 | 36.938 / 29.297 | True |
| Int32/1000000 | 2.305 / 0.728 | 29.328 / 21.672 | True |
| Int/1000000 | 2.341 / 0.675 | 36.938 / 29.281 | True |
| String/1000000 | 45.062 / 0.678 | 44.641 / 29.281 | True |
| Date/1000000 | 57.709 / 0.712 | 44.656 / 29.312 | False |
| Bool/1000000 | 65.570 / 0.738 | 30.344 / 15.000 | True |
| CompactDouble/1000000 | 2.369 / 0.664 | 30.672 / 23.078 | True |
| Double/8000000 | 18.323 / 5.937 | 250.547 / 189.500 | False |
| Float/8000000 | 18.552 / 5.253 | 189.531 / 128.484 | True |
| Int64/8000000 | 18.567 / 6.037 | 250.562 / 189.516 | True |
| Int32/8000000 | 18.535 / 5.465 | 189.547 / 128.484 | True |
| Int/8000000 | 21.291 / 6.598 | 250.562 / 189.500 | True |
| String/8000000 | 383.430 / 6.147 | 311.672 / 189.500 | True |
| Date/8000000 | 455.214 / 5.464 | 311.688 / 189.531 | True |
| Bool/8000000 | 536.513 / 5.475 | 197.234 / 75.062 | True |
| CompactDouble/8000000 | 18.867 / 6.076 | 191.828 / 130.797 | True |

Fourteen of the 18 cases qualify under the frozen identical-binary controls. Their observed CPU reductions range from 67.5% to 99.0%. These are exceptional-case results for entirely missing keys. They do not establish the prevalence of that condition in production.

The qualified eight-million-row compact Double case falls from 18.867 to 6.076 ms CPU. Peak RSS falls from 191.828 to 130.797 MiB, about 61 MiB. The qualified String case falls from 383.430 to 6.147 ms CPU, with peak RSS 311.672 to 189.500 MiB, about 122 MiB less. Bool falls from 536.513 to 5.475 ms, with peak RSS 197.234 to 75.062 MiB.

The retained input and required index result are the same size. Held heap is essentially unchanged. The memory benefit comes from lower process peak, consistent with avoiding temporary sorting storage. These measurements do not establish physical memory traffic, cache effects, energy, or FLOPs.

The Double one-million-row, Float one-million-row, Date one-million-row, and Double eight-million-row comparisons are unqualified. Their identical-binary median CPU ratios exceed the existing 10% limit. Their outputs remain correct, and their observations remain in the table and raw records. No performance conclusion is drawn from those four cases. No rerun or quality waiver replaces them.

## Keep common-path costs visible

The existing 80 shape cases cover 32,768 and one million rows with both storage choices. They include monotonic order, early/middle/late disorder, random values, sparse values, clustered and distributed missing rows, and the earlier admission boundary. They check the added branch when a key contains values.

All 2,560 measured outputs match their full fingerprints. Seventy-nine timing comparisons qualify. The compact 32,768-row distributed case just below half occupancy is unqualified because the identical-binary CPU ratio is 1.1311.

The largest qualified common-control CPU increase is the optional 32,768-row half-minus-one case, 0.068 to 0.076 ms, about 11.8%. The compact million-row half-plus-one case rises from 2.353 to 2.589 ms, about 10.0%. The optional million-row ascending control rises from 1.270 to 1.354 ms, about 6.6%. These observations are retained. A single metadata branch does not by itself explain their physical cause, and the panel does not establish that every increase is a persistent algorithmic cost. It would also be wrong to discard them because the all-missing case improves.

[All shape results](shape-results.md) include the earlier shared-key checkpoint and the immediate parent. No new threshold or source workaround was fitted to these results.

## Check complete reference workflows separately

Four serial household workflows cover optional and compact storage, index sorting, and sorting followed by matrix preparation over 2,075,259 observations. These keys contain values and do not take the new early return. The same complete schema, null tokens, input bytes, native types, and row order apply to every source version.

Total CPU includes CSV construction, the requested operations, consumer preparation, and release. Operation CPU excludes CSV construction and release. Full verification is outside timing.

| Household serial storage and workflow | Total CPU parent / candidate, ms | Operation CPU parent / candidate, ms | Held heap parent / candidate, MiB | Peak RSS parent / candidate, MiB |
|---|---:|---:|---:|---:|
| compact/sort-indices | 296.613 / 294.878 | 46.750 / 46.545 | 191.952 / 191.952 | 312.391 / 312.359 |
| compact/sort-matrix | 424.859 / 414.671 | 168.780 / 169.118 | 286.952 / 286.952 | 503.242 / 503.328 |
| optional/sort-indices | 286.343 / 289.494 | 46.694 / 49.629 | 300.999 / 300.999 | 420.594 / 420.562 |
| optional/sort-matrix | 439.696 / 434.149 | 195.451 / 196.609 | 395.999 / 395.999 | 737.516 / 737.461 |

Total CPU changes range from 2.4% lower to 1.1% higher. Retained heap and peak RSS are essentially unchanged. Optional index-sort operation CPU rises from 46.694 to 49.629 ms, about 6.3%, although its full-path increase is 1.1%. Matrix-operation CPU also changes slightly. These observations do not show a general CSV or ordinary-sort improvement.

All four reference cases qualify and match exactly. This selected panel is a common-path check, not a replacement for the earlier 24-case reference panel or a new formal performance baseline. The same input contracts also pass 28 eager and 28 streamed exact reads across the existing reference policies and storage choices.

## Verification, qualification, and decision

Release, Debug, and Address Sanitizer each pass all 431 dataframe test functions with zero failures or skips. The two new functions check all supported native types, both directions, empty and bitmap-boundary sizes, public sort output, unchanged column names and types, Int64 row identities above 2^53, compact null validity, and valid NaNs among missing values. This validates the dataframe module, not the complete MLX-dependent package. Address Sanitizer does not prove universal leak freedom.

The panels contain 408 preflights and 3264 measured fresh processes. Every complete output matches. There are 102 timing comparisons, of which 97 qualify. Four all-missing cases and one common-shape case remain unqualified.

Eight balanced orders put each label in each position twice and each ordered adjacent pair twice. The original label is `b982028c59c89f615688882ee71be19a0eccd8f2`. The parent label is `940353d441c5b2b1bcec69344629452b4ac65b7c`. Current and twin run the identical new executable. Median CPU drift above 10%, or peak RSS above 5% plus 8 MiB, flags the affected comparison. No quality rule, numerical tolerance, worker budget, affinity setting, or precision policy changed.

Tests, builds, and input preparation finish before timing. AC power is checked at both ends. Native parallelism is unchanged. CPU is process user plus system time. Independent audits verify source and input hashes, matching object and module provenance, complete output equality, balanced orders, and recomputed medians.

The decision is to retain the one-line shortcut as an isolated local candidate. Its invariant is general and its qualified exceptional-case resource savings are substantial. Five unqualified comparisons and the common-control CPU increases prevent an unconditional performance or production recommendation. The source checkpoint is preserved without changing other sorting policies.

## Evidence and reproduction

[Overall audit](overall-audit.json), [source and reference audit](audit.json), [all-missing audit](native-audit.json), [shape audit](shape-audit.json), [full reference results](results.md), [all shape results](shape-results.md), and [comparator provenance](comparator-provenance.json) retain the results and their limits.

The [experiment archive](experiments.tar.gz) contains the clients, fixture generators, controllers, raw measurements, build and test receipts, source snapshots, and validation logs. The [source patch](changes.patch.gz) applies to the recorded direct parent. [Artifact hashes](artifact-sha256.json) identify these files.

The archived `verify.py`, `validate.py`, `measure.py`, `audit.py`, `audit-native.py`, and `package.py` reproduce the stages. Restore the recorded dependency paths and external dataset contracts before rebuilding. Match each client to its own module interface and object. Preserve unqualified records when repeating any later study.
