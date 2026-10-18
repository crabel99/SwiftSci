# Parallel sorting evaluation plan

2026-10-18. Frozen before implementation and candidate measurements. This plan belongs on engineering-notes, not an implementation PR.

## Contract and controls

Both independent candidates start at d23bf7cac92fe9f9c10bd98046ca8ade354b5a3c. The separate scalar-gather specialization stays absent, so changes in gathering cannot explain a candidate's result. Keep existing adaptive comparison sorting for sparse, small and run-ordered Double columns. Replace only the large disordered Double permutation path. Stable equal-key rows and signed zeros keep original order, missing rows remain last in both directions, and NaNs retain the existing comparison fallback. No public options, value-precision change, storage change, or new dependency.

Candidate A uses stable parallel LSD radix. Candidate B sorts contiguous chunks of key/index entries and merges them. Each synchronous parallel phase joins before owners leave scope. Scatter and merge writes must be disjoint and initialized before reads. Limit workers by activeProcessorCount and at least 65,536 valid rows per worker. Start parallel work at 131,072 valid rows. These are trial constants, not a production crossover claim.

Measure permutation creation and complete public sort separately. Complete sort includes allocating and gathering every output column. Output owners stay alive at timer stop. Independent stable reference sorting precedes timing. Full output validation follows every warmup and measured sample. Generated keys, schema, row identities, stable ordering, null placement, direction and output materialization are identical for every executable.

Use one frozen, uninstrumented Release executable per source candidate and baseline. On the same Mac, retain native CPU scheduling and unchanged AC power settings. Run one benchmark process at a time, rotating implementation order each round. Each process performs two warmups and five samples. Configured workers do not prove active-core placement or energy efficiency.

## Screening

Use three process rounds per case. At 131,073 and 1,000,000 rows, use random, repeated and missing-key distributions with four numeric columns, and measure permutation plus complete sort. Add both operations for small 4,096-row random input and 1,000,000-row ordered and sparse controls. Include a 1,000,000-row mixed-table complete sort and a descending missing-key complete sort. Total 20 cases, three implementations, 180 processes and 900 samples.

A viable candidate must improve the 1,000,000-row random four-column complete sort by at least 1 ms at the paired median, with every screening round favoring it. Screening is not confirmation. Preserve all cases, including slow or inconclusive ones. Do not change a candidate after inspecting held-out results.

## Held-out confirmation

Reserve a different generator seed, 250,003 and 750,007 rows, three and eight numeric columns, and random keys. Measure both operations, plus repeated-key mixed-table complete sorts at 250,003 rows with three and eight columns. Run five process pairs for each viable candidate against the original. A useful candidate must save at least 0.25 ms on both 250,003-row numeric complete sorts and 1 ms on both 750,007-row numeric complete sorts, with every pair favoring the candidate. Mixed cases must not lose more than 0.25 ms at the paired median. Failure is recorded, not waived.

## Safety and resource bounds

Protected complete-sort median slowdown limits are 5 microseconds at 4,096 rows, 0.1 ms at 131,073 rows, and 1 ms at 1,000,000 rows. Report paired ranges and investigate consistent losses. Ratios shorter than one microsecond cannot support conclusions.

Keep source-plus-destination logical payload below 1 GiB and algorithm-owned scratch below 256 MiB per request. Record buffer strides, capacities and simultaneous allocations. A median process-RSS increase above 64 MiB needs an explanation. RSS includes setup and validation and cannot isolate scratch or a leak. Collect process CPU time for the benchmark loop as an additional cost, outside elapsed-time boundaries. Do not infer energy from CPU time.

Run dataframe Debug, Release, Address Sanitizer and a focused Thread Sanitizer test for each concurrent candidate. Cover chunk boundaries, stable duplicate keys, nulls, signed zeros, infinities, late NaNs, constant radix digits, and source snapshots. Small tests retain the original routes. Large tests must actually cross the parallel threshold. Use all relevant scientific, persisted-model and CSV conformance controls for any candidate retained for production consideration. No new scheduling or storage policy is promoted by this experiment alone.
