# Kiraa reference status

## User clarification

On September 26, crabel99 clarified that the Kiraa version used in our investigations is not an official release. He reports serious bugs and regards it as experimental reference code, not production code. This records the status of our selected build; it is not a claim about every Kiraa version. This clarification did not include a new source audit or an enumeration of those bugs.

## Benchmark role

Use this build to study algorithms, memory layout, API choices and possible optimizations. It must not supply expected answers or determine SwiftSci certification. Independent mathematical references, published reference datasets and explicit output checks remain the basis for acceptance. Results from pandas, NumPy or SciPy also require independent validation rather than automatic acceptance.

Any future Kiraa adapter is optional research tooling. Pin its repository and commit, declare its supported semantics and known limitations, and validate every measured output. A passing workload establishes only that workload's observed behavior. Failed or unsupported workloads must remain visible and cannot support speedup claims.

## Roadmap correction

Earlier plans group Kiraa with the reference-engine migration work. Treat those entries as optional implementation comparisons, not a requirement for production benchmark or certification readiness. Prioritize broader SwiftSci dataframe correctness, independent numerical references and reliable measurement. Add Kiraa comparisons only where a specific implementation question makes them useful.

Keep the historical plans unchanged and read them with this correction. No production code, benchmark results or contribution-branch files changed for this clarification.
