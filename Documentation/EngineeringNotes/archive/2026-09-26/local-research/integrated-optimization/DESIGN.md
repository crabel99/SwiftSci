# Selected integration design

Use Candidate A on `codex/dataframe-pipeline-optimization`, based on `2694d303f8`. Keep Candidate B with the separate compact-column-storage experiment. The [cross-review](design-review.md) and source notes explain the alternatives.

The public eager API and current column types remain the compatibility boundary. CSV owns byte grammar and mapped lifetime. Grouping owns typed equality, first-seen IDs and arithmetic order. Sorting owns stable permutations. These operations share row positions but do not need a common execution framework.

## Selected work

1. Replace per-row CSV offset arrays with one ragged flat field index. Both reader paths use it; the public parser materializes nested arrays through a wrapper over the same scanner. Complete conversion inside the mapped bytes closure.
2. Reuse integer direct lookup for the first composite grouping key, then refine bounded prefixes using checked products and a row/byte budget. Preserve dictionary fallback and exact integer identity.
3. Measure a Double stable-radix permutation outside production before selecting any sorting replacement. Count full gather cost, ordered-input behavior and scratch memory.
4. Measure byte null matching separately after the CSV storage change. The sampled baseline attributes 24.1% self CPU weight to Set.contains and 8.6% to String comparison. Preserve custom tokens, quoting, trimming, escapes and canonical Unicode equality.

The baseline profile is a bounded 20-second capture. Its 23.355 seconds of sampled CPU weight includes concurrent column workers. Inclusive percentages overlap and are not wall-clock shares. See [profile summary](csv-profile.txt).

## Verification and integration

Each component has an exclusive source owner during implementation. The parent reviews and runs builds and benchmarks serially, then commits verified slices separately. Tests cover exact integer extrema, null identity, Unicode equality, stable equal-key order, signed zero and NaN fallback. CSV layout preserves existing tokenization; inherited EOF, inference and integer-overflow bugs are recorded separately in the grounding note.

Acceptance requires full public-operation parity and a repeatable latency or memory benefit. Record source and executable hashes, raw samples and peak process RSS. Reject algorithm candidates that lose outside a defensible applicability range. Final verification includes the complete Debug and Release suites, including MLX. No push or PR is authorized by this task.

## What carries forward

Pandas and Kiraa support flat token storage, typed conversion and integer factorization as useful mechanisms. Their different output types, Unicode behavior and overflow policies prevent copying implementations unchanged. NumPy currently uses indirect Timsort for the measured Float64 sort, so radix is an experiment rather than an assumed explanation for pandas performance.

Candidate B remains valuable for reducing repeated materialization across whole queries. It needs independent storage ownership, sparse-view retention, backpressure and final materialization measurements before integration with public TypedColumn.values.
