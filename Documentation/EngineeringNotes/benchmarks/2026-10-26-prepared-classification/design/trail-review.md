# Decision-trail audit

## Result

The seven data rows in `decisions.tsv` are well-formed, chronological, and map to real design, review, qualification, and verification work. Every cited path resolves. The final source checkout is clean at `8926829bf2952a8f981a8be199be9ee9c3f7c458`. `production.patch` has SHA-256 `292b8429e6300e38ba3abbbfbeedd11783cb32ae59755f3f7a60d8dc537a4364` and exactly reproduces that commit.

The substantive verification claims check out:

- Native Debug and Release reports each contain 893 passed tests with zero failures and zero skips.
- Swift 6.3.3 evidence records successful Debug and Release builds, 77 XCTest passes, 740 Swift Testing passes, and compilation of all test targets. The combined 817-test count is therefore correct.
- The public WDBC workflow contains nine executions over 569 rows and 30 features at 0, 1, and 32 epochs. It checks 10,521 numerical fields, reports exact old/new results, exact labels and row positions, and a maximum NumPy difference of `1.1102230246251565e-15`.
- The standardized certificate and audit cover six cases on two engines, all passed, with the certified source commit and run hash matching the saved qualification record.
- The baseline proof binds the old probe result to the saved `logistic-old-binary.json`. That result confirms legacy NaN probability `[0, 1]` and the existing CPU/GPU first-step difference. The current tests correctly compare each prepared route with its same-route original oracle rather than asserting CPU/GPU equality. No evidence indicates a GPU algorithm change.
- DocC generation completed with the recorded pre-existing warnings. The standards and specification reviews contain no open implementation finding; the standards review's earlier concurrency P1 was resolved before the final runtime qualification.

The trail is materially truthful, but it is not yet a complete handoff record. The evidence-pointer gaps below make several claims harder to reconstruct than the underlying artifacts warrant.

## Attention

reviewed by GPT-5.6-sol (requested override; reviewer text self-identified as GPT-6)

- The `qualification` row cites only `baseline-probe-proof.json`. That file proves the result-file hash but does not contain the stated NaN and CPU/GPU values; those are in `verification/logistic-old-binary.json`. Same-route parity is proved by the native test reports. Add both pointers in a superseding row.
- The Swift 6.3.3 verification row cites the combined test log, which proves test-target compilation, 77 XCTest passes, and 740 Swift Testing passes, but not the Release build. The Release result is in `verification/swift633-release-build.log`; the Debug build has its own log as well. The claim is true, but its cited evidence is incomplete.
- `verification/public-workflow/summary.json` identifies the original source head, not the final candidate commit or tree, and predates the final commit. Other artifacts connect the candidate binary and source hashes, while `qualified-commit.json` associates the summary with the commit, but the trail does not cite that chain. Record the candidate binding or a summary hash in a superseding checkpoint.
- The trail has no final packaging checkpoint for the clean commit, exact `production.patch`, DocC result, or qualification receipt. Both `commit.json` and `qualified-commit.json` also leave `status` empty; `qualified-commit.json` omits the 77 XCTest count even though the log proves it. These are receipt-quality gaps, not test failures.
- The trail does not record the qualification boundary: no full local GitHub-workflow claim, no CodeQL pass, no new upstream PR, and Xcode 27 remains selected. Those limits appear elsewhere but should accompany the final qualification checkpoint so the verification rows are not read as broader CI coverage.
- The compatibility result is strong, but the explanation for the existing first-step CPU/GPU difference remains an inference. Preserve that distinction; the work proves unchanged route behavior, not the inferred mathematical cause.
- No active transcript path was exposed for this audit, so the self-audit used only the task artifacts and supplied task context. Cross-review was limited to the GPT model family; the requested GPT-5.6-sol reviewer returned text identifying itself as GPT-6, so neither cross-family independence nor exact reviewer identity can be established from the artifact record.
