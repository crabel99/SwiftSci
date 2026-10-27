# Initial evidence audit

Reviewed the current-turn transcript through the 20:33:16 checkpoint, four decision rows, specification, plan, initial receipts and their controller, source reconciliation, and active qualification controllers. Source under review is `c676a0acfca0274fe05e2dc72bf7a0b45ab9f5c9` on `200d3935cc43396658a315bf4d5f745b6c7b496c`.

The initial success claims have supporting evidence. All 23 control-log hashes and all recorded exported-output hashes match the files. The control controller matches its recorded hash. All six initial source hashes match the frozen-source reconciliation. The five altered-output controls fail with the expected assertion diagnostics. Rows 3 and 4 correctly describe these as prototype checks, and row 5 correctly says final qualification is running. Unfinished jobs are not skipped checks.

## Attention

reviewed by gpt-6-astra

- Qualification has different scopes that the decision trail does not yet explain. `decisions.tsv:5` says complete applicable CI, while `check-swift633.py:9` excludes eight named suites, including SwiftML, SwiftCluster and SwiftPreprocessing. Its scope text correctly promises compilation and safe tests, with example execution recorded separately. `check-swift-codeql-replay.py:13,28` uses Swift 6.3.3 and a conditional compilation flag, while `launch-ci.py` selects Swift 6.4 for the main jobs. Preserve these distinctions in the completed qualification summary, with separate final-source example-execution receipts. This is a disclosure and pending-evidence issue, not evidence that the current jobs were skipped or that source behavior failed.

- Local workflow replay does not execute hosted action steps. `full-ci-runner.py:165` skips steps without a `run` body. Its explicit local CodeQL invocations provide a separate analysis path, but cannot prove hosted upload or service behavior. Keep the existing PR97 coverage/export qualification separate as `spec.md` requires. A final statement that all hosted CI passed would exceed this evidence.

- The starting decision has a weak evidence pointer. `decisions.tsv:2` cites "existing numerical-template source and verifier" without a path or receipt. The transcript's 20:04:35 and 20:05:12 calls identify the actual template under `/private/tmp/swiftsci-mlprogram-20261026/notes/Documentation/EngineeringNotes/benchmarks/2026-10-26-numerical-template/`. Append a row resolving the prior qualification receipt if that prior qualification remains part of the justification. The current example checks stand on their own, but a reader cannot audit the earlier qualification from the log alone.

No source correctness finding is claimed by this evidence-only audit. Review of finished receipts and the frozen publication package remains pending.
