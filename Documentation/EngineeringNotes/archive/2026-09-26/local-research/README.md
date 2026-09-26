# SwiftSci local build and TDD result

The local checkout now belongs to your fork at https://github.com/crabel99/SwiftSci. Nodibell remains the upstream remote. The local checkout, fork main, and upstream main are synchronized at merge commit `f65e15de19d3d2de7da707cf8e765b8ec73862d4`. The checked-out branch is `main`.

The Release sorting failure was isolated and the workaround was merged upstream in [PR #38](https://github.com/Nodibell/SwiftSci/pull/38), closing [issue #37](https://github.com/Nodibell/SwiftSci/issues/37). A standalone program reproduces the original failure with Swift 6.4 optimization enabled and no SwiftSci dependencies. One comparison closure avoids the compiler trigger while preserving missing-values-last ordering.

## Verification

- Three new regression tests failed before the production change and passed after it.
- All 249 scoped upstream and regression tests pass in Release and Debug modes.
- All 10 independent checks pass in Release mode, including the original sorting reproduction.
- Existing upstream expectations were not changed or weakened.
- Dataframe, statistics, and forecasting modules were covered. This is not a full-package test or security audit.

The patch and regression tests are in `/Users/crabel/Documents/src/SwiftSci`. The standalone reproducer and issue text are kept outside the repository in `/Users/crabel/local-ai/spl/swiftsci/issue-material`. The merged source tree matches the tested fix branch exactly.

[Issue text and compiler reproduction](/Users/crabel/local-ai/spl/swiftsci/issue-material/issue.md)

## Rerun current tests

```sh
~/local-ai/spl/swiftsci/run-tests.sh release
~/local-ai/spl/swiftsci/run-tests.sh debug
```

The runner executes the 249 scoped tests and then the 10 independent checks. To run only the new regressions:

```sh
~/local-ai/spl/swiftsci/sorting-tdd/run-tests.sh release DescendingNullSort
```

The `sorting-tdd` package links directly to the repository's current test directories. The original `validation` package retains unchanged upstream test copies and the independent checks. Runtime dependency revisions still match the pinned baseline.

## Evidence

- `tdd-red.log`: minimal failing regression before the workaround.
- `tdd-red-expanded.log`: three failing regression tests before the workaround.
- `tdd-green.log`: the same three regressions passing afterward.
- `tdd-full-release.log` and `tdd-full-debug.log`: 249 passing tests in each configuration.
- `tdd-independent-release.log`: 10 passing independent checks.
- `standalone-debug.log`, `standalone-release.log`, and `standalone-workaround.log`: compiler isolation.

`BASELINE-20260925.md` and the original logs retain the pre-fix build results. `run-tests-baseline.sh` retains the old verification script; it intentionally rejects source changes and therefore will not run against the patched checkout.
