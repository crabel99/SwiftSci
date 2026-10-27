# Repair safe-test coverage export

Base: upstream main 200d3935cc43396658a315bf4d5f745b6c7b496c, after merged classification #93, agent #95 and stable embeddings #96.

Replace positional multi-binary llvm-cov arguments with explicit objects for every discovered macOS XCTest executable. Keep paths with spaces intact. Remove the exporter error mask. Validate required executed source records for SwiftDataFrame, SwiftAgent and SwiftNLP before releasing LCOV to stdout/upload. Missing profiles, absent/malformed bundles, llvm-cov failures and absent required executed records must fail with diagnostics. Retain llvm-cov stderr and its nonzero status. Leave Codecov thresholds/exclusions, dependency pins, safe-test skips, numerical behavior and libraries unchanged.

Use the smallest repository helper and existing Python unittest discovery. Prove the real workflow command against real instrumented multi-binary fixtures before and after the fix, including paths with spaces and exporter/input failures. Also verify complete actual package safe-test coverage, not only synthetic fixtures. Run applicable complete local checks before a focused draft PR; publish records separately. Preserve known benchmark, MD5 and MLX cold-start limits. No upstream merges, comments or review requests.
