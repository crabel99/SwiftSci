# CSV String optional-return experiment

Keep `codex/csv-local-batch-builder` at `c906c3fbbb0baf1357438a7079921a6448e0c9e5` unchanged. Neither optional-return trial provides a consistent resource improvement. No source branch, production commit, push, or PR was created for this experiment.

This follows the [worker-local builder experiment](../2026-10-22-csv-local-batch-builder/README.md). Its initial small-file default-token flag remains part of that record. This follow-up does not remove or waive it.

## Hypotheses

1. If classified-result conversion costs CPU on the String path, an explicit optional-return decoder reduces that cost.
2. If the optimizer already removes the conversion, the direct return provides no useful instruction change.
3. If setup dominates short reads, small timing differences do not persist across matched repetitions.

## Reproduction

The initial repeat uses frozen Array baseline `680ac74b96ab6c6968d83a9511ebdce69d30093b` and current builder head `c906c3fbbb0baf1357438a7079921a6448e0c9e5`. Five cases run under both column policies, with 16 observations per implementation and policy. All 320 workers validate complete native output. There are no CPU or memory review flags. The previously reported large parallel default-token penalty is not reproduced.

| Input | Policy | Baseline CPU ms | Current CPU ms | CPU change |
|---|---|---:|---:|---:|
| all-string-default-nulls-0 | parallel | 4.067 | 4.232 | +4.1% |
| all-string-default-nulls-0 | serial | 4.202 | 3.940 | -6.2% |
| all-string-default-nulls-50 | parallel | 3.998 | 3.955 | -1.1% |
| all-string-default-nulls-50 | serial | 3.862 | 3.817 | -1.2% |
| all-string-default-nulls-90 | parallel | 3.331 | 3.306 | -0.8% |
| all-string-default-nulls-90 | serial | 3.260 | 3.250 | -0.3% |
| default-nulls-0 | parallel | 2.954 | 2.978 | +0.8% |
| default-nulls-0 | serial | 3.059 | 2.814 | -8.0% |
| Aotizhongxin-default | parallel | 12.097 | 12.077 | -0.2% |
| Aotizhongxin-default | serial | 9.812 | 9.782 | -0.3% |

## Trials and methods

The screening matrix compares four executables. `production` is the frozen binary from the preceding builder study. `control` rebuilds exactly the same sources in a new snapshot. `hashed-optional` gives only `CSVStringDecoder` an explicit `decodeValue` method. `both-optional` also changes `CSVSmallStringDecoder`. Each classified `decode` method wraps that optional result, so each field is still parsed once.

All variants retain the same null tokens, native String equality, parser, capacity, workers, and public API. No raw-byte null classifier or new lookup threshold is added. The proposed simplification removes a source-level result conversion rather than adding another parsing layer.

Thirteen input/scope combinations run with explicit parallel and serial conversion. Each implementation receives eight observations in rotated and reversed order. All 832 workers validate full native values, types, null positions, and row and column order. Streaming uses a separate complete untimed read for validation. Inputs include default, one-token, two-token, 17-token and 2,048-token sets, long keys, mixed columns, all-String columns, air quality, and household data.

Every implementation receives the same `argv[0]` within its scope. Input bytes are warmed, power is AC, and the existing production worker environment preserves native scheduling and hash randomization. All build and link processes finish before screening starts. Assembly inspection starts only after screening completes. No build, test, or profiler overlaps accepted timing. Host activity outside this task remains uncontrolled.

CPU means process user-plus-system time during the complete read. Peak RSS includes the entire worker and is not an allocation count. Elapsed time is recorded separately. These measurements do not establish energy, FLOPs, cache behavior, or hardware contention.

## Generated code

The unchanged-source control and hashed-only trial have identical bytes in every Mach-O `__TEXT` section, including instructions and constants. Their instruction section is 1,011,924 bytes with SHA-256 `4093ef42f2c7aea8bf95ad3b0abd69d03301285736d2e929b65b67cf41c871c0`. The explicit hashed optional method therefore does not remove emitted instructions on this compiler. Hypothesis 1 is rejected for that trial.

The two-decoder trial changes code placement and emits a separate compact-record small-String append function. Its instruction section is 1,012,012 bytes. Static size and instruction-entry counts do not measure executed work. No repeatable performance benefit follows from that layout change in this screen.

## Results and decision

The household reference results are below. See [all 104 implementation/policy medians](screening-results.md) for complete CPU, elapsed, and peak-RSS measurements.

| Scope | Policy | Production CPU ms | Unchanged rebuild CPU ms | Hashed optional CPU ms | Both optional CPU ms |
|---|---|---:|---:|---:|---:|
| eager | parallel | 269.692 | 271.306 | 271.702 | 279.226 |
| eager | serial | 253.440 | 251.269 | 253.168 | 255.158 |
| stream | parallel | 253.327 | 250.150 | 253.454 | 253.295 |
| stream | serial | 231.775 | 231.328 | 231.817 | 235.986 |

Small-case differences reverse across cases and policies. Two CPU review flags remain in the screen: serial 17-token all-String input is 11.7% higher for the unchanged rebuild and 21.8% higher for hashed-only, each against the frozen production binary. The unchanged rebuild and hashed-only trial have identical instruction and constant sections. These flags do not establish that optional return caused the cost. They show why timing alone cannot justify this change.

Neither trial has a consistent CPU benefit or a demonstrated memory benefit. The largest median peak-RSS increase against production is below 0.73 MiB. That is not proof of identical allocation behavior. Keep all flags and measurements, reject both optional-return trials, and retain the existing builder head.

No new production tests, sanitizer run, grammar qualification, or standardized benchmark run is claimed. They would qualify a selected implementation, and this screen selects none. The prior builder test results remain attached to their original head and report.

## Next investigation

Investigate the cost of hashed membership and String construction separately on actual reference inputs before proposing another representation. Preserve native String equality, Unicode normalization behavior, invalid-UTF-8 repair, and escaped-field semantics. The evidence here rules out source-level result conversion as a useful hashed-path optimization. It does not prove a physical cache or scheduling mechanism.

## Evidence

- [Source state and hashes](source-state.json)
- [Reproduction plan](reproduction/plan.json), [medians](reproduction/summary.json), and [flags](reproduction/review-flags.json)
- [Screening plan](screening/plan.json), [medians](screening/summary.json), and [flags](screening/review-flags.json)
- [Complete resource table](screening-results.md)
- [Assembly hashes and counts](assembly/summary.json)
- [Preserved source variants, patches, and input contracts](experiments.tar.gz)
- [Artifact hashes](artifact-sha256.json)

`build.py`, `link-variants.py`, `screen.py`, `reproduce.py`, and `inspect-code.py` retain executable procedures. `experiments.tar.gz` preserves all three module snapshots and both trial patches. Reference CSV bytes remain with their existing dataset owner; contracts retain their byte hashes and full expected native output. Generated text inputs are included. Recreate the recorded paths or adapt paths while preserving hashes, schemas, policies, and validation.
