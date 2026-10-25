# Apple Silicon core placement for the CPU benchmark

Research date: 2026-10-25. Scope: the specified M4 Max with 12 P cores and 4 E cores. This investigation did not run benchmark workloads, change benchmark source, or change system scheduling.

## Decision

The strongest supported macOS path is to apply identical scheduling settings to every library condition and verify the actual core-type residency of every accepted measurement. I found no public Apple API in the inspected materials that guarantees P-only or E-only execution of arbitrary benchmark worker threads. QoS, `taskpolicy`, Mach affinity tags, and Game Mode do not provide such a guarantee.

This can support a claim such as "the accepted timed intervals were observed to execute only on P cores." It cannot support "macOS pinned these processes to P cores." A requirement for enforced affinity remains unmet without another supported mechanism or a different execution environment.

## Scheduling controls

| Control | Supported meaning | Placement conclusion |
| --- | --- | --- |
| QoS, including pthread QoS | Communicates the nature and importance of work to the scheduler. Apple says it influences P/E placement. | A preference, not a core mask. The same QoS in two conditions does not prove the same core type. |
| `taskpolicy -b` or `-c background` | Applies background process policy or a QoS clamp. The installed manual says children inherit policy. | No documented P/E binding contract. Background is a candidate way to encourage E-core execution, requiring measurement. |
| `taskpolicy -B` | Removes `PRIO_DARWIN_BG`. | Does not request or guarantee P cores. |
| `THREAD_AFFINITY_POLICY` | Historically expresses L2-cache-sharing hints between threads using arbitrary tags. | Tags are not CPU identifiers. Apple's current ARM affinity source returns zero supported affinity sets, and the setter rejects unsupported affinity. |
| Game Mode | Gives games more resources, reduces background activity, and improves Bluetooth latency. | No documented per-thread P/E selector. It changes the operating environment and is unsuitable as a claimed affinity mechanism. |
| `SCHED_RR` | Keeps selected periodic game threads at a fixed priority without priority decay. | Fixed priority is not fixed core type. Apple advises against using it for long-duration work. |

Sources: [Apple's Apple Silicon tuning guidance](https://developer.apple.com/documentation/apple-silicon/tuning-your-code-s-performance-for-apple-silicon), [Apple's AMP explanation](https://developer.apple.com/news/?id=vk3m204o), [Apple's taskpolicy manual source](https://github.com/apple-oss-distributions/system_cmds/blob/main/taskpolicy/taskpolicy.8), [Apple's affinity release notes](https://developer.apple.com/library/archive/releasenotes/Performance/RN-AffinityAPI/), [ARM affinity implementation](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/arm/cpu_affinity.h#L32), [Mach affinity policy rejection](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/kern/thread_policy.c#L484), [Game Mode and Sustained Execution Mode](https://developer.apple.com/videos/play/wwdc2025/209/?time=99), [Apple's game scheduling talk](https://developer.apple.com/videos/play/tech-talks/110147/?time=1109).

The installed SDK's `mach/thread_policy.h` also describes affinity as sharing an L2 cache "if possible." A read-only search of the installed public pthread and os headers found no additional core-type binding control. This is a bounded search result, not proof that every private or future Apple API lacks one. Apple's scheduling talk explicitly states that the system can make P cores unavailable under critical thermal conditions.

## Measure actual residency with process resource counters

Apple's Recount documentation explicitly lists `proc_pid_rusage` as returning overall totals plus a separate P-core-only value. The source implements the following chain:

1. Recount maps hardware clusters to performance or efficiency CPU kinds and records CPU resource use at context switches and user/kernel transitions.
2. `recount_task_usage_perf_only` reads task lifetime counters and isolates the performance CPU kind.
3. `task_power_info_locked` obtains total and performance-only usage. It assigns the P-only time, cycles, and instructions to the extra task statistics.
4. `fill_task_rusage` copies those values into `ri_user_ptime`, `ri_system_ptime`, `ri_pinstructions`, and `ri_pcycles`. Total time uses `ri_user_time` and `ri_system_time`.
5. `proc_get_rusage` copies the selected resource structure to userspace without converting these time values.

The exported time values in this inspected implementation are Mach absolute time units. Convert with `mach_timebase_info` for seconds. Ratios and differences can use the raw time units consistently. These are accumulated CPU times, not wall-clock durations and not periodic profiler samples.

For two valid snapshots bracketing completed benchmark work:

```text
all_cpu = delta(ri_user_time + ri_system_time)
p_cpu   = delta(ri_user_ptime + ri_system_ptime)
e_cpu   = all_cpu - p_cpu
p_share = p_cpu / all_cpu
```

The analogous instruction deltas provide a useful independent check of P/E execution. The source gates P-time assignment behind `CONFIG_PERVASIVE_CPI`; zero P-time alone therefore cannot establish E-only execution on an unvalidated platform. Require a successful V6 query, positive total counters, consistent deltas, and evidence that P counters work on this installed machine before using them as an acceptance rule.

These are process counters. They cover its task's threads, including native library workers and terminated threads retained in task lifetime accounting. They do not automatically supply the P/E breakdown of separate child processes. Measure every participating PID if a condition launches children. Snapshot collection and benchmark setup also consume CPU, so use the same bracketing method for every condition and state what the interval contains.

Important limit: reading a running task sums its per-CPU tracks sequentially. Accounting updates occur at execution transitions. It is not an atomic stop-the-world snapshot of every active worker. Take snapshots only after workers have reached a completion barrier or otherwise quiesced. Preserve the raw counters. Do not silently clamp a negative derived E delta, tolerate nonzero cross-type time while calling the interval "only P," or reinterpret an unsupported all-zero P counter as E-only. If strict zero cross-type execution cannot be established, report the measured residency mix and leave the strict requirement unmet.

Sources: [Recount documentation and API table](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/doc/observability/recount.md), [cluster-kind mapping](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/kern/recount.c#L121), [counter reads and kind isolation](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/kern/recount.c#L396), [task lifetime P-only aggregation](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/kern/recount.c#L805), [task power statistics and feature guards](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/kern/task.c#L6784), [resource field assignment](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/kern/bsd_kern.c#L1248), [resource export](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/kern/kern_resource.c#L3347), [public resource structure](https://developer.apple.com/documentation/kernel/rusage_info_current).

The inspected public XNU revision is `f6217f891ac0bb64f3d375211650a4c1ff8ca1ea`. Its implementation is primary evidence for field semantics, but it does not establish that the running proprietary kernel is byte-for-byte identical. Runtime support and counter behavior still need validation on the installed OS.

## Verify placement with Instruments

System Trace records scheduler activity. Apple's Thread State Trace records decisions that affect app threads and exposes per-process state changes and context switches. Use its CPU tracks and thread records to associate execution intervals with actual CPU identifiers and core types, restricted to the participating PIDs and timed benchmark range. Inspect the entire interval, preserve the trace, and check trace completeness. Do not infer process residency from aggregate system core activity or from counts returned by `hw.perflevelN.logicalcpu`.

A complete scheduler trace can show that all recorded running intervals for the relevant threads used the selected core type. It remains observed execution, not enforcement. A dropped-event or truncated trace cannot prove the absence of migration. Verify the installed Instruments trace schema and CPU-type mapping before automating an acceptance check.

CPU Profiler samples each CPU according to CPU cycles. It is useful for CPU cost analysis and cross-checking which core types were sampled, but sampling can miss short excursions. A P-only set of CPU Profiler samples alone is insufficient proof of continuous P-only residency.

Sources: [System Trace in Depth](https://developer.apple.com/videos/play/wwdc2016/411/), [Thread State Trace and System Load on Apple Silicon](https://developer.apple.com/videos/play/tech-talks/110147/?time=911), [Thread State Trace description](https://developer.apple.com/documentation/xcode/analyzing-the-performance-of-your-metal-app), [CPU Profiler sampling behavior](https://developer.apple.com/videos/play/wwdc2025/308/?time=530).

## Recommended next step

Validate the V6 counters and a short scheduler trace on an inert test process before changing the benchmark. Then use the same scheduling policy and native-thread limits for every library condition, capture residency per timed condition, and reject or separately label measurements with mixed or unverified placement. If the user requires enforced P-only or E-only affinity, state that the inspected public macOS mechanisms do not meet that requirement and do not start replacement runs under a false guarantee.
