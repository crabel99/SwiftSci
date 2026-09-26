# Integrated numeric and grouping design

## Constraints and decisions

The execution target is modern Apple Silicon. The inherited macOS 14 package minimum is not an Intel requirement or a design preference from the user. This pass does not need a newer OS API, so changing the manifest would not improve these loops. All validation and measurements target arm64 Release on the local M4 Max.

Public TypedColumn optional-array storage remains unchanged. Compact buffers, validity ownership and model adapters remain on the compact-storage branch. Within this branch, reduce dynamic operations and data passes before adding vector intrinsics, threads or GPU transfers.

Correctness takes precedence over throughput. Ordinary sums retain Double output and compensation; checked sums retain exact integer output. Typed filter comparison now preserves represented numeric values in both mixed-type directions, including integer extrema, fractional thresholds and NaN. Null remains distinct from a present NaN.

## CPU kernels

Resolve column types and comparison thresholds once per call. Specialized generic loops scan concrete arrays and append selected positions. Integer thresholds are classified by mathematical boundary before scanning; integer data never round through Double. Float data widen exactly. Inexact integer thresholds of floating columns adjust the comparison at the representable boundary.

This follows the X100 observation that per-row interpretation obscures independent work from the compiler. It does not establish that the resulting loop saturates memory bandwidth. Apple CPU counters, allocation measurements and generated code are the next tools if timings leave unexplained costs.

## Group identity

Alternative A hashes full row keys or representative rows. It can reduce passes, but a general implementation requires dynamic equality dispatch or a new hash table and collision machinery. Per-row arrays of erased values introduce allocations.

Chosen alternative B refines groups by one typed column at a time. Dictionary identity is the prior group ID plus the current optional value. Correctness follows inductively: two refined IDs match only when their prefixes and current values match. Memory for row IDs remains linear in row count, rather than retaining every column's code array. Hash equality alone never establishes group identity.

The existing bounded integer lookup remains useful for narrow ranges. The 65,536-entry limit is a software allocation policy, not a claimed Apple cache size. All grouping retains first-seen representatives and String output labels. Floating zeros share identity; NaNs form a present group distinct from null. Custom non-Hashable values retain a documented description fallback because AnyColumn supplies no equality operation.

## Metadata and ownership

Rename retains the immutable array and cached null count. Filtering counts nulls while producing results; unique values already know whether they emitted null. No storage alias mutation or unsafe Optional-layout assumptions are introduced.

## Evidence and boundaries

Regressions run before each correctness fix, then targeted and integrated tests. Performance comparisons use complete values and row order, not just result shape. Run benchmarks serially; retain raw samples and source revisions. Do not call a broken baseline's missing sums a valid speed comparison.

Research and direct citations are in hardware-research.md, algorithm-research.md and semantics-research.md. Primary foundations include Apple Swift specialization and CPU profiling, X100, column-store materialization, Roofline, and pandas/DuckDB grouping implementations. Their findings guide experiments; their historical timings do not predict this Mac's performance.
