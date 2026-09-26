# Integrated dataframe optimization

Baseline: SwiftSci 2694d303f8. Production benchmark: ../production-comparison/results/20260926T033814Z/REPORT.md.

- [x] Ground: trace CSV, grouping, sorting, column storage and materialization; profile representative workloads.
- [x] Sketch: compare at least two distinct designs against correctness, memory traffic, Apple Silicon execution, API depth and measured benefit.
- [x] Agree: synthesize the design without changing established semantics; no user checkpoint requested.
- [x] Implement: work in verified increments, with production APIs and targeted regression tests.
- [x] Scrap or revise: reject candidates that add copies, weaken semantics or fail measured acceptance criteria.
- [x] Verify: full Debug and Release suites and matched production benchmarks; no push or PR.

Arena phases: frame, fan out, cross-judge, pick, graft, verify. Candidate files are independent. Source ownership is divided by subsystem; the primary agent reviews all changes and serializes builds, measurements and commits.

Local commits completed: flat CSV storage, bounded composite grouping, ASCII null matching. Adaptive Double sorting is committed; full-suite and sparse-policy verification passed. Pure unconditional radix and full-input comparison preparation were rejected after measurement.
