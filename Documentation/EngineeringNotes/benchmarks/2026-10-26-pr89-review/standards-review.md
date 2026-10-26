# Standards review

Reviewed `09607a7e9caa2b7166651dcaaa167178f6097b55..6061a70217`, including the commit log, against `CONTRIBUTING.md` and the required subtract-before-you-add skill.

No actionable documented-standards violations found.

- **Module ownership and concurrency:** `PCAFullSVDLayout` is an immutable, internal `Sendable` value in SwiftCluster (`Sources/SwiftCluster/Decomposition/PCAFullSVDLayout.swift:3–11`), matching CONTRIBUTING’s Tier B rule for value-semantic configuration/data containers. It exposes no new public API requiring DocC.
- **Native boundary and allocation arithmetic:** The layout consolidates LAPACK dimension conversion and checked output/workspace sizing (`PCAFullSVDLayout.swift:12–45`). `fullSVD` consumes those counts before constructing the native output buffers (`Sources/SwiftCluster/Decomposition/PCAComputation.swift:115–125`). This is a focused owner for related backend constraints; the helpers avoid repeating overflow handling.
- **Tests:** Both new suites live under the correct target. The shape tests include rectangular layouts, invalid dimensions and an LP64 workspace boundary without allocating giant matrices (`Tests/SwiftClusterTests/PCAFullSVDLayoutTests.swift:6–26`). The mean-overflow suite uses an explicitly typed fixture and checks preservation of the fitted state across four input routes (`Tests/SwiftClusterTests/PCAMeanOverflowTests.swift:16–31`). These conform to the documented fixture/type-checking guidance.

**Design judgment:** The extra layout type is justified by its production caller and allocation-free boundary testing. It bundles a single backend concern, adds no public extension points, and replaces the three unchecked allocation expressions. I would retain it. No useful extraction, renaming, or removal emerged from the requested smell checks.

**Verification limit:** This source review does not certify CONTRIBUTING’s full local test, numerical benchmark, or CI-compiler compatibility requirements; those need the parent run’s actual receipts. In particular, assessing the mathematical completeness of DGESDD’s workspace bound is part of the independent specification review, not an inferred style violation.
