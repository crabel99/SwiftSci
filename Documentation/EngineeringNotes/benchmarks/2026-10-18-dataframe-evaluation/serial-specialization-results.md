# Serial gather specialization results

2026-10-18. Engineering record on `codex/engineering-notes`. Keep this record out of implementation PRs.

Implementation branch: `codex/dataframe-serial-gather-specialization`, commit `2196173097b55cb6b15a8d619e6d8032d0e95106`. Parent: `d23bf7cac92fe9f9c10bd98046ca8ade354b5a3c`.

## Change and decision

The existing scalar gather loop now has concrete String, Bool and Date calls through a private helper. The change adds 13 production lines. It preserves the copy loop, optional-value storage, initialization, null counts and existing dataframe scheduler. User-defined SupportedType columns retain the generic path. Optimized object symbols contain concrete specializations for all three types.

Keep this focused change as a local implementation candidate. Held-out mixed-table sorting meets the preregistered benefit criterion. Numeric results include small losses, recorded below. This does not qualify the separate row-parallel dispatcher, a new storage policy, or a universal sorting speedup.

## Matched experiment

The frozen original and candidate use identical executable source, inputs, independent stable reference permutations and validation. Each process performs two warmups and five timed samples. Every output is complete and alive at timer stop. Checks run afterward and cover all rows, column types, null counts, stable order and Double bit patterns. The prepared-permutation gather timing excludes permutation creation. Complete sort includes it.

The Apple M4 Max uses the existing production-default CPU environment and native scheduling. AC power and power-mode settings remained unchanged. One benchmark process ran at a time, with alternating original/candidate launch order. This does not establish actual core placement, cache utilization or energy consumption.

## Held-out confirmation

The held-out cases use 250,003 rows, repeated keys, mixed String and Boolean payloads, and widths absent from screening. Ten independent process pairs per case provide 80 processes and 400 timed samples. Both complete-sort cases must save at least 0.25 ms at the paired median, and every pair must favor the candidate. No implementation adjustment followed confirmation.

| Operation | Rows | Columns | Layout | Original ms | Candidate ms | Paired saving ms [range] | Paired speedup |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| gather | 250,003 | 3 | mixed, ties | 11.712979 | 4.421750 | 7.290791 [3.815458, 14.801792] | 2.628x |
| sort | 250,003 | 3 | mixed, ties | 12.810438 | 6.126042 | 6.621959 [6.216333, 10.572666] | 2.061x |
| gather | 250,003 | 8 | mixed, ties | 20.029958 | 8.346875 | 11.565104 [11.280251, 13.407791] | 2.386x |
| sort | 250,003 | 8 | mixed, ties | 21.288020 | 9.836479 | 11.500896 [11.203792, 12.114041] | 2.172x |

## Screening and protected-case follow-up

All 20 screening cases and both follow-up cases satisfy the preregistered absolute sort-loss bounds. A bound is a workload decision, not proof that a slower result is noise. The independent follow-up repeats the two small numeric cases with consistent initial losses. It uses the same frozen executables and ten pairs each. Negative savings mean a loss. Ratios are suppressed when any sample is shorter than one microsecond.

| Operation | Rows | Columns | Layout | Original ms | Candidate ms | Paired saving ms [range] | Paired speedup |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| sort | 129 | 4 | numeric, random | 0.006605 | 0.006854 | -0.000229 [-0.000708, 0.000375] | 0.968x |
| sort | 4,096 | 1 | numeric, random | 0.045145 | 0.047729 | -0.002542 [-0.010583, -0.001293] | 0.947x |

## Correctness, memory and coverage

All 332 dataframe tests pass independently in Debug, Release and Address Sanitizer configurations, without failures or skips. Three added tests cover supported scalar types, missing values, uniform validity, duplicate selections, empty outputs, cached null counts and a user-defined generic fallback. The test file is 47 lines. Fifteen retained scientific, persisted-model, streaming CSV and wine controls also pass full-output conformance. These controls establish integration correctness, not workflow speed.

The local coverage export now uses the instrumented SwiftDataFrame library object and its matching raw profile. It maps 46 production files and covers all 12 added executable lines. The object and profile are preserved together before later builds can overwrite them. The earlier test-only export did not prove library coverage. This local result is not a hosted Codecov result.

No payload arrays, permutation arrays, row tasks or counters were added. Source and destination representations are unchanged. Measured optional-value strides and generated text lengths bound source-plus-destination logical payload at 128,000,000 bytes across these cases, below the planned 1 GiB limit. This counts text twice even when the output shares its backing storage. Allocator capacity, indices and runtime are outside that logical bound. Fresh-process high-water RSS includes source construction, reference sorting and validation. It does not isolate operation scratch, allocation count or retained memory. Every matched case stays within the declared 2 MiB median RSS-increase review limit.

The maximum case-median high-water RSS is 186.36 MiB. The audit verifies 320 processes and 1,600 measured samples, binary checksums, identical benchmark source, matching permutations, source identity, test receipts and unchanged power settings. No CPU-work, energy or allocation trace was collected.

## Complete screening table

| Operation | Rows | Columns | Layout | Original ms | Candidate ms | Paired saving ms [range] | Paired speedup |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| gather | 129 | 1 | numeric, random | 0.000833 | 0.000709 | 0.000125 [-0.000084, 0.000291] | unresolved |
| sort | 129 | 1 | numeric, random | 0.005167 | 0.004750 | 0.000417 [0.000166, 0.000916] | 1.081x |
| gather | 129 | 4 | numeric, random | 0.002208 | 0.002416 | -0.000167 [-0.000625, -0.000042] | 0.930x |
| sort | 129 | 4 | numeric, random | 0.006500 | 0.006917 | -0.000459 [-0.000792, -0.000084] | 0.932x |
| gather | 4,096 | 1 | numeric, random | 0.003542 | 0.003583 | 0.000000 [-0.000125, 0.000167] | 1.000x |
| sort | 4,096 | 1 | numeric, random | 0.044791 | 0.047709 | -0.002791 [-0.007291, -0.002626] | 0.941x |
| gather | 4,096 | 4 | numeric, random | 0.024917 | 0.027083 | -0.001958 [-0.003125, 0.002000] | 0.928x |
| sort | 4,096 | 4 | numeric, random | 0.073000 | 0.072500 | 0.000708 [-0.004417, 0.002667] | 1.010x |
| gather | 32,768 | 1 | numeric, random | 0.033542 | 0.033250 | 0.000083 [-0.001792, 0.002500] | 1.002x |
| sort | 32,768 | 1 | numeric, random | 0.459542 | 0.459417 | 0.001208 [-0.012083, 0.022959] | 1.003x |
| gather | 32,768 | 4 | numeric, random | 0.085125 | 0.085333 | 0.000959 [-0.014000, 0.005750] | 1.011x |
| sort | 32,768 | 4 | numeric, random | 0.540375 | 0.569292 | -0.009041 [-0.041041, 0.001833] | 0.984x |
| gather | 100,000 | 4 | numeric, random | 0.225500 | 0.219291 | 0.006750 [-0.004291, 0.024542] | 1.031x |
| sort | 100,000 | 4 | numeric, random | 1.677750 | 1.671792 | 0.003750 [-0.033751, 0.048458] | 1.002x |
| gather | 1,000,000 | 4 | numeric, random | 4.567917 | 4.571875 | -0.021959 [-0.102709, 0.020167] | 0.995x |
| sort | 1,000,000 | 4 | numeric, random | 21.204583 | 21.245667 | -0.046501 [-0.846709, 0.119333] | 0.998x |
| gather | 100,000 | 2 | mixed, nulls | 2.886959 | 0.996917 | 1.906417 [1.738833, 2.059083] | 2.944x |
| sort | 100,000 | 2 | mixed, nulls | 4.159542 | 2.324708 | 1.834834 [1.790751, 1.990333] | 1.789x |
| gather | 100,000 | 4 | mixed, nulls | 2.961000 | 1.067625 | 1.893375 [1.805084, 1.932083] | 2.773x |
| sort | 100,000 | 4 | mixed, nulls | 4.365916 | 2.420167 | 1.925374 [1.851500, 2.460626] | 1.789x |

## Evidence and next work

Raw evidence and repeatable procedures: `/Users/crabel/local-ai/spl/swiftsci/csv-sort-throughput-20261017/serial-specialization-20261018`. `compare.py`, `check-protected-followup.py`, `check-integration.py` and `audit.py` reproduce the comparison and checks. Use fresh output destinations for new runs. `committed-source.json` maps the exact tested source to the final commit without rewriting historical build receipts.

Source fingerprint: `2d5771e0ee6c4e37b8cbc35add4322bf776e8eda01ba86a0628e6ca674ce3f0c`.

[Preregistered plan](serial-specialization-plan.md). [Experiment register](experiments.tsv). [Earlier row-partitioned trial](row-gather-results.md).

Parallel stable radix and stable chunk sorting remain competing experiments. Test each against the same frozen parent, then check interaction with this specialization. Application-scale workflow timing remains open. Do not infer a new SwiftSci-versus-Polars ranking from this SwiftSci-only experiment.
