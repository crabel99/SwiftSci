# Standardized benchmark validation

This evidence validates the first benchmark protocol on top of upstream main `fd68e6be058aa9fb10be1627a8b8841b9ee9a7e7`, which includes PR #39 and version 3.10.2. It is an infrastructure acceptance run, not a before/after optimization claim.

The standard profile passed all 84 fresh worker processes and 420 measured output validations. It covers 11 operations on the 100,000-row table plus three NIST checks, in SwiftSci and pandas/NumPy, with three processes per case and five measured samples per process. Every process also validated two warmups. The standalone certification command passed all six NIST engine/case pairs.

Both complete native test configurations passed 899 tests with no failures or skips. After the final benchmark-support visibility change, its four Release tests passed again. Fifteen Python protocol tests passed, covering fixture corruption, wrong outputs, missing responses, process crashes, timeouts, duplicate/incomplete cases, unresolved timings and incompatible comparisons. A separate CLI check confirmed that modifying a run invalidates its certificate checksum.

Measurements used an Apple M4 Max with 128 GB memory, macOS 27.0 and Xcode 27. Full versions, compiler flags, thread settings, input identities, binary hashes and raw samples are in each `run.json`. Builds and tests finished before the standard run. Normal desktop background activity was not controlled; these samples do not establish regression thresholds or statistical significance.

The benchmark sources were uncommitted when measured. Their complete file hashes are retained in the run and build records. The measured source fingerprint is:

```text
40e7b07ce9ab9027f5f0179e0c3d0e1128560064efca4792a258eee60fd9593a
```

It identifies implementation content, rather than implying that the new tooling already existed in upstream main. Documentation and this evidence are excluded from that source fingerprint.

The published bundles retain the exact run and certificate bytes, including all raw samples. Per-process logs, requests and regenerated expected-value binaries remain in the ignored local run directories. The manifest-pinned inputs and reference implementation reproduce those expected values. Absolute build paths record provenance; they are not required to audit the published bundles.

From the repository root:

```bash
python3 Benchmarks/Tools/bench.py audit Benchmarks/Results/StandardizedValidation/standard
python3 Benchmarks/Tools/bench.py audit Benchmarks/Results/StandardizedValidation/certification
python3 Benchmarks/Tools/bench.py report Benchmarks/Results/StandardizedValidation/standard
```

Follow [the benchmark instructions](../../README.md) to reproduce the run. Performance comparisons require matching experiment contracts and environments. The GitHub workflow was syntax-checked locally; it has not yet run on GitHub.
