# Common-path CPU diagnosis after sparse key admission

The earlier operation-level slowdown does not repeat consistently in two fresh full-path confirmations or the repeated-operation control. No source patch is justified by this evidence. The original full-panel measurements remain unchanged, including their small common-path CPU increases.

The candidate stays at `940353d441c5b2b1bcec69344629452b4ac65b7c` on `codex/csv-shared-keys-sparse-admission`. Its parent is `b982028c59c89f615688882ee71be19a0eccd8f2`. There are no new library changes, commits, pushes, or PRs in this diagnosis. The [sparse admission study](../2026-10-23-csv-sparse-key-admission/README.md) retains the 20% to 40% sort CPU savings and the complete qualification limits.

## Confirm the symptom before changing code

The prior panel's worst full-path increase is serial optional household sorting followed by matrix preparation, 436.280 to 452.313 ms total CPU. Operation CPU is 197.000 to 202.331 ms. Replaying its eight rounds with both candidate labels gives an operation increase in seven rounds, but a total CPU increase in six. Compact index sorting has no equally consistent operation increase.

The diagnostic command `python3 loop.py replay` records an alert for that seven-of-eight operation direction. This is a diagnostic signal, not a conformance limit or an acceptance-policy change. The live command accepts the same inputs and can report either direction. The small performance difference is not a deterministic correctness failure, so it would be misleading to claim a reliable regression test or force a production fix from the original medians.

The first confirmation is `python3 loop.py run --label live-1`. The second uses `--label live-2`. Each measures the same two selected public workflows over 2,075,259 household observations. Optional storage runs sorting followed by matrix preparation. Compact storage runs index sorting. Every worker checks the full outputs against the frozen reference contracts.

Both the parent and candidate have duplicate labels. Eight balanced orders put each label in each position twice and each ordered adjacent pair twice. Each implementation therefore has two fresh workers per round. The same frozen quality policy checks duplicate-label median CPU deviations above 10%, or peak RSS differences above 5% plus 8 MiB. Neither confirmation has a quality flag.

## Exclude CSV loading without replacing the full workflow

The smaller diagnostic loads and validates the original frame once. It then performs six public operations with the caller retaining that input. Every iteration checks all matrix or index bytes outside timing. The final iteration also checks the complete dataframe and the original wrapped matrix or index fingerprint against the frozen full-path contract. Release CPU is included separately from verification.

`python3 prepare-operation.py` builds both clients from identical source and flags against their matching module interfaces and objects. `python3 operation-loop.py` runs the same balanced duplicate-label controls. Its 64 workers perform 384 checked public operations. No quality flags occur.

This retained-input workload has different allocation reuse and input lifetime from the complete CSV workflow. Its absolute timings cannot replace the full-path baseline. Comparisons remain within each matched scenario.

| Study and workflow | Total CPU parent / candidate, ms | Paired total CPU change | Operation CPU parent / candidate, ms | Paired operation CPU change |
|---|---:|---:|---:|---:|
| live-1 / sort-indices | 295.411 / 300.306 | +0.66% | 47.505 / 46.559 | -0.39% |
| live-1 / sort-matrix | 426.782 / 429.026 | +0.81% | 192.280 / 194.640 | +1.15% |
| live-2 / sort-indices | 292.306 / 293.388 | +0.72% | 46.339 / 45.928 | -1.25% |
| live-2 / sort-matrix | 444.429 / 445.018 | +0.47% | 207.488 / 204.380 | -1.11% |
| operation-live / sort-indices | 46.624 / 47.096 | +0.33% | 46.623 / 47.094 | +0.33% |
| operation-live / sort-matrix | 181.675 / 180.118 | -0.63% | 165.151 / 163.442 | -0.86% |

The paired change is the median of eight within-round candidate-to-parent ratios. The two absolute CPU columns are separate medians across those rounds. A ratio of the printed absolute medians need not equal the printed paired change.

The earlier matrix-operation increase changes direction in the second full-path confirmation. It also changes direction in the retained-input control. The two live full-path total CPU differences remain slightly positive by the paired measure, approximately 0.47% to 0.81%. These checks do not prove that every common-path cost is absent. They do not re-establish the earlier worst result as a stable algorithmic penalty either.

## Compare emitted work instead of assuming a cache cause

`otool -tvV` records the exact two module objects after all timing workers finish. `inspect-code.py` compares matched symbol bodies. It removes leading instruction addresses, converts internal numeric branch targets to offsets within each symbol, and removes the disassembler-generated ADRP page-address comment. Actual opcodes and operands stay in the comparison, as do other comments.

All 428 matched CSV symbol bodies have identical normalized instruction listings. The shared `sortedDoubleRows` body has 194 instructions in both objects and matches after that normalization. Its eight-instruction comparator stub also matches. `prepareNumericMatrix` has 1,299 instructions in both objects and matches. The optional-array key-preparation specialization has 234 instructions in both objects and matches.

The old separate compact key-preparation specialization is not emitted under the same name in the candidate. Its body cannot be declared identical by this symbol comparison. The exact-output and public-operation controls exercise that compact route. The report does not infer its full generated shape from the missing symbol.

These are comparisons of emitted code, not dynamic instruction counts, FLOPs, physical cache traffic, or energy. Linked addresses, instruction placement, allocator behavior, runtime state, and scheduling can still affect cost. The earlier page-address comments changed because routines moved. That observation does not establish that instruction-cache placement caused the timing differences.

## Check retention without claiming universal leak freedom

Across all 64 retained-input workers, the sixth post-release heap measurement is 9,296 bytes above the first. That increase is identical for both implementations and both duplicate labels. The client itself retains six timing records, six digests, and a final full-frame fingerprint. A representative sequence is 299,004,544; 299,005,088; 299,005,600; 299,006,096; 299,006,640; and 299,013,840 bytes.

This result provides no evidence of different retained storage between implementations. It does not prove universal leak freedom or account for every allocation. The [release-heap records](release-heap.json) preserve every sequence.

## Decision and remaining limits

Preserve the smaller sparse-admission candidate. Do not add alignment directives, forced inlining, worker limits, density thresholds, or other workarounds to chase these small timing differences. The current evidence does not identify an extra common-path algorithmic pass or differential retention defect.

The earlier full-panel results remain valid observations. The new confirmations cover two selected serial workflows, not all 24 reference cases. A small full-path CPU effect and its physical cause remain unresolved. Any stronger claim needs a controlled profiling experiment or a further complete release comparison. No benchmark gate, numerical tolerance, or quality rule was relaxed.

The library source is unchanged and remains clean. No new unit tests were run because this work changes diagnostic clients and evidence only. The prior source head passed all 429 dataframe test functions in Release, Debug, and Address Sanitizer. Those earlier receipts are linked through the parent study rather than presented as new runs.

## Evidence and reproduction

The [audit](audit.json) verifies all 192 fresh diagnostic workers, balanced orders, exact outputs, matching modules and objects, phase statistics, and AC power at both ends of each run. The [phase comparisons](phase-comparisons.json), [compiled-code inspection](code-inspection.json), and [retained-heap records](release-heap.json) retain the detailed results.

The [experiment archive](experiments.tar.gz) contains the controllers, exact diagnostic client source, build commands, raw worker output, decisions, module receipts, disassemblies, inspection scripts, and input contract. The initial stricter code normalization is preserved separately. The final normalization removes only the documented page-address comment after examining its exact differences. [Artifact hashes](artifact-sha256.json) identify the report files.

Restore the recorded library objects, module interfaces, local dependency paths, and household dataset before running the archived commands. Keep each client matched to its recorded module and object. Finish builds and input preparation before any timing run. `python3 audit.py` independently recomputes the recorded phase statistics and verifies the evidence. `python3 inspect-code.py` regenerates the instruction comparison from the preserved disassemblies.
