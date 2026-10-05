# Balancing memory and execution time

## Decision

Keep compact columns as owned storage and qualify a bounded tiled traversal for StandardScaler. It recovers execution time while retaining the prepared path's lower memory use in the larger fixtures. Do not introduce a global speed-versus-memory switch from these results.

The production integration checkpoint remains `5c092885fd20a80f8b321570cb22de356235882d` on `codex/memory-kernel-trial`. All candidates and instrumentation were built in isolated source snapshots. Production sources, the parent prototype and public interfaces were not changed. This report belongs only to `codex/engineering-notes`.

## Diagnosis

Five fresh-process pairs reproduced the 100,000 × 8 ordinary retained-input gap. Median workflow time was 85.71 ms for rows and 89.14 ms for prepared input. Conversion fell from 7.53 ms to 5.05 ms, but fitting rose from 43.52 ms to 49.34 ms. Peak RSS fell from 54.0 MB to 46.1 MB.

Temporary stage instrumentation separated scaler fitting, scaler transformation, solver work and prepared finite-value scans. Prepared scaler fitting was faster, while transformation and solver work were slower. Two finite scans cost under 0.6 ms together. Removing validation would address little of the measured gap and would weaken the consumer contract, so it was not tested as an optimization.

Three hypotheses guided the investigation:

1. Prepared scaling pays for repeated column-to-row gathering and per-element output-column mutation. A tile should reduce repeated buffer access and write columns in batches while preserving row-width vDSP arithmetic.
2. Preparing simple array descriptors once might reduce solver access overhead. This can share value buffers without duplicating numeric payloads.
3. Duplicate finite scans might dominate. The instrumented cost ruled out that explanation for most of the gap.

The descriptor candidate did not show a reliable benefit. Its screened workflow median was 81.74 ms versus 80.98 ms for the original prepared control; fitting was essentially unchanged. Do not carry that extra implementation forward. The instrumented solver timings alone did not justify attributing the gap to descriptor access.

## Tiled candidate

The candidate gathers a bounded set of rows from compact columns into one row-major scratch tile. It applies the existing row-width vDSP addition and division, then scatters the results into output columns through scoped buffers. It reuses the tile throughout the transform. Output column allocations and solver workspaces remain necessary.

Screening covered 16, 64 and 256 KiB scratch limits, a descriptor-only version and a combined version. Five rotated rounds covered seven variants, 35 process measurements. A same-build no-option control matched the original binary closely. The 16 and 64 KiB options had similar fit times; 256 KiB provided no reliable extra benefit. The combined version did not establish a benefit from descriptors beyond tiling alone.

The initial build of the temporary profiler failed because its added timer/log code needed a Foundation import. The corrected profiler built successfully. That failed build never changed the library branch. Instrumented times are diagnostic only; all comparison timings use uninstrumented binaries.

## Qualification

Both the 16 and 64 KiB candidates passed 44 existing public regression scenarios, five additional checks and 32 existing NIST snapshot comparisons. Across the two settings that is 88 scenarios and 64 NIST comparisons. Tests cover CPU/GPU/automatic routes, snapshot mutation, noisy and poorly conditioned inputs, underdetermined fallback, invalid input and admission. Existing CPU comparisons require exact fitted parameters and predictions against the row-array path. Existing GPU and NIST tolerances were unchanged.

The numerical solver, reduction order, requested devices and dtype policy did not change. The experiment is not permission to relax any precision contract. It does not replace the dedicated scaler regression suite or full Debug/Release validation required before promoting the candidate.

## Broader comparison

Three rotated fresh-process rounds cover five shapes and four variants, 60 checked processes. Construction is separate from workflow timing. Workflow includes selection, conversion or preparation, fitting and prediction. Independent reference checks follow timing and the peak-RSS measurement. These are exploratory medians without confidence intervals.

| Training shape, data, treatment | Rows ms | Prepared ms | 16 KiB tile ms | 64 KiB tile ms | Rows RSS MB | 64 KiB tile RSS MB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1,000 × 4, ordinary, retain | 10.66 | 9.58 | 10.11 | 10.24 | 15.5 | 15.6 |
| 100,000 × 4, ordinary, retain | 64.98 | 60.57 | 59.04 | 58.39 | 41.0 | 33.2 |
| 100,000 × 8, noisy, materialize | 84.95 | 86.56 | 83.25 | 83.56 | 61.1 | 53.3 |
| 100,000 × 32, ordinary, retain | 191.27 | 209.33 | 184.83 | 184.18 | 137.6 | 123.5 |
| 1,000,000 × 4, ordinary, retain | 688.37 | 593.05 | 582.95 | 580.51 | 276.1 | 196.0 |

The 64 KiB tile reduced the 100,000 × 32 prepared workflow by about 12%, from 209.33 ms to 184.18 ms. Its peak RSS remained below the row-array path. At one million × 4, the tiled path took 580.51 ms and 196.0 MB, versus 688.37 ms and 276.1 MB for rows. Relative to the existing prepared path, the million-row gain was about 2%; most of its advantage over rows already came from compact storage.

The small case is mixed: tiling took about 0.5 to 0.7 ms longer than prepared input without tiling. Cold process/model setup contributes to these measurements. Do not infer a precise crossover from five shapes or claim a universal speedup. Broader scaling-only tests should separate fixed overhead from transformation work before choosing a default threshold.

The host was an Apple M4 Max with 128 GiB unified memory. Reported cache sizes were 128 KiB L1 data and 16 MiB L2 for the performance cluster, and 64 KiB L1 data and 4 MiB L2 for the efficiency cluster. Tests used AC power and cleared thread-count overrides. A tile-size result is not proof that it fits every active core's available cache; other data and threads share those resources. Hardware cache-miss and allocation counters were not collected. The experiment identifies a useful traversal change, not the exact fraction of gain attributable to cache locality, buffer access or uniqueness checks.

## Policy design

Keep storage ownership, temporary workspace, reuse and scheduling separate:

| Decision | Proposed treatment |
| --- | --- |
| One pass over a selection | Retain an immutable selection when its source lifetime is acceptable; use bounded scratch for traversal. |
| Repeated fits or scans | Compare one-time materialization and reusable prepared data against repeated gathering; amortize preparation over measured reuse. |
| Temporary numerical work | Use a bounded internal tile first. Consider caller-owned reusable workspace only if repeated allocation is measured as a remaining cost. |
| Several concurrent jobs | Share an estimated-byte budget. Measure completed work per second and peak memory under contention, not just isolated job latency. |
| CPU/GPU consumers | Select layout and dtype for the consumer. Keep precision policy separate from memory treatment. Retain input owners until device completion. |

Apple documents shared storage for CPU/GPU access on unified memory and requires completion ordering before the other processor accesses it. [Storage modes for Apple GPUs](https://developer.apple.com/documentation/metal/choosing-a-resource-storage-mode-for-apple-gpus), [shared storage synchronization](https://developer.apple.com/documentation/metal/mtlstoragemode/shared). In this library, shape packing and Double-to-Float conversion still allocate and move values even though CPU and GPU share physical memory. A general zero-copy claim would be inaccurate.

The existing production `MemoryBudget` limits declared reservations; it does not enforce a process-memory ceiling. Scratch belongs in the operation estimate, and reused caches or model state must remain accounted for across calls. Do not add an unbounded global workspace cache or select policy solely from nominal free RAM.

## Next implementation sequence

1. Promote only the tiled scaler candidate after adding direct scaler tests for small inputs, tile boundaries, widths, empty batches and NaN/missing-value behavior. Retain the exact arithmetic contract. Measure small-case overhead before selecting a threshold.
2. Compare repeated preparation and workspace reuse across one, three and many fits, measuring total time and retained bytes. Use explicit lifetime ownership if reuse earns its complexity.
3. Measure throughput under shared admission with concurrent CPU/GPU work. Choose scheduling from latency, throughput and memory evidence, without treating lower single-operation time as a universal policy.

No candidate was committed, pushed or made a default. The production integration's two known MLX rotary-precision failures remain outside this experiment.

## Evidence

The local archive is `~/local-ai/spl/swiftsci/memory-balance-20261005/`. It contains the baseline pairs, profiler traces, source archive, candidate patches, executable hashes, screening samples, broader samples and numerical qualification. Scripts reproduce the isolated builds and comparisons using this machine's existing dependency cache. The ordinary benchmark executable was restored to the exact integration-control hash after the experiment.
