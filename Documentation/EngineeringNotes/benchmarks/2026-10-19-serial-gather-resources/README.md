# Serial gather specialization resource qualification

October 19, 2026. This study measures the existing local specialization under the library's resource-efficiency objective. It does not change production code or promote the parallel radix experiment.

## Current result and local change

The narrower String/Bool candidate meets the measured resource objective for these cases. It keeps the large mixed-column CPU savings and removes the consistent Date regression. The local follow-up is `546510bb7d` on `codex/dataframe-scalar-resource-qualification`, based on the preserved original candidate. It deletes only the explicit three-line Date dispatch. Nothing has been pushed.

| Final narrowed candidate | Paired CPU change | Elapsed time before → after | Live heap change |
| --- | ---: | ---: | ---: |
| Million-row mixed sort, four columns | -48.0% | 118.39 → 68.71 ms | 0 bytes |
| Mixed sort, 250,003 rows and eight columns | -54.5% | 38.49 → 21.79 ms | 0 bytes |
| Million-row mixed gather, four columns | -54.4% | 99.19 → 50.96 ms | 0 bytes |
| Date sort, 250,003 rows and four columns | +0.3% | 5.68 → 5.70 ms | +80 bytes |
| Date gather, 250,003 rows and four columns | +0.5% | 2.30 → 2.31 ms | +80 bytes |

The [narrowed results](narrowed/RESULTS.md) cover fourteen cases and 224 fresh workers, with 700 timed samples and 84 separate memory samples. Every output check passed. All eight mixed-column cases consistently use less CPU across the five pairs. Their paired medians save 48.0–66.6%. The numeric controls and all four Date cases have CPU ranges crossing parity. Date medians lie between -0.4% and +0.5%. This removes the original repeatable 24–49% Date penalty; it does not establish a Date speedup.

The four Date cases retain 80 additional live malloc bytes after the call. The increment does not grow with the tested row or column counts; its cause was not isolated. Other cases have identical held-heap medians. Peak process RSS differs by at most 48 KiB. Do not interpret these small process-level differences as a storage-layout change or leak.

The existing three scalar-gather regression tests also pass against the same Release production object used by the narrowed benchmarks. They cover duplicate selections, fractional Date values, missing values, empty results, unchanged sources and a user-defined supported type. See [the test log](narrowed/regression-tests.log) and its [build receipt](narrowed/regression-receipt.json). This is focused validation, not a new full-suite or hosted-CI run.

This favors retaining the narrower candidate for the next production review. No additional worker, output format or caller policy is needed. The separate parallel radix trial remains parked. The next investigation is quoted CSV's spare capacity; resource qualification of concurrent preparation and prediction-cache churn remains open. The present results do not establish whole-application throughput, accelerator cost or energy savings.

## Decision from the original candidate

The combined String/Bool/Date specialization does not qualify unchanged. Across the final 192 workers, all output checks pass, but the two Date-heavy cases use consistently more CPU. Date sorting costs 23.8% more paired CPU time and Date gathering costs 48.7% more. Both paired ranges stay above parity, and neither case reduces held output storage.

Large mixed String/Bool sorts save 48.8–56.3% paired CPU time. Mixed gathers save 52.4–68.6%. Numeric controls have paired ranges crossing parity. Held output heap medians match in ten cases; the two Date cases add 80 bytes each. Peak RSS differs by at most 48 KiB. These results support the String/Bool direction but require a narrower implementation before promotion.

A follow-up removes the explicit Date dispatch and repeats all cases, adding two new Date shapes. Its [plan](narrowed/PLAN.md) and results live in `narrowed/`. No change to production defaults is justified by the original candidate alone.

## Compared implementation

Baseline `d23bf7cac92fe9f9c10bd98046ca8ade354b5a3c` and candidate `2196173097b55cb6b15a8d619e6d8032d0e95106` differ by explicit String, Bool and Date dispatch to a specialized copy loop. The candidate preserves the scalar algorithm, output representation and existing dataframe concurrency. "Serial specialization" describes the per-column loop, not a promise that the complete dataframe operation uses one CPU thread.

The previous [latency study](../2026-10-18-dataframe-evaluation/README.md) remains historical evidence. This follow-up measures total process CPU and separates live output storage from process high-water memory. It includes output release, so its latency values have a different boundary from call-only historical timings.

## Method and evidence

The [frozen plan](PLAN.md) defines twelve cases, five alternating timing pairs per case and three separate memory pairs. Each timing worker performs two warmups and five measured operations. Each memory worker performs one operation without warmup. Native CPU parallelism remains enabled. Both versions use identical dependencies and compiler options, Release optimization, arm64 and a macOS 14 deployment target. Neither binary contains coverage or sanitizer instrumentation.

Fixtures cover numeric controls, mixed String/Bool payloads and Date payloads. An independent stable comparison sort determines the expected permutation. Every output value, missing-value count, type and column order must match. Double comparisons preserve bit patterns; other supported payloads use typed equality.

CPU measurements include user plus system time across process threads. Both CPU and elapsed clocks cover the public API call and result release. Input construction, reference sorting and validation are outside those clocks. Separate memory workers measure live malloc bytes before the call, with the output held and after release. Peak RSS is captured before validation but includes process startup, input construction and reference sorting. It can therefore hide a smaller operation-specific peak. These are neither allocation-traffic measurements nor energy measurements.

The checker initially converted nonnumeric columns into strings. We stopped that run because Date formatting performed unnecessary work. We preserved its 145 completed workers and switched to exact typed comparisons. The final study repeats every case on both builds. Preliminary and final samples are never pooled. The changed checker also changes cache history, so comparisons with the preliminary run are not new optimization claims.

The complete [results](RESULTS.md), [summary](summary.json), [build and run plan](plan.json), [toolchain record](toolchain.json), and [audit](audit.json) accompany this report. [Archived evidence](evidence.tar.gz) contains raw final worker records, preliminary records, and both build receipts. [Checksums](evidence-sha256.json) cover each archive member. A matching dependency object hash proves the same dependency bytes were used within the pair; it does not recreate an old release's dependency resolver state.

## Reproduction

The scripts use the local Git object store and the existing dependency build cache identified in `prepare.py` and `build.py`. `run.py` imports the project's existing environment and instrumentation checks from the checkout named in that file; `toolchain.json` records their hashes. No new benchmark framework or runtime dependency was added.

Copy these tools into a new scratch directory. Run `prepare.py`, `build.py baseline candidate`, `run.py`, `summarize.py`, and `audit.py` with Python 3. Use AC power. Source export is idempotent, and the runner refuses to overwrite existing worker records. The build requires the recorded cached Arrow and Atomics objects. Building those dependencies on another toolchain creates a new comparison, not a replay of the exact binary evidence.

`package.py` captures the original local study into the engineering-notes branch. It is an archival helper, not a requirement for rerunning the measurements. Production changes remain on their existing branch; this report belongs only to `codex/engineering-notes`.
