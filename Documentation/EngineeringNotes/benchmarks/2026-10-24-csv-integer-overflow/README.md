# CSV signed-integer overflow fix

Retain `58db37c4b3c97b287186c377f76f89abcbbb0b0d` on local branch `codex/csv-integer-overflow`, based on `575f2f63cbd3c35c0611ba3a977b066b2e4fd390`. Nothing is pushed and no PR is opened. Engineering records stay on `codex/engineering-notes`.

The byte parser now accepts the smallest signed integer and returns nil for out-of-range input. The retained implementation avoids the first candidate's extra overflow-flag work. The final integer queues use 0.7% less CPU with optional storage and 0.2% more with compact storage. The larger reference queues use 0.4–1.9% more. The detailed cases below retain both improvements and increases.

## Failure and correction

The old parser builds a positive magnitude with trapping arithmetic, then applies the sign. The magnitude of Int.min cannot fit in Int. Both larger positive and smaller negative decimal values also trap before the CSV decoder can apply its existing invalid-value handling.

The focused native regression fails before the patch with an arithmetic-overflow crash. In separate public CSV processes, Int64.max passes while Int64.min and the two adjacent out-of-range values terminate with SIGTRAP. All four pass after the fix.

The patch accumulates negative digits with reporting-overflow arithmetic. Each overflow check immediately follows its arithmetic operation. Negative input returns that value directly. Positive input uses checked negation. Quotes, signs, whitespace, full-token validation, null matching, inference rules, and storage representation stay as before. There is no public API change or new allocation.

## Correctness checks

The full dataframe suite passes 447 Debug and 447 Release tests, with no failures or skips. Seven small regression tests cover signed limits, out-of-range decimals, formatting, malformed tokens, long zero padding, serial and parallel explicit schemas, and exact inferred integer limits.

An independent Python integer and range oracle checks all native values and nulls in a deterministic 6,796-row corpus in both Double storage modes. It includes random signed integers, signed-boundary neighborhoods, up to 200-digit decimals, malformed tokens, Unicode whitespace, ASCII whitespace, and long zero padding. Expected null count is 630. Each complete output hash matches.

The first corpus check exposed a mistake in the auxiliary String-column oracle: it encoded a UInt64 length instead of the worker's UInt32 length. Integer hashes and null counts already matched. The corrected oracle follows the unchanged worker format. Both the failed diagnostic and corrected results are retained.

## Matched integer resource comparison

Five fixed inputs contain 8,192 rows and eight columns. Four use varied short, long, whitespace-padded, or mixed and null integers. The fifth is a Double control. Every build gets the same full schema, native output checks, custom null set, native CPU parallelism, and power policy. Eight rotated rounds include twins, four callers, and 640 reads per queue. No tolerance or worker-budget change was made.

| Input | Storage | Parent CPU ms/read | Fixed CPU ms/read | Change |
| --- | --- | ---: | ---: | ---: |
| short-integers/read | optional | 0.985 | 0.950 | -3.57% |
| long-integers/read | optional | 1.919 | 1.910 | -0.49% |
| formatted-integers/read | optional | 1.338 | 1.383 | +3.33% |
| mixed-integers/read | optional | 1.032 | 1.003 | -2.76% |
| double-control/read | optional | 0.971 | 0.970 | -0.05% |
| short-integers/read | compact | 0.977 | 0.950 | -2.72% |
| long-integers/read | compact | 1.904 | 1.910 | +0.29% |
| formatted-integers/read | compact | 1.337 | 1.378 | +3.02% |
| mixed-integers/read | compact | 1.026 | 1.000 | -2.53% |
| double-control/read | compact | 1.007 | 1.010 | +0.33% |

These are summed operation CPU milliseconds, not wall time, energy, FLOPs, or normalized work across performance and efficiency cores. Negative changes use less CPU. Small differences are observations on this machine and link layout, not universal speed claims.

## Complete reference workflows

The larger panel uses the existing 35,064-row Aotizhongxin air-quality dataset and 2,075,259-row household-electricity dataset. Each read and read-sort-matrix workflow retains identical schemas, null policies, input hashes, native values, stable sorting, and matrix hashes for both builds. It uses eight rotated rounds, twins, four callers, and fixed 128-job queues.

| Input and workflow | Storage | Parent CPU ms/job | Fixed CPU ms/job | Change |
| --- | --- | ---: | ---: | ---: |
| Aotizhongxin-default/read | optional | 13.961 | 14.133 | +1.23% |
| Aotizhongxin-default/sort-matrix | optional | 19.727 | 19.623 | -0.53% |
| energy-common/read | optional | 308.791 | 313.386 | +1.49% |
| energy-common/sort-matrix | optional | 631.831 | 632.051 | +0.03% |
| Aotizhongxin-default/read | compact | 13.695 | 13.856 | +1.17% |
| Aotizhongxin-default/sort-matrix | compact | 18.776 | 18.923 | +0.78% |
| energy-common/read | compact | 319.077 | 323.634 | +1.43% |
| energy-common/sort-matrix | compact | 604.559 | 616.880 | +2.04% |

## Queue CPU and memory

| Panel | Storage | Charged CPU change | Wall-time change | Parent sampled peak MiB | Fixed sampled peak MiB |
| --- | --- | ---: | ---: | ---: | ---: |
| integer-final-workflows | optional | -0.74% | -0.81% | 57.98 | 58.14 |
| integer-final-workflows | compact | +0.15% | -0.54% | 58.14 | 58.17 |
| reference-final-workflows | optional | +0.44% | +1.68% | 3506.88 | 3505.10 |
| reference-final-workflows | compact | +1.91% | +1.93% | 2511.62 | 2509.79 |

Charged CPU includes worker and measured controller CPU. Sampled RSS is the combined resident size of the four callers. Conservative sums of per-process kernel peaks remain below the unchanged 4 GiB ceiling. These are upper bounds, not simultaneous peak measurements. The patch changes no data storage and does not establish a memory reduction.

## Rejected first candidate

The first correct candidate checks both overflow flags together. Its qualified integer panel uses 5.5–6.7% more charged CPU. Generated instructions materialize overflow Booleans before testing them. Checking immediately after each arithmetic operation removes that extra flag handling. The initial larger reference run was interrupted after this diagnosis and is excluded from acceptance evidence. Its partial records and interruption are retained.

## Receipts and scope

Both final panels pass the existing twin CPU, wall-time, and memory controls. The audit recomputes queued jobs, charged CPU, raw memory summaries, source hashes, binary hashes, and every preflight and postflight full-output check. The final worker's 51 measured source hashes match the final source commit. The parent differs only in the parser among those measured files. Historical build receipts are unchanged. provenance.json maps their exact source hashes to the named commits.

Only the parser and regression test belong to the source commit. This record, raw measurements, compiler evidence, and reproducible experiment scripts belong to the notes branch. The archive omits compiled binaries, caches, raw CSVs, and xcresult bundles. It contains their hashes, commands, contracts, and summaries.

This validates the dataframe slice locally. It does not claim the full MLX-dependent suite, hosted CI, or Codecov have passed. The original baseline crash is resolved here, not waived or retroactively removed from the earlier report.
