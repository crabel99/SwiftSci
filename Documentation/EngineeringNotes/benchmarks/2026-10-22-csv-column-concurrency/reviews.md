# Review of selectable CSV column conversion

Fixed point `c8c56d1eb25f51afa27c452c6f656cb79dec73a6`.
Reviewed head `9c067c6c5116d78c0849073acea7fb150404efab`.

## Standards

No documented-standard violations or actionable code smells found. Public declarations have DocC comments. The shared scheduling helper keeps the decision in one place for eager and streaming conversion. Both modes have feature tests. Compiler and benchmark compliance require the separate executed checks.

## Spec

No actionable findings. The option reaches initial eager conversion, retries, and streaming construction. Parallel remains the default and uses native system scheduling. Serial invokes the same conversion closures synchronously. The diff preserves batch bounds, inference, fallback, cancellation, limits, storage, and the deployment minimum.

Two independent read-only reviewers inspected the pinned diff. Neither ran tests or benchmarks.
