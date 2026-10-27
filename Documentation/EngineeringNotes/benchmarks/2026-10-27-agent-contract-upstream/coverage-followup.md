# Next independent CI correction

Observed on agent source 3a9482122c, with no workflow changes: all eight main workflow run steps exit0, but its original LCOV contains no SwiftAgent/ReActAgent record. Main safe tests execute 20 XCTest and 42 SwiftTesting agent definitions. The added local guard fails as expected.

The original export gives multiple test executables as positional arguments to llvm-cov. llvm-cov treats the first as the covered object and subsequent positional arguments as source filters. The completed explicit-object supplemental export uses one positional object plus `-object` for the remaining 14 binaries, the same profile and unchanged source. It contains the ReActAgent record and positive hits on all 80 added executable lines.

A separate focused contribution should replace the original multi-binary positional invocation with explicit object arguments, stop masking exporter failures, and verify actual source records before upload. Reuse this source/profile-bound red/green evidence and preserve .codecov.yml thresholds/exclusions. Add only the smallest rerunnable exporter/control needed. Handle build paths with spaces as arguments, validate missing profile/binaries, and preserve stdout/stderr/exit status. Recheck actual exported records after the final workflow command, with at least agent and DataFrame coverage when those tests run. This remains pending; the current agent PR does not fix hosted coverage.

Then continue the numerical example once classification PR #93's API is upstream; PCA #89 is already merged. No new generic preprocessing API is required. Keep MLX cold-start, MD5 policy and broader performance research separate.
