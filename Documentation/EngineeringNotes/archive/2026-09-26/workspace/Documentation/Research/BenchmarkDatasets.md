# Standard datasets and validation for SwiftSci

Research date: 2026-09-26. This is a proposed benchmark corpus, not a claim that SwiftSci has run these workloads.

A reproducible benchmark needs data, an operation contract, expected results, and a measurement protocol. The same dataset can support correctness, performance and interoperability tests, but each needs its own acceptance criteria.

## Existing repository foundation

`Benchmarks/generate_fixtures.py` already generates seeded CSV and little-endian Double arrays for both Swift and Python and records SHA-256 checksums. `Benchmarks/Data/.gitignore` excludes generated data. Existing reports under `Benchmarks/Results` record code revisions, timing samples and machine details. Extend this structure with dataset manifests and independent reference answers. Do not replace the useful synthetic cases with one famous dataset.

## Established dataframe workloads

H2O/db-benchmark, now maintained in a DuckDB Labs fork, combines generated data with ten grouping queries and five joins. It varies key types, cardinality, missing entries and sortedness at published scales of 10 million, 100 million and one billion rows. Queries include single- and multi-key aggregates and joins against differently sized inputs. Use smaller explicitly labeled local scales for development. Preserve the generator revision and exact parameters. [Published benchmark](https://duckdblabs.github.io/db-benchmark/), [generator](https://raw.githubusercontent.com/duckdblabs/db-benchmark/main/_data/groupby-datagen.R), [operation explanation](https://duckdb.org/2023/04/14/h2oai).

TPC-H defines eight related tables and 22 analytical queries. DuckDB's extension provides convenient generation and expected answers at several small scale factors. Begin with Q6, filtering and arithmetic reduction, and Q1, calculated columns followed by grouping and ordering. A dataframe subset with fixed parameters is a TPC-H-derived workload, not a compliant or audited TPC-H benchmark. [Specification](https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPC-H_v3.0.1.pdf), [DuckDB extension](https://duckdb.org/docs/stable/extensions/tpch), [Q1](https://raw.githubusercontent.com/duckdb/duckdb/main/extension/tpch/dbgen/queries/q01.sql), [Q6](https://raw.githubusercontent.com/duckdb/duckdb/main/extension/tpch/dbgen/queries/q06.sql).

NYC TLC publishes monthly Parquet trip records and a zone lookup table. Pin a service and month, preserve its schema and source checksum, and explicitly define SwiftSci queries for date/fare filtering, trip-duration calculation, zone grouping and lookup joins. TLC supplies real data rather than an official benchmark query suite; reference answers and cleaning policy would be ours. If testing CSV, record the conversion process and resulting checksum separately. [TLC data and schema notes](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page).

ClickBench provides about 100 million web-analytics rows and 43 analytical queries on one flat table. It stresses scans, filtering, distinct values, grouping and ordering, but adds no join coverage. Keep it as an optional capacity run. Its current repository license is CC BY-NC-SA 4.0, so redistribution cannot be assumed to follow the ClickHouse software license. [Benchmark](https://github.com/ClickHouse/ClickBench), [queries](https://raw.githubusercontent.com/ClickHouse/ClickBench/main/clickhouse/queries.sql), [license](https://raw.githubusercontent.com/ClickHouse/ClickBench/main/LICENSE).

Pandas complements public comparison suites with its own ASV benchmarks for time and memory. Parameterized operation-level tests are still needed to isolate implementation regressions. Standard datasets supply outside comparability; targeted generated fixtures supply control over the cases an algorithm must handle. [Pandas benchmark guide](https://github.com/pandas-dev/pandas/blob/main/web/pandas/community/benchmarks.md), [grouping benchmark source](https://raw.githubusercontent.com/pandas-dev/pandas/main/asv_bench/benchmarks/groupby.py).

## Numerical correctness

NIST Statistical Reference Datasets provide certified answers for univariate statistics, ANOVA, linear regression and nonlinear regression. They include both constructed and real observations with differing difficulty. Use the matching statistical model and conventions, including sample versus population variance; compare numerical error, not speed alone. NIST describes these as best-available reference solutions, not proof that a library is correct for every input. [NIST background](https://www.nist.gov/itl/sed/statistical-reference-datasets/strd-background-information), [usage guidance](https://itl.nist.gov/div898/strd/general/howto.html).

A useful first fixture is NumAcc4, with 1,001 observations, certified mean 10,000,000.2 and standard deviation 0.1. The large offset relative to variation makes it relevant to numerical stability. Test the estimator against the certified convention before using it as a scaler reference. [NumAcc4 certified values](https://www.itl.nist.gov/div898/strd/univ/certvalues/numacc4.html).

SciPy also retains small adversarial statistical fixtures with large, tiny and closely spaced numbers. These complement real datasets because they isolate arithmetic weaknesses. [SciPy statistical tests](https://github.com/scipy/scipy/blob/main/scipy/stats/tests/test_stats.py).

## Matrix algorithms

Matrix Market supplies matrices and generators for linear systems, least squares and eigenvalue studies. SuiteSparse supplies curated sparse matrices from engineering and other applications. Neither collection is a single universal pass/fail test. Choose matrices by shape, symmetry, conditioning, sparsity and application. Sparse fixtures belong in sparse algorithm coverage; silently densifying them would measure a different workload. [Matrix Market](https://math.nist.gov/MatrixMarket/info.html), [SuiteSparse collection](https://sparse.tamu.edu/about).

LAPACK provides a better model for validation than demanding identical eigenvectors or singular vectors. Its tests use scaled residuals and orthogonality checks. For SwiftSci, check reconstruction, solve residuals and appropriate orthogonality errors, accounting for precision and dimensions. Vectors may differ in sign or basis within repeated eigenspaces while representing the same answer. Dense generated matrices with controlled rank and conditioning should accompany application matrices. [LAPACK orthogonality test](https://www.netlib.org/lapack/explore-html/d9/df0/dort01_8f_source.html), [ScaLAPACK test procedures](https://netlib.org/scalapack/scalapack_install.pdf).

## Real machine-learning workflows

Scikit-learn provides California Housing with 20,640 rows and eight input features, and Covertype with 581,012 rows and 54 features. Housing is a manageable regression input; Covertype provides a larger classification input with numeric and indicator features. [California Housing](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_california_housing.html), [Covertype](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_covtype.html).

Proposed SwiftSci tests would select rows and columns, preserve target alignment, fit a scaler on a fixed training partition, transform held-out rows, export the requested matrix layout and run a supported estimator. Record prediction error or classification metrics separately from conversion and runtime metrics. Fix partitions and seeds, and do not fit preprocessing on held-out data. These are proposed workflow tests, not a fixed benchmark specification bundled with the datasets.

## Interoperability

Apache Arrow generates small fixtures by type and feature and tests producer/consumer pairs across implementations. It exercises IPC, Flight and the C Data Interface, compares reconstructed arrays to reference data, and can check release behavior for exported buffers. This is directly relevant to future compact-column adapters. Begin with supported numeric types, missing entries, slices and empty batches; declare unsupported types explicitly. Do not claim compact Swift buffers are already Arrow-compatible. [Arrow integration testing](https://arrow.apache.org/docs/format/Integration.html).

## Measurement contract for Apple silicon

These are recommendations for SwiftSci:

- Keep exact comparisons for row identities, schema, strings, integer results and operations whose bitwise semantics are explicitly promised. Use justified numerical tolerances and residuals when algorithms legitimately change floating-point reduction order.
- Canonicalize unordered group output before comparison. Specify null/NaN handling, sort stability and ties, join multiplicity, date units, numeric precision and overflow behavior.
- Measure construction, decoding, filtering, sorting, grouping, mutation, layout conversion and the complete numerical workflow separately. Retain both first-use and reused-input runs.
- Report elapsed time, rows or bytes per second, peak resident memory and logical payload separately. Use allocation profiling to explain regressions rather than infer allocation counts from RSS.
- Vary tall/narrow, short/wide and large-square shapes; null fraction; skew and number of distinct keys; ordered/reversed/shuffled input; selectivity; unique/shared ownership; contiguous/scattered edits. Retain boundary fixtures around SIMD widths and validity bitmap words.
- Use fixed Apple silicon hardware for performance gates, record macOS/compiler/library versions, power and thermal conditions, and avoid concurrent builds. Treat measurements below timer resolution as unresolved.
- For future GPU paths, include command submission, synchronization and layout/materialization costs. Measure warm reuse separately. Unified memory alone does not eliminate those costs.

## Proposed repository layout

Keep small reference and edge-case inputs with tests. Store manifests, generators and workload definitions under `Benchmarks`; keep large downloads and generated files in the existing ignored `Benchmarks/Data` directory. Keep reports under `Benchmarks/Results`.

Each manifest should identify the source URL, dataset/version, license or redistribution terms, raw checksum, generator revision and seed, schema, shape, derived-file checksum, expected output and tolerance policy. A seed alone is insufficient if generator versions or serialization change. Generate one canonical input for all engines rather than asking each engine to reproduce random data independently.

Use three execution tiers:

1. Every change: small correctness fixtures, NIST reference cases, ownership tests, row alignment and supported interoperability checks.
2. Dedicated performance run: fixed medium datasets and representative shape/distribution variations on the same Mac.
3. Release comparison: larger public workloads, multiple scale factors, full workflow timings and memory limits. Run engines serially and identify adapted subsets honestly.

Promote the existing generated fixtures into this shared corpus first. Add NIST numerical references and an established dataframe workload next, then one pinned real-data workflow. Preserve adverse results in reports; do not collapse all cases into one overall speed score.
