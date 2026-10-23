# Direct compact Double CSV prototype

This local experiment moves compact numeric construction into the CSV reader while retaining `TypedColumn<T>` lookup. It reuses the existing `CompactNumericColumn` value and validity buffers. It does not add a second compact column framework or convert a completed optional array after reading.

The household read holds **285.15 → 176.11 MiB live heap**, a **38.2% reduction**. This is a measured result, following the earlier [memory accounting](../2026-10-23-csv-eager-memory/README.md). It does not establish a universal resource improvement. Existing bulk callers can request optional arrays, and that work must be counted.

## Experimental scope

- Base commit: `5d1f89a961106104757f2d8d0b8faba79487d100`.
- Local branch: `codex/csv-compact-double-prototype`.
- Recorded experimental head: `6af4b8f071443779964ce77ac0856c48127657c6`.
- Three source files and one focused test file change. No source changes reach the qualified CSV branch or a pull request.
- Double CSV decoders choose a compact builder at compile time. All other decoder builders retain their original representations. Int64 values do not pass through Double.
- CSV syntax, null-token matching, inference candidates, record batch bound, scheduling policy and output ordering are unchanged.

`TypedColumn` privately distinguishes optional arrays from dense values with a validity bitmap. Its typed subscript reads either representation directly. Requesting `.values` returns the existing `[T?]` calling format. For dense storage, that request materializes an array each time. There is no retained compatibility cache. This preserves source-level reads, but changes their cost. It is not an ABI compatibility qualification or permission to make this the production default.

The dense builder shares the numerical pipeline's existing arrays at finalization and clears its temporary ownership. Valid NaNs remain different from missing values. Missing slots contain the same NaN placeholder used by `CompactNumericColumn`; the bitmap determines whether a value is present. The prototype preserves metadata-only renaming without expanding values.

## Correctness before measurement

The dataframe suite passes **399 tests each in Release, Debug and Address Sanitizer**, with no failures or skips. Focused additions cover bitmap word boundaries, all-present and all-missing columns, NaN payload bits, signed zero, infinities, builder growth and reuse, independent exported arrays, exact Int64 values above 2^53, boxed and typed scalar access, lags, filtering, gathering, sorting, joins and matrix conversion.

Fourteen additional eager reads and fourteen streamed-reference checks cover the seven existing reference contracts under both conversion policies. They retain exact native types, row and column order, null positions and per-column SHA256 values. Ninety-six workflow preflights and 1,152 measured fresh processes compare complete final frame, matrix and exported-array fingerprints with the baseline. The row-scan workload also compares a wraparound sum of the exact Double bit patterns read through boxed row access.

Workflow fingerprints establish equivalence to this baseline. They are not an independent mathematical certificate for every pre-existing dataframe operation. The [audit](audit.json) records the exact checks and measurement-quality status.

## The compatibility defect caught during review

The first implementation left scalar `value(at:)` and lag loops indexing `.values`. With a materializing getter, that would allocate and traverse a whole optional array for each scalar access. The original 398-test functional run passed but did not demonstrate constant-time access. Review caught the complexity regression before this code was committed or promoted.

The owned trial controller and its child were stopped. All 202 completed partial workers, their original source hashes and build receipts are preserved as an incomplete, unaccepted trial. Scalar and lag calls now use direct indexed storage. Generic numeric gather helpers also avoid repeated property materialization, and renaming retains storage. Row scanning and lagged matrix construction were then added to a new, frozen panel. Only this corrected version supplies the results below.

One intermediate compile attempt also caught two overly broad edits in plain-array sort helpers. Those edits were corrected before the successful 399-test runs. Its failure log remains in the archive. No incomplete trial data are combined with the corrected run.

## What the resource panel includes

The inputs are the complete 2,075,259-row household file and the 35,064-row Aotizhongxin air-quality file. They use their recorded exact schema and null-token contracts. The household case has eleven declared null tokens, including `?`, and is not the ten-token Swift default. No inference advantage is given to either implementation.

Each input runs both existing conversion policies across eight complete workflows:

1. Read and release a complete frame.
2. Read and retain optional arrays for all Double columns.
3. Read, filter, and construct a matrix.
4. Read, gather every seventeenth row, and construct a matrix.
5. Read, sort, and construct a matrix.
6. Read, perform a left lookup join, and construct a matrix.
7. Read and scan a numeric column through boxed row access.
8. Read, add a lagged numeric column, and construct a matrix.

CPU includes public CSV construction, the requested operations and release. Full output hashing is outside timed intervals. Held heap and peak RSS are captured before hashing. Input option and small lookup-table preparation occur before the baseline counters. A frame and requested export arrays or matrix coexist at the held checkpoint because that is what each workload requests.

The baseline, an identical-binary baseline twin and the prototype run in all six orders twice, giving twelve fresh processes per label and case. The CPU backend uses native scheduling without worker caps. Serial and parallel refer only to CSV column conversion, not a one-core versus many-core budget for the complete workflow. Builds, tests and profiling do not overlap accepted measurements. AC power is checked at the beginning and end. No GPU, NPU, energy-use or cache-utilization result is inferred.

## Results and qualification

[Complete results](results.md) show CPU time, held live heap and absolute process peak RSS for every workflow. CPU is process user plus system time, not wall time or FLOPs. Held heap is live malloc allocation size, not physical footprint. Peak RSS includes clean mapped input and allocator-retained pages. These quantities should not be combined into a single efficiency score.

For household serial reading, CPU is **248.25 → 254.66 ms**, and peak RSS is **421.92 → 313.86 MiB**. Requesting the numeric optional arrays changes held heap to **285.15 → 397.81 MiB**, demonstrating why the calling pattern is part of the storage decision. Its CPU changes from **246.51 to 1377.30 ms**, about **5.59 times** the baseline. This is a serious compatibility cost. The experiment has not isolated how much comes from generic code generation, optional construction, bitmap tests or allocation.

The identical-binary control status is **passed**. Its unchanged review limits are a 10% deviation in median CPU, and a peak-memory difference beyond 5% plus 8 MiB. Any flagged cases remain unqualified. Small unflagged differences are descriptive observations, not established general rankings.

This compares the prototype with the existing Swift CSV baseline in the same panel. It does not rerun pandas, Polars or DuckDB. Do not combine its timings with earlier external medians to claim a new cross-library speed ratio.

The costs extend beyond explicit array export. The household serial sort-and-matrix path uses about 12% more CPU and increases peak RSS from roughly 739 to 852 MiB. Its join-and-matrix path uses about 2.5 times the CPU. The lag-and-matrix path retains about 109 MiB less live heap but peaks about 112 MiB higher. Lower retained storage therefore does not guarantee a lower peak or less CPU work. These measurements justify more integration work, not a default switch.

## Integration decision

Keep this as an experiment. Compact ingestion demonstrates a retained-memory opportunity, but a complete design must account for callers that expand the values. Changing only the reader and calling that finished would move allocation and copying costs to later operations.

The next focused experiment must investigate the generic optional-array getter and let matrix and prepared-batch construction consume the existing dense buffers directly. Single-column packing should reuse values when its missing-value policy permits it. Wider matrices should read dense values and validity in one packing pass. Filter, gather, sort and join outputs also need a deliberate storage policy so they do not automatically erase the benefit.

Measure those changes against the same complete workflows, including optional-array callers. Preserve the original baseline and this experimental head. No default representation, user-facing storage policy, or upstream PR is decided by this prototype alone.

## Reproduction and evidence

- [Resource results](results.md).
- [Audit](audit.json).
- [Experimental patch](prototype.patch).
- [Experiment archive](experiments.tar.gz), containing controllers, source snapshots, input contracts, compiler module-loading receipts, test receipts and logs, the interrupted trial, and all raw measured outputs.
- [Artifact hashes](artifact-sha256.json).

Restore the recorded base, apply the patch on an isolated branch, rebuild its dependencies, and update the archived scripts' absolute roots for the machine. Every new standalone client asserts that its imported module interface matches the linked object. The baseline uses its previously qualified module and object; the experiment builds all 50 dataframe source files with the same optimized whole-module compiler flags and macOS 14 deployment target. Native binaries, caches, result bundles and large reference files are excluded.

The reproducible edit recipe captures the initial implementation. The final patch is the authoritative corrected experiment. `verify.py` drives the restricted dataframe test scheme, `build.py` and `link-workflows.py` produce matched clients, `run-panel.py` performs exact preflights and the balanced panel, and `audit.py` independently recomputes summaries and control flags. Engineering records stay on `codex/engineering-notes`; source changes stay on the experimental branch. Nothing is pushed.
