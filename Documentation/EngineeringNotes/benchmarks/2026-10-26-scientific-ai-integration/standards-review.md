## Standards

No actionable findings in `git diff a1e234d25677d91ce5914062603c41233fe13c09...c4de6cc866fff6f52100535dbcb38dd708558200`.

Reviewed CONTRIBUTING.md and the required subtract-before-you-add skill, including the code-review skill's smell baseline. The integration retains an actor for mutable PCA fitting state and Sendable value types for numerical inputs/results. Prepared paths avoid nested-row conversion, use the existing numerical backends, and document the added public overloads. The matrix replacement helper preserves private provenance through the existing constructor; its focused tests check both layouts, repeated/empty selections, and copy-on-write snapshots.

The documentation change removes the inaccurate unconditional success claim without changing the placeholder exit policy. Its five temporary-fixture tests cover measured coverage, empty scans, and placeholder failure. The workflow label reflects that behavior.

No documented-standard breach or useful baseline-smell finding was identified. Existing undocumented properties outside changed declarations were not attributed to this diff. Build, concurrency, numerical benchmark, and workflow execution checks were excluded from this read-only standards review as requested.
