# Completion reporting and cooperative agent cancellation

Source `0e1635199654ac6a20b32ea53eea0ffdfa39e747` adds two separately committed agent fixes on the qualified scientific integration `c4de6cc866fff6f52100535dbcb38dd708558200`. The first commit is `6ef1a4b35be11a611d8d101d1db2c56cd3c5a953`; the second fixes consumer cancellation. These are fork development results, not upstream delivery or maintainer approval.

## Resulting behavior

`CompletionReportingLLMModel` refines the existing `LLMModel` using the existing detailed generation stream. TransformerDecoder adopts it without changing generation. The native model adapter requires one final completion record, a `.stop` reason and normal stream termination before parsing a response or invoking a tool. Length limits, reported cancellation, malformed event ordering, missing metadata and producer errors fail the run. Accepted producer metadata is preserved on each agent step. Legacy text-only models remain compatible and have unknown completion status represented by nil metadata. The original four-argument AgentStep initializer remains available, including as a typed function reference. Both model and closure entry points use one ReAct loop.

The stream owns its producer task through termination cancellation. `run` throws on caller cancellation rather than returning an empty successful result. Checks around generation and tool boundaries stop late noncooperative generation results from starting another tool call or completing the answer. A tool's independent CancellationError retains ordinary tool-observation behavior. Cancellation remains cooperative: arbitrary external work cannot be forcefully interrupted, existing side effects cannot be rolled back, and cancelled `run` does not guarantee the producer has drained before returning.

No numerical production module, model-training algorithm, dependency, server, runtime, token-count policy or retry policy changed. The seven-file patch includes public API documentation and deterministic tests.

## Verification at the final source

- Native Debug and Release each pass 1,712 test definitions, with zero failures or skips. Parameterized invocations are counted separately by Xcode; 1,712 is the top-level test summary count.
- The local main workflow passes all nine steps, including both builds, safe tests, real coverage export, DocC, reporting regressions and documentation checks.
- The local benchmark workflow passes all 19 steps, including optional Polars/DuckDB checks, public worker challenges and three MLX CPU profiles. Of 404 policy executions, 400 meet strict conformance and four unchanged Python Wampler cases remain failed. The existing policy passes without changing tolerances or the failure inventory.
- Installed Swift 6.3.3 passes Debug/Release builds, compiles all test targets and passes the safe suite. Xcode 27 remains selected throughout; no toolchain rollback occurred.
- Python CodeQL completes with zero findings. Swift CodeQL completes on the matching installed Swift 6.3.3 compiler, with one retained pre-existing finding described below. This is not a clean security result.
- Standards and spec reviews report no open findings. `verify-qualification.py` verifies actual source, log and result hashes and the final counts.

Focused red evidence reproduces a truncated action that actually called a tool without raising an error. Nine new completion test definitions pass, covering rich stop/rejection paths and legacy compatibility. Seven cancellation test definitions reproduce 17 issues before the fix, then pass after it; the final complete agent suite passes 42 definitions. Handshakes and task-lifetime sentries establish ordering and producer quiescence for the assertions; five-second timers only guard against deadlock.

The missing-explicit-return compiler failure during development is retained in `cancellation-build-failure.log` and `agent-build-failure.log`. It was corrected before the green focused/full tests and final qualification.

## Swift security finding and execution limits

CodeQL 2.27.3 uses a Swift 6.3.3 extractor. The installed matching compiler supports local extraction while the selected Xcode 27 compiler is newer. The first compatibility attempt failed launching a sandboxed SwiftPM manifest with a bad CPU type. The second uses `swift build --disable-sandbox --arch arm64` and an unused conditional compilation flag, absent from tracked Swift sources, to force fresh extraction. Database creation and all 29 standard code-scanning queries complete. The database source archive contains byte-identical final agent/LLM source files.

The one result is `swift/weak-password-hashing` in `Sources/SwiftDatabase/DatabaseConnection.swift:606`. That file is byte-identical to the integration baseline. The helper implements the server-requested PostgreSQL MD5 authentication response; changing its digest would break that protocol. PostgreSQL documents the response and also deprecates this less secure method. The result remains recorded, unsuppressed. A separate authentication-policy follow-up should assess legacy MD5 support and SCRAM deployment; this run does not certify database security or test a live database.

Sources: [PostgreSQL 18 protocol](https://www.postgresql.org/docs/18/protocol-flow.html), [password authentication](https://www.postgresql.org/docs/18/auth-password.html). The inference that the flagged helper serves protocol compatibility is based on its sole auth-type-5 call site and these documents.

The extractor's manual `--version` probe initially wrote an untracked `extractor-out` diagnostic directory into the source working directory. Its version-only logs are preserved outside source. Tracked files remained unchanged; the worktree was temporarily dirty from this diagnostic output. `check-swift-codeql.py` is the exact successful captured controller. `check-swift-codeql-replay.py` moves the version probe into its requested output directory and uses a fresh build directory; that corrected replay script is syntax-checked, not a second claimed security execution. The failed first controller is also retained.

## Evidence and replay

`production.patch` records the complete source change. Red bindings tie the initial failing tests to their source parents and logs. Design alternatives and their cross-model comparison are under `design/`. The successful compatibility security receipt, SARIF, failure receipt and logs are under their named security directories. Native result bundles, build caches and the full CodeQL database remain local; their summaries, selected source archive hashes and log receipts are published.

Run `python3 verify-qualification.py` in the original local working directory to verify retained raw artifacts. Published records compress logs and comparison artifacts, redact the machine hostname and native hardware identifier, and retain authorized filesystem paths. Original/published digest maps distinguish those transformations. Run `python3 verify-publication.py --records PATH` on a downloaded record directory to verify its manifest and compressed payloads. These checks verify the recorded evidence, not a universal security, performance or numerical guarantee.
