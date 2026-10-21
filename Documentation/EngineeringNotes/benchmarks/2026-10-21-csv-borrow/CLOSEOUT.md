# CSV resource-efficiency closeout requirements

Actual reference-file comparisons are required before closing this segment or recommending a production default. Synthetic fixtures establish controlled behavior; they do not establish the frequency or magnitude of benefits on real files.

## Reference inputs

Start with the original distributions of these datasets:

- [UCI Individual Household Electric Power Consumption](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption), dataset 235. This tests energy observations with missing measurements and the source's original delimiter and timestamp fields.
- [UCI Beijing Multi-Site Air Quality](https://archive.ics.uci.edu/dataset/501/beijing+multi+site+air+quality+data), dataset 501. This tests environmental observations with missing values, measurements, and station identifiers. Preserve each original file; do not concatenate or requote files just to select a favorable parser path.

Inspect the supplied documentation and original bytes before fixing the run plan. Record source URL, retrieval time, license, archive and member hashes, member names, sizes, row counts, declared null tokens, schema, and observed quoting. Download and decompress outside the measured operation. Do not commit large dataset copies to the library.

## Comparability

1. Compare the pinned production reference, the earlier compact candidate, and the final candidate on identical bytes. Keep validation and resource differences visible for each file.
2. Verify column names, order, types, row counts, null counts, and values against an independent reference. Use the same interpretation of missing values and timestamps. Separate incompatible interpretations rather than timing them as equivalent results.
3. Report inferred-schema and supplied-schema runs separately when both are supported and correct. No variant receives free schema knowledge that another variant must discover.
4. Retain original encoding, delimiters, quoting, and file boundaries. Report which parser path is actually exercised. Files that get no compact-index benefit are part of the evaluation.
5. Use the same CPU backend with native parallelism. Keep power conditions and setup/release boundaries matched, alternate process order, and report the spread under normal desktop activity.
6. Measure full public reads and output release. Record summed CPU time, elapsed time, process peak RSS, and held output heap separately. Do not infer energy savings from CPU time alone.
7. Preserve all valid measurements, including regressions. Report correctness failures as failures, never as cheap successful runs.

## Decision

Summarize improvements and regressions per workload rather than collapsing CPU, latency, and memory into an invented weighted score. If a workload retains a material resource tradeoff, document the caller choice needed. Passing synthetic and sanitizer checks alone does not close this gate.

Status on 2026-10-21: the [original reference-file comparison](../2026-10-21-csv-reference/README.md) completed this gate for the stated schemas. All twelve air-quality files improve CPU time and peak memory; the unquoted energy file is effectively neutral. Automatic inference remains unqualified because both pre-existing inference defects reproduce in all three variants. Production integration and separate inference repairs remain outstanding.
