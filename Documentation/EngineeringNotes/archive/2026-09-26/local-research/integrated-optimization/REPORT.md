# Integrated dataframe optimization results

Four local commits on `codex/dataframe-pipeline-optimization`, final commit `dc31b5f1af`, implement flat CSV fields, ASCII null matching, bounded composite integer grouping and adaptive Double sorting. The previous optimization branch and compact-storage experiment remain separate. Nothing was pushed and no PR was opened.

## Final production comparison

One million rows, native arm64 Release on this M4 Max. Medians in milliseconds from 15 timed repetitions per library, with two warmups per process and rotating serial batches. These are complete public operations, including result gathering.

| Operation | SwiftSci | pandas | Kiraa |
|---|---:|---:|---:|
| CSV read | 40.158 | 68.824 | 9.901 |
| Two-key group sum | 11.543 | 10.106 | 35.774 |
| Stable descending sort | 36.113 | 29.734 | 59.256 |
| Filter → sort → group | 19.875 | 20.252 | 41.998 |

[Full comparison, memory and raw evidence](/Users/LOCAL_USER/local-ai/spl/swiftsci/production-comparison/results/20260926T043033Z/REPORT.md). The recorded source is clean except for the two pre-existing untracked directories. All 24 SwiftSci workload/size combinations passed output parity. Kiraa retained its two known integer-filter failures; those timings are excluded. Actual Kiraa composite key columns now participate in validation.

## Matched before-and-after experiment

The preserved original executable at `2694d303f8` was alternated with the candidate on the same fixtures. This measurement used the final dense-input algorithm before the later sparse-density guard. The guard affects inputs below five percent non-null; these fixtures have about 99 percent non-null values. The clean final-source comparison above confirms the final implementation independently.

| Operation | Original ms | Candidate ms | Speedup | Original peak MiB | Candidate peak MiB |
|---|---:|---:|---:|---:|---:|
| CSV read | 111.861 | 39.339 | 2.84× | 584.4 | 308.5 |
| Stable descending sort | 65.674 | 36.288 | 1.81× | 151.7 | 136.7 |
| Filter → sort → group | 36.730 | 20.077 | 1.83× | 121.1 | 125.0 |
| Two-key group sum | 49.536 | 11.375 | 4.35× | 101.0 | 99.6 |

[Alternating samples and executable hashes](/Users/LOCAL_USER/local-ai/spl/swiftsci/integrated-optimization/measurements/20260926T042111Z/raw.json). RSS is a whole-process high-water measurement, including fixtures and allocator reuse. It is not an incremental scratch-allocation count. CSV memory fell about 47 percent. Sorting scratch can increase memory on other distributions, and this pipeline used about 4 MiB more at its peak.

## Source and design decisions

- Pandas and Kiraa use flat parser storage. SwiftSci now uses a flat ragged index and keeps every mapped-byte consumer within its valid lifetime.
- A CPU profile attributed substantial conversion work to String null matching. Numeric conversion now checks normalized ASCII bytes, with String fallback for Unicode and escaped fields.
- Pandas checks combined key cardinalities. SwiftSci now uses checked bounded integer refinement and retains typed dictionary fallback for sparse or overflowing domains.
- NumPy uses adaptive comparison sorting for this Float64 workload. Pure radix lost on ordered inputs, so SwiftSci now chooses between comparison and radix using input size, density and ordered runs. It stops comparison preparation early when radix is selected.

[Implementation comparison and rejected alternatives](INTEGRATION-NOTES.md) links the detailed source traces and academic references. [Candidate B](candidate-b.md) preserves the compact-buffer and delayed-materialization direction for separate work.

## Verification

- Complete Debug suite: 863 tests passed, zero failures and zero skips.
- Complete Release suite: 863 tests passed, zero failures and zero skips.
- Both suites included MLX-dependent targets. Parameter expansion produced 905 device-level test executions per configuration.
- Sort experiments verified 416 frame cases plus six explicit NaN-rejection cases. Regression tests separately verify late-NaN fallback, stable row identities, exact bit patterns, integer limits, Unicode key equality, CSV quoting and mapped-buffer ownership.
- The final 99%-missing case retained comparison sorting and removed the extra roughly 7 MiB radix cost. The 90%-missing case retained its measured speed benefit.

[Debug summary](../full-suite-validation/debug-20260926T042551Z-h43q2l/summary.json), [Release summary](../full-suite-validation/release-20260926T042652Z-XTcq8F/summary.json), [final sparse measurements](sort-prototype/results/20260926T042841Z/samples.jsonl).

## Limits and next integration work

Kiraa remains faster on CSV in this fixture. Its compact Double storage and guarded parallel scanning have different type and parsing policies. SwiftSci still creates public optional-array columns and indexes the full file before conversion. Streaming typed builders and retained row selections remain candidates on the compact-storage branch.

The existing CSV trailing-delimiter behavior, integer-parser overflow and sampled type-inference limitations are documented in the source review and were not changed in this performance patch. Existing NaN sort behavior is preserved rather than redefined. These results do not establish GPU or MLX inference acceleration. No hardware-counter result establishes memory-bandwidth saturation.

Other applications shared the Mac during measurements. Use the recorded variation and complete-operation results; do not treat sub-millisecond differences as universal rankings.

## Local commits

- `2088e04647` Flatten CSV field storage and scope mapped bytes.
- `455d0a1f2f` Bound integer composite group refinement.
- `39c9553c20` Match ASCII CSV nulls without String decoding.
- `dc31b5f1af` Adapt Double sorting to order and density.
