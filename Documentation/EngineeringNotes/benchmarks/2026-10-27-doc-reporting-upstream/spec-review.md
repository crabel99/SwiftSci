No spec findings.

Reviewed `git diff e19db7dda4567c425b7eb002da82e234e6c7980f...84aa7c59e80d8282c7daf0ce8e9dfc4871308b60` against `spec.md`.

- Spec line 5 requires "Report the actual documented/matched public-open declaration ratio" and "Label the output as a heuristic declaration scan." The existing counters supply the printed measured ratio. The unconditional 100% success assertion is removed; the output explicitly distinguishes the heuristic from DocC symbol-graph coverage. With no matched declarations, the branch reports N/A. The declaration regular expression, comment walk and matched-file traversal remain unchanged, including their existing limitations.
- Line 5 requires "Preserve ... unresolved Xcode-placeholder failure with exit1" and "Missing comments remain reporting-only with exit0" without a new threshold. Placeholder detection, failure text and exit1 are unchanged. The no-placeholder branch still exits0 regardless of missing comments. No numeric acceptance threshold was added or relaxed.
- Line 5 requires "the five existing documented/undocumented/mixed/empty/placeholder regressions" in the "actual main workflow" and a renamed misleading step. The real DocC job now runs unittest discovery over scripts/tests before running the checker. Its step names accurately describe reporting and placeholder enforcement. Fixtures cover 100%, 0%, 50%, no-matched-declaration N/A and placeholder exit1, with partial/empty cases forbidden from printing 100%.
- Spec line 3 requires an isolated three-file correction, independent of PR89/90/91. The only changed paths are the checker, its regression suite and ci.yml; all three match the existing c4de6cc866 correction byte-for-byte. No Swift source, package, numerical-policy or Codecov file changes appear.

The red receipt fingerprints match the actual upstream checker/workflow and report five tests with four failures and one pass. Its scan exits0 while printing 98.66%, 2431/2464, followed by the false 100% claim. Green records report five passing tests and the identical measured ratio with truthful wording. This demonstrates reporting correction without changing declaration inventory.

Read-only review. I ran no source action, build, test or remote operation. Full local CI, compatibility, security and submission status remain separate execution requirements; this review does not declare them complete.
