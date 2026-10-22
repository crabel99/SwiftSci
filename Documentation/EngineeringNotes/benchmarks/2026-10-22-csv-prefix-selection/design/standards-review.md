# Standards review

Reviewed `git diff c906c3fbbb0baf1357438a7079921a6448e0c9e5...HEAD`, including commits `f9a99ce54c` and `167d9a4e6f`, against `CONTRIBUTING.md`, neighboring CSV implementations, and the requested constraints.

No documented-standard violations or actionable code-smell findings.

- The immutable `Sendable` decoder follows the repository's value-container concurrency guidance. It owns its token set and masks. It introduces no shared mutation, retained input pointers, public API, or unchecked concurrency declaration.
- Selection belongs to the existing column factory. Eager reads provide the total selected record count, retries retain that count, streaming supplies the actual chunk count, and single-field probes supply one. The renamed argument distinguishes this work estimate from allocation capacity.
- Preparing `CSVNullMatcher` only for its consumers removes unused work. The new decoder bounds token visits and inspected bytes before installation, keeps original String membership as the authority, and adds no per-row strategy choice to the hashed fallback.
- The additional enum arms follow the existing concrete-decoder dispatch. Replacing these switches with a new polymorphic layer would add abstraction without an established need.
- The new test files contain 50 and 37 lines. Fixture collections and closure results use concrete types; their expressions are small. They exercise constructor boundaries, owned state, Unicode and invalid bytes, and public eager/streamed reads under both policies.

The similar byte-to-String test loops follow the existing suite and test different decoders. I would keep them local rather than introduce a shared test abstraction for this change.

This was a read-only source review. It did not run builds, tests, or benchmarks. Performance and compiler compatibility remain qualification results, not conclusions of this review.
