# Concurrent CPU admission and shared caches

## Decision

Commit `4a488b52799cbf3b173b8d3b9b2606588cd2f265` on `codex/memory-kernel-trial` adds a CPU concurrency benchmark and public admission guidance. The baseline is `a356fd07a739da9f8eca38db7a7b275f880c4e6e`. Production Swift code and default policies are unchanged. Cache policy and admission policy remain separate caller decisions.

For repeated fixed-split model fits, shared scaled input provided the strongest combined throughput and memory result in this experiment. Higher admission limits improved batch throughput in most cases but increased per-job service time and peak memory. Do not set one global concurrency default from these results. This report belongs only to `codex/engineering-notes`.

## Workload and accounting

Each fresh process submits eight independent CPU LinearRegression models. They share one immutable prepared or scaled input cache for each distinct shape. The workload is a noise-free synthetic linear relation, with 128 held-out observations per model. Uniform workloads use 100,000 × 8, 100,000 × 32 or one million × 4 training values. A mixed workload alternates narrow and wide job definitions. Task scheduling determines actual arrival order; the experiment does not impose a deterministic admission sequence.

A shared reservation covers three times the source numerical payload plus a 64 MiB runtime allowance. It is acquired before cache construction and remains held until all consumers finish. Keeping the construction estimate for that entire lifetime deliberately overestimates steady cache memory. Each job separately reserves twelve feature buffers, four row buffers and a 64 MiB allowance. These conservative estimates are experimental capacities, not calibrated production recommendations.

The total limit is the shared reservation plus one, two, four or eight times the largest job estimate. These budget units equal a maximum admitted-job count only for uniform jobs. The mixed workload reached five admitted jobs at four units. Every run released all reservations and stayed within its declared reservation limit. This does not prove that the budget enforces process RSS; it does not intercept allocation.

Queue time begins when a task requests admission. Service time begins after admission and includes subsequent scheduling. Completion time begins at batch submission. Batch throughput excludes cache setup; setup-inclusive batch time is reported separately. CPU time covers the process and its native numerical worker threads. RSS includes cache construction and is sampled before reference calculations.

## Results

Three interleaved rounds completed 96 processes and 768 jobs on the Apple M4 Max host. Native thread settings were retained, thread-count overrides removed, and AC power checked. Each process passed an independent row-array replay for exact fitted scaler parameters, exact model parameters and complete held-out predictions. Analytical target checks also passed.

The table shows medians for eight wide jobs sharing scaled input. RSS uses decimal MB. Median service time describes admitted execution; median completion includes queueing. They answer different latency questions.

| Budget units | Jobs/s after setup | Setup + batch ms | Median service ms | Median completion ms | Peak RSS MB |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 8.39 | 987.3 | 117.9 | 539.8 | 94.4 |
| 2 | 10.88 | 769.3 | 181.0 | 468.2 | 121.1 |
| 4 | 16.89 | 507.5 | 232.4 | 353.0 | 177.3 |
| 8 | 26.41 | 336.8 | 284.9 | 284.9 | 283.4 |

Eight units delivered about 3.15 times the throughput of one unit for this workload. Peak RSS rose from about 94 MB to 283 MB, and median service time rose from about 118 ms to 285 ms. The whole batch and its median completion nevertheless improved because queueing fell. Eight was the largest tested concurrency, not an established optimum.

At eight units, sharing scaled rather than unscaled wide input increased throughput from 23.35 to 26.41 jobs/s, about 13%, and reduced peak RSS from 467 MB to 283 MB, about 39%. This avoids repeated preprocessing and its per-job output buffers. The experiment did not collect hardware counters, so it cannot assign the gain to a particular cache or bandwidth mechanism.

The tradeoff varies by shape. For narrow jobs with unscaled input, moving from four to eight units gained only about 7% throughput while increasing peak RSS from 87 MB to 139 MB. For the million-row shape, two units were slightly slower than one; eight scaled-input units reached about 2.35 times one-unit throughput while using about 440 MB rather than 128 MB. More admitted work is therefore not a reliable rule for improving every latency or resource measure.

Mixed-job measurements confirm byte-based admission can use space for smaller jobs. They do not establish FIFO fairness or quantify head-of-line blocking because task arrival order varies. Raw request, queue, service and completion measurements are preserved for further analysis.

## Qualification and limits

Uniform workloads with more than one budget unit must observe overlapping admitted jobs. All such checks passed. The overlap counter includes suspended work, so it does not prove simultaneous solver instructions. Process CPU time also includes native library threads. Throughput is the observed outcome; a scheduling trace would be needed to attribute exact execution overlap.

Two read-only reviews found no remaining ownership, numerical-contract or accounting issue after the overlap gate was added. The controller's success, nonzero-exit and timeout-diagnostic paths were tested. Final smoke checks cover serial uniform, concurrent uniform and mixed admission.

The only change after timing was public documentation. All measured executable inputs match the final build, whose complete source fingerprint matches the committed files. Production Swift is unchanged, so the full production Debug/Release suites were not repeated. Their two previously recorded MLX precision failures remain unresolved. This experiment does not qualify GPU concurrency, cancellation races, arbitrary model algorithms or an automatic scheduling policy.

The public guide now states the nested-reservation requirement: the limit must accommodate retained shared storage and the largest additional job estimate together. Otherwise an inner request can wait indefinitely for capacity held by its outer scope. MemoryBudget cannot infer these ownership dependencies. The benchmark constructs a limit that satisfies this requirement before starting work.

## Reproduction and next work

Run `python3 Benchmarks/UnifiedMemoryPrototype/concurrent.py --build --output /tmp/swiftsci-concurrent`. The runner rotates cache/budget configurations, verifies executable and source fingerprints, and preserves raw samples and failures. Local evidence is archived under `~/local-ai/spl/swiftsci/concurrent-admission-20261005/`.

CPU balancing now has measured cache, latency, throughput and memory tradeoffs. The next distinct qualification is mixed CPU/GPU consumers under the same admission budget, including device-completion ownership. Keep that separate from the CPU results. Calibrate estimates against the intended workload before treating them as production limits, and retain caller control over the objective.

Implementation and engineering notes remain local. Nothing was pushed or submitted.
