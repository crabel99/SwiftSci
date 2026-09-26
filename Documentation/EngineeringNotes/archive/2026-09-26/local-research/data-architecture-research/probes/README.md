# Data boundary diagnostic

This small executable checks current SwiftSci dataframe boundaries. It uses SwiftDataFrame and SwiftStats without MLX. It changes no production files.

The inputs are synthetic and printed in `result.jsonl`. The executable reports observed behavior and independent expected results; exit code zero means the probe completed, not that the implementations matched the expectations.

Run from any directory:

```bash
swift build --package-path /Users/crabel/local-ai/spl/swiftsci/data-architecture-research/probes -c release --product BoundaryProbe --disable-sandbox -j 4
/Users/crabel/local-ai/spl/swiftsci/data-architecture-research/probes/.build/release/BoundaryProbe
```

`metadata.json` records source commit, working-tree state, compiler version and source/binary hashes for the saved run. `build.log` records the original build. There are no production patches or commits in this diagnostic.
