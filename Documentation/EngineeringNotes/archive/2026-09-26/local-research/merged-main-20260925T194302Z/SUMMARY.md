# Merged main rebuild and tests

Fresh builds completed on September 25, 2026 for merge commit `f65e15de19d3d2de7da707cf8e765b8ec73862d4` on Apple Silicon with Swift 6.4.

Generated build artifacts were cleared before rebuilding. Source files were unchanged.

| Configuration | Module build | Scoped tests | Independent checks | Total |
|---|---|---:|---:|---:|
| Debug | Passed | 249 passed | 10 passed | 259 passed |
| Release | Passed | 249 passed | 10 passed | 259 passed |

The module build targets SwiftForecast and its SwiftDataFrame and SwiftStats dependencies. Testing covers those three modules, the new regressions, and the independent known-answer checks. It does not cover the rest of SwiftSci.

Both runs include the descending-sort regression. No test failures occurred. The working tree remained clean.

Logs in this directory record each build and test run. `revision.txt` and `toolchain.txt` identify the tested source and compiler.
