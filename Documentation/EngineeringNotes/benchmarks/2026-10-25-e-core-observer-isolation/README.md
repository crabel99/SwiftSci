# E-core observer isolation

This experiment repairs benchmark observation while preserving the original `e-core-application-v1` profile. It changes benchmark tooling only. It does not change production SwiftSci algorithms or establish a performance baseline.

## Source and design

The local branch is `codex/e-core-observer-isolation`, based on `af4e2cd45b53cf1a76253dc174c508e5459b3cf7`. Its final tested head is `117dc92a64`. Three local commits implement the profile and repair the four defects found during saved review. Nothing was pushed or submitted.

The new explicit `--observer-isolation` option selects `e-core-workers-observer-v2`. Compute workers retain the background clamp and must report zero P-core user time. The controller runs ordinarily and reports its own P/E time and QoS counters. Its charged CPU includes initial and final observations, queue bookkeeping, stats, and receipt validation. Final serialization, disk writes, process startup, and full-output checks are outside that charge.

The profile records absolute scan boundaries and process start identities. Coverage requires at most 50 ms between effective observations and at most 50 ms per scan. The requested period remains 10 ms. Missing boundaries or inconsistent raw data fail audit. Valid but inadequate coverage is retained as a qualification failure. RSS keeps its original definition and twin gate. Physical footprint is additional evidence.

See [design synthesis](synthesis.md), [saved design judgment](design-judgment.md), [implementation review](implementation-review.md), [local commits](source-commits.txt), and [patch](implementation.patch).

## Validation

The all-enabled controller suite passed 269 tests with no failures or skips. `controller-test-provenance.json` binds its repeated run to the command, clean source revision, file hashes, interpreter, timestamps, and log hash. A separate live native queue also passed the default v1 whole-tree clamp with zero application P-core user time and no v2 observation receipt, as recorded in `legacy-verification.json`. The tests reproduced the missing profile boundary, incomplete CPU charging, lost rejected receipts, standalone import failure, and missing fixed-phase deadline behavior before their respective repairs. The deterministic coverage checks also cover missing brackets, slow scans, long holes, identity changes, and changed policies.

The final six-condition smoke retained SwiftSci optional and compact storage, pandas C reader, Polars, DuckDB, and the explicit-schema Arrow-to-pandas reader, each with an identical-condition twin. It used the original air-quality and household-energy contracts, native library pools, four callers, eight jobs per queue, and unchanged twin limits.

| Check | Result |
| --- | --- |
| Completed queues and jobs | 24 queues, 192 jobs |
| Full native-bit output checks | 48 passed before and after timing |
| Worker placement | 96 intervals, zero P-core user time |
| Controller accounting | 24 intervals, role and QoS evidence retained |
| Sampling coverage | All queues passed |
| Largest effective observation gap | 19.998125 ms |
| Longest memory scan | 8.766833 ms |
| RSS twin controls | All six conditions passed |
| CPU and elapsed-time twin controls | Eight failures retained |
| Performance qualification | False, both because this is a smoke and because controls failed |
| Owned-process cleanup | 119 recorded worker/probe PIDs checked, none remaining, including the later legacy check |

The independent comparison audit passed structural and accounting validation while retaining all eight control failures. Final replay under the recorded Python 3.14.6 passed 317 assertions, including an explicit interpreter-version check. Read [verification](portable-verification.json), [comparison report](comparison-report.md), and [unadjusted audit](comparison-audit.json) together. Two earlier attempts were interrupted after review found defects; they remain invalid and are preserved under `smoke` and `smoke-reviewed`.

## Remaining CPU-rate variation

The twins' median retired instruction counts differed by no more than about 0.7%, while some CPU and elapsed-time controls failed. The counted cycles per CPU nanosecond also changed. [Counter-rate analysis](counter-rates.json) reports these raw quantities without normalizing or qualifying a result.

The existing native fixed-register probe reproduced the variation independently of Python, CSV parsing, dataframe allocation, and model execution. Across 240 samples in alternating one-worker and four-worker phases, every checksum matched and all P-core user time was zero. CPU time ranged from 238.275 to 564.901 ms. SDK CPU and getrusage agree within 0.016%. All three readings, including the process CPU clock, agree within 0.025%. The separate `rate-probe-clock-audit.json` corrects the original summary, which compared only two interfaces. Effective counted cycles per CPU nanosecond ranged from 1.085 to 2.574. Instruction and cycle totals vary slightly because the process counters also include boundary and kernel work.

This isolates a change in effective execution rate and additional wall waiting. It does not independently identify physical frequency, thermal throttling, forced-idle policy, or the exact macOS mechanism. The new observer profile fixes the sampling failure in this smoke; it does not explain away the CPU or wall failures. It also does not retroactively qualify the older full study or prove that its RSS failures are fixed.

Apple's read-only `powermetrics` can capture CPU frequency, QoS, forced-idle and thermal evidence. This session's noninteractive attempt failed because administrator authentication is required. No automatic approval review rejected the operation. The [capture script](capture-frequency.sh) has passed shell syntax checks and its Python helper passes syntax compilation, but the privileged capture has not been run.

Run the capture as your ordinary user. Only the profiler receives administrator access. It requests two minutes of sampling, settings remain unchanged, and the compute probe runs unprivileged. The script writes to a new `frequency-capture.*` folder and preserves clock anchors for correlation. It cannot be fully verified until an authenticated capture completes. The profiler relies on its built-in sample count and has no separately verified hard timeout; interrupt handling of the privileged process remains untested. A syntactically valid capture still needs hardware-field and time-correlation review.

## Evidence replay

The archive contains exact controller sources, raw receipts, local patch and commits, failing and passing test logs, design reviews, native probe evidence, and the decision trail. Reference CSV files and the production worker build remain external. Replay requires the recorded Python 3.14.6. The system Python 3.9 does not reproduce the exact floating-point counter totals, as demonstrated in `runtime-rounding-witness.json`. The version requirement preserves exact checks rather than relaxing tolerances. The replay verifies saved evidence; it neither reruns those production operations nor collects live counters.

```sh
/path/to/python3.14.6 verify-smoke.py /absolute/path/to/extracted-evidence
```

The full comparison audit can also be rerun against the unchanged source checkout using `run-smoke-final.sh` as the recorded launch recipe and `compare.py --audit` for the completed panel. Raw timing conclusions belong on `codex/engineering-notes`, outside source PRs.
