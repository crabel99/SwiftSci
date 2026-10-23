# Stable permutations for monotonic Double columns

The previous allocation trial avoided a full row/value cache on the radix path, but its separate detection pass increased CPU work on already ordered inputs. This candidate uses the detector's proof of monotonic order to build stable indices directly. It retains the allocation trial's disordered path.

The source checkpoint is `e1f5f8c30500e1511b0700bcffe10efb7ac8e88b` on `codex/csv-monotonic-permutations`, based on `42f0633fd52e8e6ece961465880050ebc16db60e`. The earlier qualified checkpoint `91c0ff09b7810b57cabdd953f8bc67791b1008f5` is measured again in the same panel. This is local experimental work. The full allocation strategy remains unpromoted because nearly ordered inputs still cost more CPU than that earlier checkpoint.

## Ordered inputs avoid comparison caches

The existing detector counts direction changes between present values. A complete scan with no direction change proves monotonic order, including equal values. The candidate then allocates only the result indices. Null indices remain last in original row order.

If present values already match the requested direction, their indices keep their original order. Otherwise, the candidate reverses their indices and reverses each equal-value group to restore stable ties. Signed zeros compare equal and retain their original bit patterns. Infinities follow the requested direction. Valid NaNs retain the existing comparison fallback, including NaNs discovered after radix dispatch.

No public API, worker policy, precision rule, CSV contract, or sort threshold changes. Both optional and compact storage use the same private algorithm. The new test type is 53 lines and contains two test functions.

## Matched shape controls

Eight generated fixtures cover ascending, descending, nearby-swap, and pseudorandom arrangements at 32,768 and 1,000,000 rows. All layouts include repeated ties and exact binary-fraction values. An independent generator supplies complete stable-permutation and value hashes. Both storage choices run through the public sorting method.

All 512 measured processes match expected output and pass the unchanged identical-binary quality policy. Each case has eight fresh processes per label. The labels are the earlier qualified checkpoint, the allocation trial, the candidate, and a duplicate of the candidate executable.

CPU covers sorting and index release. Input construction and full output validation are excluded. The caller retains the input through the final CPU timestamp. Process peak RSS can include the earlier CSV construction peak. Held heap and peak RSS describe different costs.

| Million-row storage and layout | CPU earlier / allocation / candidate, ms | Peak RSS earlier / allocation / candidate, MiB |
|---|---:|---:|
| optional / ascending | 4.441 / 5.087 / 1.459 | 45.797 / 45.797 / 32.859 |
| compact / ascending | 4.011 / 4.863 / 1.681 | 38.172 / 38.156 / 25.234 |
| optional / descending | 75.189 / 75.898 / 2.281 | 45.781 / 45.781 / 32.844 |
| compact / descending | 65.951 / 66.855 / 2.729 | 38.156 / 38.156 / 25.219 |

For the million-row compact column, ascending CPU falls from 4.863 to 1.681 ms against the allocation trial. Descending CPU falls from 66.855 to 2.729 ms. Against the earlier qualified checkpoint, those comparisons are 4.011 to 1.681 ms and 65.952 to 2.729 ms. The descending fixture contains repeated ties, so this result must not be generalized to every reverse-ordered workload.

Peak process memory falls from about 38.16 to 25.22 MiB in the compact million-row monotonic cases. Held input and result allocations remain about 15.39 MiB. The observed benefit is lower temporary sorting memory, not a smaller retained result.

The remaining cost is nearly ordered comparison sorting. The compact million-row nearby-swap control uses 9.278 ms at the earlier qualified checkpoint, 10.131 ms at the allocation trial, and 10.214 ms at the candidate. At 32,768 rows, the corresponding numbers are 0.182, 0.212, and 0.214 ms. The new monotonic path does not remove this inherited scan cost. Large pseudorandom cases remain close to the allocation trial. Small differences do not establish a universal improvement.

[All 16 shape controls](shape-results.md) retain both storage choices, both sizes, CPU, held heap, and peak RSS.

## Real observation workflows

The real-data panel uses 2,075,259 household electricity observations and 35,064 Aotizhongxin air-quality observations. All labels honor the same explicit schema, null tokens, storage choice, input bytes, and row order. Serial and native parallel CSV conversion each run sorting indices, sorting followed by matrix preparation, and sorting followed by retained optional exports.

Total CPU includes CSV construction, the operation, consumer preparation, and release. Operation CPU excludes construction and release. Complete numerical and row-order hashes run outside timing. The table shows household data with serial conversion. Each cell gives allocation-trial and candidate medians.

| Storage and workflow | Total CPU prior / current, ms | Operation CPU prior / current, ms | Held heap prior / current, MiB | Peak RSS prior / current, MiB |
|---|---:|---:|---:|---:|
| optional / sort-indices | 281.38 / 277.36 | 46.47 / 46.89 | 301.00 / 301.00 | 420.70 / 420.61 |
| optional / sort-matrix | 429.72 / 427.17 | 194.21 / 195.94 | 396.00 / 396.00 | 737.59 / 737.49 |
| optional / sort-materialize | 414.17 / 411.43 | 179.33 / 180.30 | 285.16 / 285.16 | 626.73 / 626.63 |
| compact / sort-indices | 292.84 / 290.41 | 47.02 / 47.46 | 191.95 / 191.95 | 312.48 / 312.42 |
| compact / sort-matrix | 412.56 / 406.92 | 166.74 / 166.97 | 286.95 / 286.95 | 503.34 / 503.16 |
| compact / sort-materialize | 423.72 / 420.40 | 177.35 / 178.72 | 397.81 / 397.81 | 550.91 / 550.97 |

For serial compact household data, total CSV-and-index-sort CPU is 292.842 ms at the allocation trial and 290.406 ms at the candidate. Sort-operation CPU is 47.018 and 47.459 ms. These small differences do not establish an improvement from the new monotonic path on disordered observations.

Matrix and optional-export workflows retain the allocation trial's held-heap sizes. Both still retain 15.4375 MiB less malloc capacity than the earlier qualified checkpoint. Peak RSS remains nearly unchanged for these real-data workflows, so that capacity reduction is not equal physical-RAM relief.

[All 24 real-data cases](results.md) also show the earlier qualified checkpoint. Real-data quality records `quality_passed=true` with flags `[]`. Flagged comparisons remain unqualified. The candidate changes the fully monotonic path; differences on disordered real observations must not all be assigned to that path.

## Validation and limits

Release, Debug, and Address Sanitizer each pass 424 dataframe test functions without failures or skips. The two added test functions pass before and after the change. Tests cover both requested directions, both storage choices, stable ties, missing values, signed zeros, infinities, and existing NaN fallback behavior.

Twenty-eight eager and twenty-eight streamed reference reads pass exact type, value, null, and order checks. The real panel has 96 preflights and 768 measured processes. The shape panel has 64 preflights and 512 measured processes. Every measured result matches its full expected fingerprints.

Both panels use eight balanced orders. Each label appears in each position twice, and each ordered adjacent pair appears twice. The frozen policy flags candidate/twin median CPU differences above 10%, or peak RSS differences above 5% plus 8 MiB. No flags are waived.

Builds, tests, and fixture preparation finish before accepted timings. AC power is checked at both ends. The independent audits verify source, executable, interface, and input hashes; recompute medians; and check ordering and output equality. The machine is an Apple M4 Max with 128 GiB of unified memory. Clients use Swift 6.4 and an arm64 macOS 14 deployment target.

CPU is process user plus system time. These results do not measure energy, FLOPs, memory traffic, cache misses, or SRAM activity. Address Sanitizer does not prove universal leak freedom. This study validates the dataframe module, not the complete MLX-dependent package.

## Evidence and reproduction

- [Real-data results](results.md) and [shape controls](shape-results.md).
- [Main audit](audit.json) and [shape audit](shape-audit.json).
- [Comparator provenance](comparator-provenance.json) and [frozen study definition](study.json).
- [Source patch from the allocation trial](changes.patch.gz).
- [Scripts, source, raw records, and receipts](experiments.tar.gz).
- [Artifact hashes](artifact-sha256.json).
- [Earlier allocation investigation](../2026-10-23-csv-sort-buffer-allocation/README.md).

Restore the recorded commits and dependencies, then rebuild the baseline modules from their compiler receipts. The archive includes `compiler-command-template.json`, which supplies the `F/build.json` input used by the build scripts. Restore that file at the recorded path or update `F`. Decompress the patch and update machine-specific paths. Run `verify.py Release --label final-release`, followed by `validate.py`, `measure.py`, and `package.py`. The archive contains the shape generator and hashes instead of large CSV fixtures. It excludes executables, dependency caches, and result bundles.

Source and tests remain on the local experiment branch. This record remains only on `codex/engineering-notes`. Nothing is pushed or submitted as a PR. The next development target is the duplicate work on nearly ordered inputs, while preserving these stable monotonic permutations.
