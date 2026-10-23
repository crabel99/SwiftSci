# CSV boundaries, reference reads, and standalone memory

The corrected matched-interface panel completes 704 paired CPU workers and 864 fresh standalone memory workers. The independent audit records resource gates as **passed**, with 0 review flags. Full native outputs pass on every worker. These results compare cleanup `f9a99ce54c77909bdd6f95fadd5fa3b5d15490f2` with candidate `5d1f89a961106104757f2d8d0b8faba79487d100`.

Production source is unchanged. This is further qualification of the existing local CSV branch, not a new production optimization or a comparison with pandas or Polars. The broader earlier-parent results remain with [the previous resource study](../2026-10-22-csv-fallback-isolation/README.md).

## A diagnostic build error was corrected first

The eager extension exposed an import-order mistake in [the earlier paired study](../2026-10-23-csv-paired-reads/README.md). Its link commands searched a general dependency directory before the explicit reader-module directories. The compiler loaded a cached `SwiftDataFrame` interface while linking the candidate or cleanup object. The eager extension failed to link because that interface referenced an internal function not exported by the matched object.

The [correction record](build-correction.json) retains the failure and both module-loading paths. Corrected link commands put explicit modules first. Every new link emits a compiler module-loading log and asserts the paths of `SwiftDataFrame`, `CSVBaseline`, and `CSVClone`. This check is executable, so the lesson does not depend on another prose instruction. The standalone memory probes already prioritize their own modules, as their recorded commands confirm.

The earlier paired workers and their observed outputs remain preserved. Their performance interpretation is superseded by corrected repeats. All 900 controls were repeated before expansion, including the reciprocal binary that keeps cleanup's real module name. Shared-table candidate CPU stays within about 1.1% of cleanup on those targeted cases, and every corrected shared-table control passes.

Separate-table diagnostic comparisons still produce candidate CPU warnings in the recurring 3,392-row parallel case. Their same-source CPU-ratio distributions remain broad. They do not reproduce a matched-table source regression. The earlier 14.5% aggregate same-source warning is not a corrected-build qualification result and must not be reused as one. [Corrected controls](corrected-audit.json) and exact raw responses preserve that distinction.

## The expanded panel keeps the same constraints

All 26 prior boundary combinations remain in the panel. They include eager and streamed reads, both conversion policies, rows adjacent to prefix admission, and zero or high null injection. Another ten combinations use full Aotizhongxin air-quality data and full household-energy data. The original two-token household stream remains a specialization control alongside the default multi-token configuration.

The paired readers receive value copies of one immutable native Set without mutation. They use identical input bytes, schema, null tokens, row limits, and chunk sizes. Matching types, values, null positions, and row and column order are checked before and after timing. Every timed read checks its row count. Hashing and CPU scheduling remain native, and all runs require AC power. No observation is trimmed, worker budget capped, or tolerance relaxed.

Input files are warm from validation and warmup reads. Caller configuration is prepared outside the timed public API call. These results do not measure cold-disk startup.

Boundary combinations use 24 independent workers, two warmup blocks, and eight timed blocks per comparison. Reference combinations use eight independent workers, one warmup block, and two timed blocks. ABBA and BAAB blocks balance order; comparison order rotates between workers. Repeated reads within one worker are not independent samples. The unchanged CPU gate reviews candidate increases above 10%, and checks same-source and same-implementation controls in both directions.

## Resource results

The [complete table](results.md) keeps CPU, elapsed time, and independent peak memory separate. Across the ten reference combinations, paired median CPU changes range from -24.80% to +1.96%. Those configurations have different workloads, so that range is not an overall speedup or a weighted production average.

Peak memory comes from separate uninstrumented processes, using actual standalone cleanup and candidate objects and clients. Each case has eight workers per label. A second label runs the identical cleanup binary as a memory control. Peak RSS is captured before full-output validation. Eager output remains held for the capture; streaming consumes and releases chunks without consumer retention. The maximum candidate-minus-cleanup median peak difference across all 36 combinations is +1.19 MiB.

The memory gate remains 5% plus 8 MiB, with a two-sided identical-binary control. RSS is a process high-water mark, not an allocation count. CPU from the independent-process memory stage is retained as diagnostic data and is not substituted for the paired CPU verdict.

## Validation and disposition

The [independent audit](audit.json) recomputes all expanded resource flags from raw observations, checks counts and balanced order, and verifies module-loading logs and binary hashes. There are 2,468 new worker responses including corrected repeats. The 704 expanded paired workers complete 61,824 timed public reads and 4,224 full native validation reads. Standalone workers also validate every output against the independent contract.

The 394-test Release, Debug, and Address Sanitizer results remain with the actual head's earlier verification. No production source or compiled reader object changed during this follow-up, so those suites were not repeated. These CSV checks are not full numerical certification. Our builds finish before associated timing; unrelated host activity remains uncontrolled.

Module aliases and a combined linked client remain limits of the paired CPU method. Native table setup includes hashing and allocation layout. These experiments do not prove a particular hash-bucket, cache, SRAM, allocator, or scheduler mechanism. Prior flags remain historical observations, and the flawed-interface study remains visibly marked.

The work remains local. Nothing is pushed or submitted. The corrected resource evidence supports review of this candidate under the stated cases and controls; it does not establish that CSV optimization is exhausted.

- [Resource results](results.md) and [raw-data audit](audit.json)
- [Frozen case plan and hypotheses](plan.json)
- [Module-import correction](build-correction.json) and [verified panel build](panel-build.json)
- [Boundary decision](expanded-boundary/decision.json), [reference decision](expanded-reference/decision.json), and [memory decision](standalone-memory/decision.json)
- [Input contracts](input-contracts.json) and [worker counts and uncompressed hashes](worker-index.json)
- [Controllers, probe, source snapshots, generated boundary inputs, and build logs](experiments.tar.gz)
- [Artifact hashes](artifact-sha256.json)

The archive preserves recorded paths and pinned module dependencies. Full reference datasets stay with their existing owner and are identified by immutable hashes in the contracts. Redirect declared scratch and dependency paths when reproducing on another machine. Raw worker JSONL is stored as exact gzip streams. No binaries or build caches are committed.
