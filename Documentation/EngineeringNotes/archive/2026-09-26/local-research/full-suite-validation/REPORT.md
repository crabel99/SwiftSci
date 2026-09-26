# Full SwiftSci test validation

Validated `2694d303f86fd1e71e32ab1633542408b669b90e` on Apple M4 Max, arm64, macOS 27.0, Xcode's Swift 6.4 toolchain. The source was tested before committing the one-line import correction; the commit contains exactly that tested change.

| Check | Result |
|---|---|
| Full native Xcode Debug suite | 840 passed, 0 failed, 0 skipped |
| Full native Xcode Release suite | 840 passed, 0 failed, 0 skipped |
| Upstream CI test selection with coverage | 456 passed: 62 XCTest, 394 Swift Testing |
| Complete package Release build | Passed |

Xcode reports 840 test definitions and 864 executions when parameterized cases are counted individually. All 14 package test targets are included in each full run. Both full runs include the MLX/GPU suites skipped by upstream CI. The Release test build retains optimization and sets `ENABLE_TESTABILITY=YES` for existing `@testable import` statements.

## What blocked testing

1. The original Documents-folder build failed during signing. Its generated bundles had `com.apple.FinderInfo` and file-provider attributes. A copied bundle failed signing with FinderInfo present and signed successfully after removing only that attribute. Moving generated output to `~/Library/Caches/SwiftSci` avoided the failure. The file-provider attributes support, but do not by themselves prove, the source of the metadata. [Apple explains the signing restriction](https://developer.apple.com/library/archive/qa/qa1940/_index.html).
2. With a clean build directory, the SwiftPM test runner compiled Metal libraries but five test targets could not locate MLX's default metallib at runtime. The native Xcode test runner located the resources and ran the suites. The pinned MLX README recommends `xcodebuild` for its Metal tests. No shader, library, numerical implementation, or test expectation was changed.
3. Xcode's dependency scanner found that `SparseMatrixTests.swift` imported undeclared sibling module `SwiftML`. The test needs `SwiftMLError`, which belongs to `SwiftDataFrame`. Commit `2694d303f8` changes that import to its actual owner. The existing SparseMatrix tests passed afterward.
4. Xcode's Release configuration normally omits testability. The local test runner enables it for testing without changing Release optimization.

## Repeat locally

Run these sequentially because they share an Xcode build directory:

```sh
~/local-ai/spl/swiftsci/run-full-tests.sh debug
~/local-ai/spl/swiftsci/run-full-tests.sh release
```

The runner retains a timestamped log, environment record, result bundle and JSON test summary under this directory. It uses the checked-in dependency versions and fails if the inspected MLX revision changes. All eight dependency checkout revisions were verified against `Package.resolved`.

Xcode's package-plugin validation exception applies only to each invocation. The pinned MLX CudaBuild plugin was inspected and returns no build commands on macOS. No global Xcode trust setting was changed.

The source checkout's old `.build` remains in place. A plain `swift test` from that checkout can still encounter its signing or Metal-resource problem; use the full-suite runner for GPU validation.

## CI comparison

The checked-in `.github/workflows/ci.yml` builds Debug and Release, and runs coverage tests with eight suites excluded. Its deployment target remains upstream's 14.0; all local execution here was on Apple Silicon and macOS 27.0. No Intel build was performed.

The CI-equivalent command was run from the source checkout:

```sh
MACOSX_DEPLOYMENT_TARGET=14.0 swift test \
  --scratch-path "$HOME/Library/Caches/SwiftSci/full-suite" \
  --force-resolved-versions --enable-code-coverage \
  --skip SwiftMLTests --skip SwiftClusterTests --skip SwiftForecastTests \
  --skip SwiftExplainTests --skip SwiftPreprocessingTests \
  --skip SwiftOptimizeTests --skip SwiftLLMTests --skip SwiftVisionTests
```

The complete Release build used the same scratch path, pinned resolution and deployment target with `swift build -c release`. These local results cover builds and tests. They do not claim to execute the remote CodeQL, documentation or publishing jobs.

## Evidence

- [Debug native summary](20260926-investigation/swiftsci-full-debug-summary.json)
- [Debug Xcode result bundle](20260926-investigation/debug-passed.xcresult)
- [Release native summary](release-20260926T032255Z-NrJnHe/summary.json)
- [Release Xcode result bundle](release-20260926T032255Z-NrJnHe/tests.xcresult)
- [Final CI-equivalent test log](20260926-investigation/ci-safe-final.log)
- [Complete Release build log](20260926-investigation/swiftsci-ci-release-build.log)
- [Original signing failure](20260926-investigation/swiftsci-full-repro.log)
- [SwiftPM Metal resource failure](20260926-investigation/swiftsci-full-clean-debug.log)
- [Xcode undeclared-import failure](20260926-investigation/swiftsci-xcode-full-debug-validated.log)

The import fix is committed locally. Nothing was pushed and no PR was opened.


## Integrated dataframe follow-up, September 26

Final source commit `dc31b5f1af` on `codex/dataframe-pipeline-optimization` passed the complete suite in Debug and Release. Each result reports 863 tests passed, zero failures, zero skipped tests and no runtime warnings. Parameter expansion produced 905 device-level test executions in each configuration. MLX-dependent targets were included.

- [Debug result](debug-20260926T042551Z-h43q2l/summary.json)
- [Release result](release-20260926T042652Z-XTcq8F/summary.json)
- [Integrated design and source comparison](../integrated-optimization/INTEGRATION-NOTES.md)

Both builds used the existing out-of-Documents Xcode cache and pinned MLX approval. No package versions or global trust settings changed.
