CSV ingestion currently retains avoidable record metadata, streamed transformations can produce work ahead of the consumer, and CSV comparisons can time schema inference in one engine while supplying a complete schema to another. This change scopes record discovery and typed conversion to batches, makes streaming demand-driven, and requires matching complete schemas in the affected benchmark contracts.

The eager reader still owns its final columns and the unfinished stream retains the mapped input. Batching bounds transient record coordinates by rows; it does not impose a byte budget or a bound on the final frame. Oversized fields and retained output chunks still consume memory.

### Behavior and implementation

- Share record grammar between batch discovery and the count-only pass. Size eager output from the row count, release batch metadata after joined conversion, and retain borrowed bytes only within their valid scope.
- Validate sampled eager types against later values. Promote integer candidates when appropriate and retain original text when a numeric candidate fails. Explicit type overrides keep conversion-failure-as-null behavior. Streamed inference remains local to each chunk; callers needing fixed types provide overrides.
- Honor streaming row limits and cancellation, normalize headers, and avoid collisions between generated and existing header names.
- Add `columnDateFormats` for explicitly declared date columns and `columnConversionMode` for choosing serial or native parallel column conversion. Parallel remains the default; neither option sets worker affinity or global thread caps.
- Retain the earlier borrowed radix buffers and scalar-gather changes used by read-to-sort workflows.
- Version the matched CSV workloads, validate native input types and complete `csv_schema` requests, and include schemas when the acceptance verifier reconstructs those requests. Tests reject missing, wrong, or extra schema entries.

The CPU coverage fingerprint changes because the CSV contracts changed. The four existing numerical failure entries, their case bindings, allowed errors, reference bases, and tolerances are unchanged.

### Validation

Local validation at `428891dfd1777be592cb04c85eea1a5b433cb32c`, based on upstream `e005efcc1dd55bb40f9e1ad63ac29e2d29de5178`:

- Full Release and Debug package builds and tests: 1,594 passed in each configuration, zero failures or skips, all 15 declared test targets included.
- Benchmark controllers with the optional Metal checks enabled: 226 passed without skips.
- Formal CPU regression policy: passed across 16 profiles and 404 engine executions. SwiftSci passed 202 of 202 cases; pandas passed 198 of 202. The four reviewed Wampler comparison failures remain failed strict conformance, with zero new or blocking failures.
- Documentation check passed with 2,429 of 2,462 declarations documented, or 98.66%. The existing script's 100% success sentence is inaccurate.
- No long type-check warnings in changed Swift files under the recorded compiler diagnostics. The largest changed Swift test file is 197 lines. This does not establish compatibility with the hosted CI compiler or prove CodeQL and Codecov success.

The known-schema contracts now support equivalent comparisons. This PR does not claim a measured speedup against upstream `main`; the compact-storage comparison uses this reader as its baseline. Hosted CodeQL, Codecov, and required CI checks are pending on the submitted head.

### Scope and follow-up

This is the first of two review units, with 45 commits across 80 files. Selectable compact Double storage and its consumers are in dependent draft #86. Merge this PR first; #86 remains blocked until its branch is refreshed onto the merged base and revalidated. Engineering notes, raw benchmark evidence, and recovery bundles remain on the contributor's `codex/engineering-notes` branch and are excluded from the source diff.
