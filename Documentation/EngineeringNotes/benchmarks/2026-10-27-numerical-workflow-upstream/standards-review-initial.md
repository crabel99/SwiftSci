# Standards review

Reviewed HEAD `c676a0acfca0274fe05e2dc72bf7a0b45ab9f5c9` against fixed base `200d3935cc43396658a315bf4d5f745b6c7b496c` using `git diff 200d3935cc43396658a315bf4d5f745b6c7b496c...HEAD` and `git log 200d3935cc43396658a315bf4d5f745b6c7b496c..HEAD --oneline`.

Standards: `CONTRIBUTING.md` and the user-mandated `/Users/crabel/.agents/skills/principle-subtract-before-you-add/SKILL.md`. The repository contains no additional standards file matching the reviewed inventory. Source working tree was clean. No source files were changed by this review.

## Documented-standard findings

1. **[P3] Add the required Conventional Commit prefix to the contribution title.** `CONTRIBUTING.md:74` requires commit messages to adhere to Conventional Commits (`feat:`, `fix:`, `perf:`, `test:`). The sole commit subject is `Add a runnable CSV-to-classification numerical workflow example`, which omits the prefix. Use, for example, `feat: add a runnable CSV-to-classification numerical workflow example` for the final contribution commit or squash title. This is a contribution-metadata issue, not a source-code correctness failure.

## Heuristic findings

None. The executable composes existing public APIs, keeps boundary checks local, and adds no speculative scientific abstraction or extra package graph. The independent scalar checker intentionally duplicates the mathematical computation through a separate implementation; extracting shared production calculation would weaken its purpose. Internal CLI types add no public API requiring DocC documentation.

Summary: one documented-standard finding (P3 contribution metadata), zero heuristic findings. No source correctness finding identified. Full qualification was still running at review time, so this report does not certify its outcome.
