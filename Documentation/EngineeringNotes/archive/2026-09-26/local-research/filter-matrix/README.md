# Filter matrix

This external benchmark separates numeric selection, column gathering, and the complete public filter call. It predeclares 96 tuning cases and 24 held-out cases. Each case runs in a fresh process for each binary and round. Comparisons run serially with alternating binary order, three process rounds, three timed repetitions, and two warmups per phase.

The tuning matrix covers Float64, Float32, native Int, and Int32 predicates, 1,000 to 1,000,000 rows, 1, 3, 8, or 16 columns, nominal selection rates of 0%, 1%, 10%, 50%, 90%, and 100%, null rates of 0%, 1%, and 30%, and clustered, shuffled, and evenly distributed matches. Three-column cases use two Int64 payload columns, matching the production benchmark. Wider cases mix numeric payload types.

The holdout changes the seed, sizes, widths, selection rates, and null rates. Eight holdout cases include String and Bool payloads. It should run only after choosing a candidate from the tuning matrix. Do not retune against it and then describe it as an untouched holdout.

The nominal selection rate applies before predicate nulls are excluded. Every result records its actual selection rate. Input generation computes expected row indices independently of SwiftSci's predicate implementation. Before timing, both gather and full filter outputs are checked against every expected typed value, column order, schema, row order, and null count. Empty selections preserve the current public behavior, a frame with no columns. The validation digest covers selected row positions and input null counts; it supplements exact value checks rather than replacing them.

The predicate is greater-than zero. Signed row numbers make matching values distinguishable and exactly representable in all four numeric types at these sizes. This matrix measures layout and selection density effects. It does not substitute for regression tests of other operators, NaNs, infinities, integer limits, or fractional thresholds.

Peak RSS includes fixture construction, independent validation, all three measured phases, and allocator retention. It is a process high-water mark, not isolated filter allocation. The stop timestamp precedes output release for each operation. Output creation is timed; destruction is outside the timed interval.

## Build

Use a separate label for every candidate. The copied binary and its metadata preserve the commit, tracked diff hash, compiler version, and binary and harness hashes. Builds are serial, using one cache. Do not edit SwiftSci while a build is running.

```sh
./build.sh baseline
./build.sh candidate
```

An optional second argument selects another SwiftSci checkout. The package copies that checkout's dependency lock file. Existing baseline binaries remain unchanged when the shared build cache rebuilds a candidate.

## Run

```sh
./run.py --binary baseline="$PWD/binaries/baseline/FilterMatrix" \
  --binary candidate="$PWD/binaries/candidate/FilterMatrix" \
  --quick --output results/quick

./run.py --binary baseline="$PWD/binaries/baseline/FilterMatrix" \
  --binary candidate="$PWD/binaries/candidate/FilterMatrix" \
  --partition tuning --output results/tuning

./run.py --binary baseline="$PWD/binaries/baseline/FilterMatrix" \
  --binary candidate="$PWD/binaries/candidate/FilterMatrix" \
  --partition holdout --output results/holdout
```

Use `--cases t14,t43,t68` for a diagnostic subset. The executable itself accepts `CASE_ID REPETITIONS WARMUPS` or `--list`. The orchestrator saves raw measurements as JSON lines, metadata, and per-case summary statistics. Inspect per-case regressions and process-to-process spread before using aggregate speedups.

## Separate operator checks

The optional operator mode adds 96 selection-only cases without changing the original matrix. Each of four numeric types covers six comparison operators and null/not-null checks at 100,000 and 1,000,000 rows. It includes exact integer thresholds, fractional thresholds that cannot be represented as integers, and a Double threshold halfway between adjacent Float32 values. Floating input includes NaNs, positive and negative infinity, signed zero, threshold neighbors, and random finite values. The original 64 cases use null rates of 1% and 30%. Cases o64 through o95 repeat each exact-threshold operator/type combination at one million rows without nulls. Equality, inequality, edge thresholds, and null checks produce different selection densities.

Expected indices come from direct scalar comparisons on the actual stored value. Integer inputs stay inside the exact Double range. Every returned index is compared before timing and after every sample. The comparison is outside the timestamp interval. This mode is not a test of extreme integer threshold semantics; dedicated regression tests cover those boundaries.

```sh
binaries/candidate/FilterMatrix --operator-list
binaries/candidate/FilterMatrix --operator o17 3 2
./run-operators.py --binary baseline="$PWD/binaries/baseline/FilterMatrix" \
  --binary candidate="$PWD/binaries/candidate/FilterMatrix" \
  --output results/operators
```

Both binaries must be rebuilt with this optional mode. An older binary preserves its original matrix behavior but does not recognize operator arguments.
