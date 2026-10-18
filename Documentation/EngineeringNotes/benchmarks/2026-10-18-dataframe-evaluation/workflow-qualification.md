# Matched CSV workflow qualification

2026-10-18. Qualification item Q0, implementation commit `d23bf7cac92fe9f9c10bd98046ca8ade354b5a3c`.

Complete CSV ingestion responsibilities now match for the registered streaming and wine preprocessing comparisons. This establishes a screening baseline for the next execution experiments. It does not establish a candidate improvement or complete application-scale coverage.

## Contract and controls

- Every engine receives the same complete native schema. Integer identifiers remain Int64, measurements remain Double, and mixed categories and flags remain String and Bool.
- Streaming read, filter and grouping compare SwiftSci with pandas at fixed 10,000-row boundaries. Wine preprocessing compares SwiftSci, pandas, Polars and DuckDB.
- Before warmups, each worker reads with its timed reader configuration, checks actual input types and row counts, and releases the raw preflight input. Streaming preflight checks every chunk. The response records the observed input schema.
- Every timed sample repeats ingestion and the declared transformations. The complete native result remains alive through the end timestamp. Canonical export and independent full-value validation occur afterward.
- Historical v1 files and receipts retain their fingerprints. New plans reject the unmatched v1 contracts. Active profiles and the migration inventory now use v2.
- Runs used AC power, CPU backends, native inner parallelism, five fresh-process rounds, two warmups and five measured samples per process. Engine order rotates. Configured pools are not measured active thread counts or evidence of E-core/P-core placement.

## Streaming results

Each input has 100,000 rows. Values are milliseconds: median of five process medians, followed by the minimum and maximum process median. The range describes observed spread, not a confidence interval.

| Input and operation | SwiftSci ms | pandas ms |
| --- | ---: | ---: |
| medium-csv-stream-read | 1.526 [1.474, 1.566] | 13.298 [13.194, 13.332] |
| medium-csv-stream-filter | 1.495 [1.467, 1.570] | 14.748 [14.724, 14.763] |
| medium-csv-stream-group | 1.498 [1.436, 1.561] | 26.010 [25.341, 26.127] |
| mixed-medium-csv-stream-read | 7.422 [6.778, 7.457] | 17.008 [16.986, 17.192] |
| mixed-medium-csv-stream-filter | 7.684 [7.484, 8.179] | 19.288 [18.901, 19.445] |
| mixed-medium-csv-stream-group | 7.377 [6.940, 7.835] | 31.013 [30.486, 31.764] |

## Wine preprocessing results

The pinned red-wine input has 1,599 rows. The complete path reads all columns, filters quality, stably sorts alcohol, fits population scaling on the selected rows and exports IDs, targets and the row-major matrix. This descriptive preprocessing fixture does not measure training quality or held-out prediction.

| SwiftSci ms | pandas ms | Polars ms | DuckDB ms |
| ---: | ---: | ---: | ---: |
| 0.507 [0.492, 0.522] | 1.709 [1.625, 1.978] | 1.515 [1.477, 1.538] | 18.693 [18.569, 18.798] |

Native implementations may fuse intermediate work. The comparison requires the same complete final result and timed responsibilities; it does not require identical intermediate arrays. These timings do not prove which internal mechanism caused a difference.

## Validation and limits

- All 400 timed samples passed full-output validation. All 80 worker responses contain matching observed input schemas. The retained artifact audit and the workflow eligibility checker passed.
- All 88 fresh-process worker checks passed. They cover complete outputs, absent and incorrect schemas, corrupted expected outputs, mixed types, integer-looking Double measurements and a 10,003-row input with a partial final chunk.
- The controller suite discovered 224 tests: 220 passed and four optional Metal tests were skipped. The uninstrumented Release worker built successfully.
- The existing scientific and persisted CPU controls passed 16 worker executions and 32 measured samples. They cover the checked numerical workflow, feature/row-order variants, training-only preprocessing, held-out prediction and fresh-process native reload. Their small fixtures and legacy execution mode are conformance evidence only. Their timings are excluded from the tables and performance rankings. Core ML routes were excluded from these CPU controls.
- Swift streaming still maps the whole input and constructs a record index. A chunked public interface does not prove bounded peak memory. Whole-process RSS includes startup, preflight, warmups and validation; it cannot isolate operation scratch or retained storage.
- These runs did not measure energy, allocation counts, concurrent interference, cold-cache behavior or large application-scale numerical pipelines. No memory policy, parallel dispatcher or new storage layout is approved by this evidence.
- The earlier matched operation results and historical benchmark fingerprints remain unchanged. This increment changes benchmark adapters and contracts; production parser and sorting code are unchanged.

## Next experiment

S1 tests row-partitioned gathering on the existing column representation. Compare it with the unchanged gather path before changing the permutation algorithm. Include complete stable sorting, narrow and wide tables, small protected cases, source ownership and additional scratch. Record the screening cases and resource limits before running; reserve different confirmation cases and declare useful absolute gains before confirmation. S2 and S3 remain competing algorithm experiments.

## Reproduce and inspect

- [Machine-readable qualification](workflow-verification.json)
- [Workflow audit tool](check-csv-workflows.py)
- [Evaluation protocol](README.md)
- [Experiment register](experiments.tsv)
- Evidence directory: `/Users/crabel/local-ai/spl/swiftsci/csv-sort-throughput-20261017/workflow-qualification-20261018`.
- `build-worker.py`, `check-workers.py` and `run-workflows.py` reproduce the local build, conformance checks and registered runs. Their destination directories must be new to preserve earlier evidence.
- `committed-source.json` maps the original build source files to the implementation commit. Original build and run receipts retain their recorded parent commit.
- Source fingerprint: `761f848cd50811e62f9e13b4089a25d62675020c8f9599415f94da7fe672f9c8`.

Run the checker with the Python environment used for the benchmark:

```sh
python check-csv-workflows.py \
  --repo /private/tmp/swiftsci-csv-sort-20261017 \
  --streams /Users/crabel/local-ai/spl/swiftsci/csv-sort-throughput-20261017/workflow-qualification-20261018/stream-comparison/run.json \
  --wine /Users/crabel/local-ai/spl/swiftsci/csv-sort-throughput-20261017/workflow-qualification-20261018/wine-comparison/run.json
```
