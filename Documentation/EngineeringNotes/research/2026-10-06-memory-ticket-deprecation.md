# Legacy memory-ticket deprecation

Date: 2026-10-06. Implementation commit: `299221aab3865c57f8220bc8f2f03854708c6c65` on `codex/memory-library-reuse`, based on `530151b4fa700cdd55cca95dc43d4d5080469d2a`.

## Change

Deprecated SwiftPreprocessing.WiredMemoryManager and WiredMemoryTicket without removing public declarations or changing their runtime implementations. The migration guide now distinguishes estimated-byte admission from MLX wired-memory coordination and task-count scheduling. It explains MLX's cancellation and policy differences rather than promising a direct substitution. The agent guide no longer claims the task-count limiter prevents out-of-memory errors.

The legacy actor and ticket remain for compatibility. This commit starts retirement but does not reduce allocator or scheduling implementation code. Existing explicit ticket cleanup still clears the MLX cache. Cache-policy changes and actual deletion require separate decisions and validation. Consumers that treat deprecation warnings as errors may need to adjust their builds or migrate.

## Validation

Nine existing Release tests passed: three concurrency/ticket tests and six prepared-regression integration tests. No failures or skips. Existing legacy calls still compile and execute, emitting the expected deprecation diagnostics. No new regression test was added because runtime behavior did not change.

The revised guide's complete Swift example was compiled in the isolated validation snapshot. DocC builds for SwiftPreprocessing and SwiftAgent passed. Xcode produced symbol-only archives, so both actual documentation catalogs were also converted explicitly. Those conversions passed without warnings, and the rendered JSON contains the migration guide, corrected agent text, and both deprecation notices. The full library test suite was not run, and this change makes no performance claim.

A source comparison excluding full-line comments and deprecation attributes verified unchanged runtime implementation in both legacy types. Builds used only tracked files plus the documentation compilation example, excluding unrelated cloud-sync duplicates. The real checkout's untracked files were left untouched. The preserved production benchmark executable was restored after validation rebuilt products in the shared build cache.

## Next step

Prototype retained Arrow buffers for supported numeric columns, preserve value and null semantics, and test slices, chunk handling, mutation isolation, and release. Compare copies, memory, and execution time before replacing production storage. The async CPU cleanup prototype remains a separate preserved experiment.

No push or PR was performed. Engineering decisions and validation summaries remain on codex/engineering-notes.
