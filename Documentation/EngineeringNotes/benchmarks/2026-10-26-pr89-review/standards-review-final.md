# Final standards review

Reviewed `09607a7e9caa2b7166651dcaaa167178f6097b55..4f33c76f39`, including both commits, against `CONTRIBUTING.md` and the required subtract-before-you-add skill. The initial review remains preserved separately.

No actionable documented-standards violations found.

- **Ownership and concurrency:** The internal immutable `PCAFullSVDLayout: Sendable` owns the related LAPACK dimensions and buffer counts within SwiftCluster (`Sources/SwiftCluster/Decomposition/PCAFullSVDLayout.swift:3–24`). This follows CONTRIBUTING’s Tier B guidance. It adds no public API requiring DocC.
- **Native boundary:** Exact Int32 dimension conversion and checked element/byte multiplication replace the unchecked output-buffer expressions (`PCAFullSVDLayout.swift:12–37`; `Sources/SwiftCluster/Decomposition/PCAComputation.swift:115–125`). The existing checked native workspace-query result remains authoritative (`PCAComputation.swift:127–131`). Removing the non-tight sufficient-bound guard avoids speculative restriction of supported inputs and follows subtract-before-you-add.
- **Tests and scope:** The target-local layout suite covers small rectangular shapes, invalid dimensions, byte overflow and the supported 24,000-square layout without giant allocations (`Tests/SwiftClusterTests/PCAFullSVDLayoutTests.swift:6–31`). The explicitly typed mean-overflow fixture checks failed-fit state preservation across input representations (`Tests/SwiftClusterTests/PCAMeanOverflowTests.swift:16–31`), consistent with CONTRIBUTING’s test-fixture guidance.

**Design judgment:** Retain the narrow layout type. It groups the values needed by one native boundary, centralizes repeated checked multiplication, and permits useful allocation-free tests. It introduces no unused hooks or general-purpose abstraction. The requested smell checks produced no actionable finding.

**Verification limit:** This review assesses source standards and structure. It does not itself certify the full local tests, numerical benchmark, or CI-compiler compatibility requirements; the parent run must supply those receipts. The independent specification review supplies the native workspace-query evidence behind the removed guard.
