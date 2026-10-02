# Memory prototype sequence results

Completed October 1, 2026 on `codex/unified-memory-prototype`, ending at `7c0e2d565dfe1e061bf83c86f990471263fd5f16`. All commits remain local. Production `Sources/` files are unchanged.

Retained selections and one-time gathering improve the checked file-to-fit workflow. Chunked storage reduces copying for localized edits under snapshots, but broad edits and indexed reads favor contiguous columns. Shared MLX imports work through a tested C adapter, yet the pinned Swift managed initializer leaks its captured owner. Shared imports did not improve this trial's full GPU interval.

The [integration proposal](2026-10-01-memory-integration.md) explains the recommended sequence and compatibility requirements. The [MLX dependency report](2026-10-01-mlx-managed-finalizer.md) records the isolated owner-release failure.

## Verification scope

| Final qualification | Result |
|---|---:|
| Existing prototype numerical, selection, ownership and Metal checks | 401 scenarios passed |
| Snapshot mutation, append and chunk-boundary checks | 151 scenarios passed |
| Direct device adapter, release, alignment and abandoned-graph checks | 9 scenarios passed |
| Mutation comparison | 360 validated fresh processes |
| Public CSV and Parquet workflow comparison | 60 validated fresh processes, 180 fits plus independent replays |
| Device comparison | 90 validated fresh processes, each with a warmup |
| Pinned Swift managed-import wrapper | One retained failure, recorded separately |

These are 561 passing prototype scenarios and 510 final measured processes. They are not the full SwiftSci test suite or a production numerical certification. No tolerance changed. Matrix and prediction checks retain the established analytical and production-reference limits.

Measurements used Release builds on Apple M4 Max with 128 GiB, Swift 6.4 and macOS 27.0, on AC power. Controllers remove thread-count overrides and rotate variants across five rounds. Table timings are medians. RSS is process high-water memory, not exact live allocations or GPU residency. Owner byte counts exclude Swift metadata, other libraries and allocator overhead.

## Snapshot mutations

The table covers one million rows, five generations and all five previous snapshots retained. Each generation edits the current column while every older snapshot must remain unchanged. Values and null state are checked after memory sampling.

| Edit pattern | Layout | Five edits, ms | Following indexed scan, ms | Existing payload copied, MB |
|---|---|---:|---:|---:|
| One value per generation | whole | 2.147 | 0.665 | 40.625 |
| One value per generation | chunk4096 | 0.040 | 1.190 | 0.166 |
| One value per generation | chunk65536 | 0.165 | 1.194 | 2.662 |
| 1,024 nearby values | whole | 2.064 | 0.675 | 40.625 |
| 1,024 nearby values | chunk4096 | 0.036 | 1.206 | 0.166 |
| 1,024 nearby values | chunk65536 | 0.174 | 1.178 | 2.662 |
| 1,024 scattered values | whole | 2.105 | 0.675 | 40.625 |
| 1,024 scattered values | chunk4096 | 3.268 | 1.216 | 40.602 |
| 1,024 scattered values | chunk65536 | 2.477 | 1.211 | 40.625 |
| All values | whole | 11.410 | 0.652 | 40.125 |
| All values | chunk4096 | 21.669 | 1.000 | 40.125 |
| All values | chunk65536 | 19.199 | 0.991 | 40.125 |
| 1,024 nearby null changes | whole | 2.126 | 0.673 | 40.625 |
| 1,024 nearby null changes | chunk4096 | 0.038 | 1.204 | 0.166 |
| 1,024 nearby null changes | chunk65536 | 0.165 | 1.200 | 2.662 |
| Append 1,024 values per generation | whole | 11.143 | 0.682 | 40.708 |
| Append 1,024 values per generation | chunk4096 | 0.039 | 1.194 | 0.073 |
| Append 1,024 values per generation | chunk65536 | 0.219 | 1.191 | 0.772 |

Single-value edits copy 40.625 MB with whole-column storage and 0.166 MB with 4,096-element blocks. Their peak owner payload falls from 48.75 MB to 8.29 MB. Scattered edits touch almost every block, so their copying advantage disappears. The smaller 10,000-row cases and runs without retained snapshots remain in the raw results.

The initial block implementation grouped every edit through a dictionary. Ordered dense batches took about 200 ms. A separate commit bypassed grouping for ordered runs and reduced that cost to about 19–22 ms. Whole-column edits still take about 11 ms. This result supports keeping contiguous storage for dense work.

The indexed scan includes a block lookup for every element. It does not measure a block-aware vectorized loop. Appends allocate exact sizes without spare capacity. Their results do not establish a win over an amortized contiguous append builder. Copy counters describe requested existing payload, not measured DRAM traffic.

## Public file ingestion through repeated fitting

The generated files contain eight numeric features, nulls, known repair markers and analytical targets. Both public readers load the files. Each strategy converts the dataframe, retains its pre-edit snapshot, repairs one column, filters and stably sorts, then fits three distinct training splits.

The table includes parsing, conversion, repair, selection-cache setup, matrix preparation, fitting and prediction. It excludes file generation and explicit result-proof scans. `sequence_ns` in the raw results includes those scans and cleanup. Every file cell and repair is checked, and each transformed result is replayed through independently generated production input.

| Format, one million rows | Strategy | Complete work, ms | Parsing, ms | Conversion, ms | Peak RSS, MB |
|---|---|---:|---:|---:|---:|
| csv | prepared | 1541.37 | 701.20 | 13.78 | 579.81 |
| csv | selection | 1094.34 | 700.59 | 11.88 | 524.44 |
| csv | gather | 988.14 | 695.35 | 11.49 | 576.45 |
| parquet | prepared | 1386.35 | 551.97 | 12.92 | 631.98 |
| parquet | selection | 944.89 | 555.07 | 10.82 | 519.88 |
| parquet | gather | 844.77 | 551.02 | 10.87 | 571.92 |

Retained selections reduce the CSV workflow by about 29% and the Parquet workflow by about 32%. Gathering once improves them by about 36% and 39%, respectively, with greater retained memory than selections. These are complete comparisons of the tested pipeline strategies, not isolated claims about a storage allocator.

Parsing remains a large part of the workflow. The trial uses real readers over synthetic scientific observations with exact binary feature values. It does not measure cold disk reads, arbitrary decimal ingestion, strings or application-specific datasets. The original dataframe and the pre-edit numerical snapshot remain retained for every strategy. The 100,000-row results and file hashes are retained with the evidence.

## Shared device buffers

A separate executable keeps MLX initialization out of the CPU comparisons. It tests copying Float32 imports, direct C managed imports, and Double-to-Float32 conversion followed by a managed import. The input pointer and the completed MLX output pointer must match the intended shared allocations. Every GPU and Metal result is checked.

| Float elements | Import | Host edit during submitted read | Import, microseconds | Import plus completed GPU interval, microseconds | Host payload detached, MB |
|---|---|---|---:|---:|---:|
| 1,048,576 | copy | no | 53.92 | 609.29 | 0.000 |
| 1,048,576 | managed-c | no | 8.50 | 623.75 | 0.000 |
| 1,048,576 | convert-managed-c | no | 8.83 | 685.29 | 0.000 |
| 1,048,576 | copy | yes | 54.54 | 625.04 | 0.000 |
| 1,048,576 | managed-c | yes | 9.08 | 1085.08 | 4.194 |
| 1,048,576 | convert-managed-c | yes | 8.38 | 1075.88 | 4.194 |
| 4,194,304 | copy | no | 209.58 | 1100.42 | 0.000 |
| 4,194,304 | managed-c | no | 15.92 | 1226.83 | 0.000 |
| 4,194,304 | convert-managed-c | no | 28.08 | 1270.38 | 0.000 |
| 4,194,304 | copy | yes | 208.79 | 1209.38 | 0.000 |
| 4,194,304 | managed-c | yes | 14.83 | 4085.96 | 16.777 |
| 4,194,304 | convert-managed-c | yes | 27.17 | 4115.12 | 16.777 |

Managed imports avoid the explicit import copy. They do not beat the copying path's full interval in this small arithmetic trial. When the host edits a retained source, copy-on-write moves the copy to the writer. A shared pointer is therefore evidence of avoided materialization at that seam, not proof of a faster model.

The GPU interval includes graph submission, any overlapping host edit and synchronization. The combined figure excludes an intervening pointer-identity check and excludes source construction, dtype conversion and the subsequent Metal consumer. Those stages have separate raw timings. This is not an end-to-end application latency metric. Device timing can include scheduling noise. No hardware-counter attribution or universal dispatch threshold was established.

The final device executable uses a package-module seam for shared generic storage. Earlier combined-executable timings are retained for diagnosis but must not be mixed with the final table as if they used the same build structure.

Float32 conversion uses Accelerate and leaves the Double source unchanged. The maximum rounding difference in the tested fixture is about 2.616e-5. Every subsequent result agrees with its explicitly rounded Float32 reference. This fixture does not justify reducing precision for arbitrary scientific data.

Page-aligned contiguous imports and page-aligned extents pass. A nonconforming extent takes a checked copy path. Null imports are rejected. Owners release after completed work and after a lazy graph is abandoned before submission. Cancellation after submission, arbitrary slices, external Arrow buffers and concurrent writers remain unqualified.

## Retained dependency failure

The pinned mlx-swift 0.31.6 wrapper calls its finalizer once but keeps the captured lease and 16 KiB source alive after synchronization and cache clearing. Its retained callback state has no matching release in the inspected trampoline. The reproducer records `known_failure`; the adapter checks do not waive that failure.

The prototype C adapter supplies an explicit retained lease as the callback payload and releases it once through the C destructor. All adapter lifetime checks pass. No dependency code was changed, no public issue was opened, and no production path was switched to this adapter.

## Commit and evidence record

The implementation sequence is:

- `a4e3aede61`: snapshot mutation and append comparison.
- `a4fd1e952d`: ordered block mutation path.
- `551d37115b`: public file ingestion, snapshot repair and repeated fitting.
- `7c0e2d565d`: separated MLX executable, direct C adapter, dtype conversion and retained wrapper-failure reproducer.

Each suite records source hashes, its binary hash and build command. Final CPU evidence predates only changes to the separate device trial and README. A file-by-file audit confirmed that every CPU compilation input matches the committed implementation. Device compilation inputs also match. Documentation changes do not alter the tested binary.

Raw JSON remains in the local evidence archive under `mutation-final`, `ingestion-final` and `device-final`. Earlier experiments remain in separately named directories. Fixture generation is deterministic and file hashes are retained; generated CSV and Parquet files are not duplicated into this evidence archive. Local build manifests contain local filesystem paths and are not copied into the public engineering-note branch.

The engineering recommendation is to integrate retained selections and prepared numerical consumers first. Block mutation and device sharing should remain opt-in development paths until their broader qualification is complete.
