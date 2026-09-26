# Benchmark architecture

Status: first implementation, 2026-09-26. The executable interface and supported coverage are documented in [README.md](README.md).

## Ownership

Production modules own numerical and dataframe operations. They do not depend on fixture downloads, Python, measurement code or benchmark records. `SwiftSciBenchmarkSupport` is a development target without a public library product. `SwiftSciBenchmarkWorker` calls existing public APIs, so the same workloads can measure upstream and optimized implementations.

The Python controller owns fixture preparation, process scheduling, provenance, failures and summaries. Each language worker owns native setup, timing, materialization and output validation. Keeping timers in the native workers excludes process startup and JSON transport from operation timings.

A separate worker keeps the new protocol independent of legacy runners whose fallback fixtures, name matching and memory measurements differ. The old runners remain available for broader historical coverage. Migrating their remaining workloads requires an explicit semantic and output-validation review.

## Records and evidence

Dataset manifests pin generator version, shape, provenance, license, size and SHA-256. Workload manifests pin operation, timing scope, output order and tolerance. Profiles select exact case IDs and repetition counts. JSON schemas describe these input records and worker responses; runtime validators enforce additional relationships such as expected sample counts.

The resolved run plan embeds these records and hashes the experiment contract. Source-file hashes distinguish staged or uncommitted code from the recorded Git revision. A build sidecar binds the actual worker binary to those source bytes and its build command. A run refuses a stale worker or changed build environment.

Each case and engine runs in a fresh process. Engine order alternates between process batches. Workers compare complete outputs against independently generated answers, outside timing. Exact-value workloads have zero tolerance. Numerical references use accurate summation or published NIST answers and explicit tolerances.

Failures remain failures. The controller records process errors, writes incremental evidence, and withholds usable timing summaries for incomplete cases. The final certificate binds the complete run file by checksum. It is a local conformance record, not an externally signed attestation.

One reporter computes all summaries. It keeps raw samples and process medians and refuses comparisons with incompatible contracts or environments. Process lifetime peak RSS is explicitly separate from operation allocation. Future metrics must state their units and observation scope.

## Next coverage increments

1. Add nulls, strings, high-cardinality and skewed groups, mutation ownership cases and complete read-to-numerical-consumer pipelines. Preserve row/target alignment in their references.
2. Add reusable fitted-state and GPU-resident workloads separately from first-use conversion and synchronization. Unified memory alone does not establish equivalent timing boundaries.
3. Add Kiraa and SciPy adapters only for semantically equivalent workloads. Unsupported cases must be declared, never silently substituted.
4. Add pinned public workloads such as H2O-derived grouping and additional NIST references, with licenses, checksums and expected answers.
5. Calibrate tiny operations and estimate uncertainty across independent processes before adding performance thresholds on a controlled Apple silicon runner.

This branch establishes a runnable contract for the first common workloads. It does not change the compact-storage design, raise the library's minimum Swift/macOS versions, or certify the entire library.
