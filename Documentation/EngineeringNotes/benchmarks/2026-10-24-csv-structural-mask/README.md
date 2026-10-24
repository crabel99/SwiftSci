# CSV structural scanning uses less CPU in matched mixed workloads

Retain the scanner change locally as `2a8f1230667eaa86cd72a67b5e78b2b3830f2c23` on `codex/csv-structural-mask-trial`, based on `5b9c90297723cf53dcba17299c57778688e282e2`. Two completed matched panels measure 3.0–3.6% less charged CPU per job and 4.9–5.8% more completed work per minute. Sampled peak memory is essentially unchanged. The change adds nine source lines and removes ten in one private scanner. Nothing was pushed and no PR was opened.

The [earlier digit-pair trials](../2026-10-24-csv-digit-parser-trials/README.md) remain separate and unpromoted. The [compact validity-word improvement](../2026-10-24-compact-csv-construction/README.md) remains in this branch's parent. Engineering reports and raw evidence stay on `codex/engineering-notes`.

## A register representation removes two reductions

The scanner compares 16 input bytes with delimiters, line feeds, and quotes. Its previous packing method uses weighted masks and two horizontal sums to produce a 16-bit match word. The new method explicitly creates byte flags of zero or 255, treats each adjacent byte pair as a 16-bit word, then shifts and narrows those words into bytes. On the tested little-endian Apple target, each original flag occupies one nibble. Masking with `0x1111111111111111` leaves one bit per original byte.

The match state is a UInt64 instead of a UInt16. Both fit a CPU register. This temporary representation adds no heap buffer and changes no dataframe values or field-coordinate arrays. A trailing-zero count divided by four recovers the original byte position. This trades unnecessary bit compression for an operation that maps directly to the hardware.

The integrated assembly for the two inspected `scanRecords` specializations changes from four horizontal reductions in total to zero, with two `SHRN` instructions in total. Each specialization has one narrowing operation per SIMD block. The compiler folds position recovery into `ADDS ... LSR #2`; it emits no standalone divide for that operation. These are compiled-instruction observations, not measured retired-instruction counts, cache utilization, or energy.

The existing 16-byte load, quote state machine, cancellation windows, offset limits, and borrowed-buffer lifetime remain unchanged. The implementation converts explicit numeric flag values, so it does not reinterpret the opaque storage of `SIMDMask`. Numeric conversion, schema selection, missing-value policy, storage defaults, and package minima remain unchanged.

## Correctness and run controls

The isolated packing probe passes all 65,536 mask patterns. The public-parser checker matches the parent byte-for-byte across 75,583 framing cases. A subset of 65,536 also checks coordinates against an independent delimiter-boundary oracle. Other cases vary input alignment, delimiter and quote bytes, malformed framing, escaped quotes, scalar tails, 65,536-byte search boundaries, and large quoted and unquoted inputs. Both produce the same 28,785,191-byte coordinate stream with SHA256 `9ef88e34ce971b6dd5855327cd32a387dcbc8828aa080585ded2b5278c3ea504`.

All 437 dataframe tests pass in Debug and all 437 pass in Release, with no failures or skips. Existing tests already exhaust every delimiter mask and exercise framing, boundaries, row limits, counting, inference, and conversion. No test file or test expression grows in this patch. No full MLX-dependent suite result is claimed.

Eight full reference-output preflight checks pass for the candidate. The two completed full panels add 64 preflight and postflight checks across both binaries, both storage modes, and complete read/sort/matrix outputs. Independent expected fingerprints include native numeric bits and missing values. Hashing is outside timed work.

A fresh identical-binary control passes before implementation. Its nominal trial/parent compact CPU ratio is 1.000795. The probe compilation starts after that control finishes. Performance panels run sequentially after native builds and tests, with no competing experiment build or profile. Linked dependency hashes match and only `SystemsCSVParser.swift` differs between measured library sources.

## Complete workload result

Each panel completes 64 queues and 8,192 jobs. Four concurrent callers process fixed queues of 128 jobs, including 32 copies of each dataset/workflow combination. The datasets are the 35,064-row Aotizhongxin observations and the 2,075,259-row household power data. Workflows read a full frame or read, stably sort, and construct its numeric matrix.

Eight rotated rounds include an identical-binary twin for each build and storage condition. A second panel reverses the ordering. Both pass the recorded 10% twin CPU/wall controls and the 5% plus 8 MiB-per-caller RSS controls. All conservative sums of kernel-reported worker peaks remain below 4 GiB.

| Panel | Storage | Parent → candidate CPU ms/job | CPU change | Throughput change | Parent → candidate peak RSS MiB |
| --- | --- | ---: | ---: | ---: | ---: |
| Rotated | optional | 201.91 → 194.62 | -3.61% | +4.94% | 3503.9 → 3505.6 |
| Rotated | compact | 199.78 → 192.88 | -3.46% | +5.56% | 2513.1 → 2514.1 |
| Reversed | optional | 195.56 → 189.64 | -3.03% | +5.80% | 3502.5 → 3499.5 |
| Reversed | compact | 193.13 → 186.71 | -3.33% | +5.04% | 2510.2 → 2510.4 |

The candidate uses less charged CPU in every paired round for both storage modes in both panels, 32 of 32 comparisons. These repeated runs are finite observations, not independent statistical samples or confidence intervals. The throughput gain establishes more completed work for this measured workload and caller budget. It does not establish the behavior of every concurrent application mix.

The first household-only read screen measures 5.97% less CPU, with effectively unchanged RSS. Its throughput change is larger than the mixed-workload result. The complete-workflow panels provide the evidence for the decision.

## Other representations and missing-value patterns

The following screens compare candidate compact storage with parent compact storage. Each format has 250,003 rows, a declared Float64 schema, and a recognized missing value every 97 rows. Each completes 144 reads in six rotated rounds with twins. Native output hashes match an independent Python float-bit oracle before timing.

| Numeric representation | CPU change |
| --- | ---: |
| long-fallback | -0.41% |
| one-digit | -2.17% |
| quoted-padded | -13.12% |
| scientific | -2.83% |
| short-limit | -4.94% |
| six-fraction | -6.96% |

The long-number result is essentially flat. Four additional screens use 1,000,003 rows of binary-exact quarter values and recognized `?` missing tokens. Each also completes 144 reads.

| Missing pattern | CPU change |
| --- | ---: |
| alternating | -6.44% |
| missing | -2.69% |
| present | -6.34% |
| sparse | -6.64% |

Two 16-column stress cases use 100,003 rows and eight rotated rounds with twins, completing 192 reads each. Dense quoted one-digit rows use 9.84% less CPU. Empty fields with the custom null set containing only `?` use 1.53% more CPU in the original screen. That countercase remains in the record and prevents a universal improvement claim.

## Null semantics expose a separate conversion cost

The empty-field stress contract inherits a custom null set containing only `?`. It does not recognize empty fields as missing. Under the explicit schema, the numeric decoder rejects the byte parse, fails the null match, then creates a String and calls the standard numeric conversion. Invalid values eventually become nil. This follows the existing API contract.

A separate control uses the same CSV bytes and the actual default null-token set from `CSVReadOptions.swift`, including the empty string. It retains the full explicit numeric schema, so it is not an inference benchmark. Both builds receive the same null policy within each comparison, and all public output checks pass.

| Null policy for the same empty file | Parent CPU ms/read | Candidate CPU ms/read | Candidate change |
| --- | ---: | ---: | ---: |
| Custom `?`, empty fields become invalid numeric values | 9183.66 | 9323.85 | +1.53% |
| Default null tokens, empty fields are recognized missing values | 19.98 | 18.58 | -6.99% |

These rows are separate configurations. The hundreds-fold difference between their absolute costs is not the scanner improvement. The matched default-null comparison measures about 7% less CPU. Its source-derived policy and exact options are recorded separately.

The longer custom-null diagnostic stopped after 587.2 seconds with 25 of 48 planned queues complete. All partial records remain archived. It has no final qualification and is excluded from completed-screen summaries. Its proposed scale would perform more than two billion field conversions. A new `diagnostic-budget.py` forecasts the cost from an existing screen before another long diagnostic is scheduled. Its checks reject this expensive extension and accept a short numeric screen. The forecast is conservative scaling, not a guaranteed runtime bound.

A bounded four-second native sample of the unchanged parent shows retain/release activity and string trimming prominent in this fallback. Five requests complete and the worker closes. The sampled timings are excluded from performance evidence. The sample does not identify the retained object, prove cache-line contention, or explain the scanner's 1.53% countercase.

The next separate optimization should investigate skipping known-empty numeric fallback while preserving the API distinction between missing and invalid values. Explicit numeric schemas coerce both to nil; inference must retain rejection and fallback-to-string behavior when empty is not a declared null. No conversion-path repair is included here.

## Scope and reproducibility

Every throughput worker supplies a complete explicit schema. `schema_contract.py` records effective options for the reviewed worker fingerprint and rejects an unknown worker implementation. This is source/receipt proof, not runtime option introspection. No inference-performance claim follows from these timings.

The host is an Apple M4 Max with 128 GiB, on AC with unchanged recorded power settings. Full panels check AC before every queue. CPU parallelism remains native. Builds use Swift 6.4 in Swift 6 language mode and target arm64 macOS 14. Execution occurs on macOS 27.0.1. No Swift 6.0 compiler or macOS 14 runtime result is claimed.

Charged CPU is worker user/system time plus measured controller CPU, including cleanup. It is not FLOPs, normalized P/E-core work, or measured energy. Sampled peak RSS can miss short peaks and count shared pages repeatedly. No GPU, Neural Engine, cold-disk, or system-cache improvement is claimed.

[Summary](summary.json), [artifact hashes](artifact-sha256.json), and the [experiment archive](experiment.tar.gz) preserve exact source snapshots, the parent file, compiler receipts, generated-code inspection, tests, golden coordinates, fixtures and generators, raw resource records, the interrupted diagnostic, and the native profile. Executables, objects, module caches, raw CSVs, and xcresult bundles are excluded. The golden binary is result data, not an executable.

Both full-panel audits recompute 128 completed queues and 16,384 jobs, including CPU accounting and 64 full-output checks. The screen audit recomputes 588 completed queues and 2,352 reads. The interrupted long diagnostic is excluded. The archived inventory verifies every preserved file.

Build receipts retain their original parent head and dirty-source hashes. The later local commit maps to those exact measured source bytes; historical fingerprints have not been rewritten. To reproduce, restore the recorded source, matching dependencies, reference-file hashes, and worker options. Remap archived absolute paths and generate synthetic files from the preserved generators. Rebuild using `Benchmarks/CPUThroughput/build.py`, use a fresh directory per run, and run `audit-workflows.py` and `audit-screens.py`. Check projected diagnostic cost before increasing repetitions. Broader library comparisons and other machines require fresh matched runs.
