# Qualification and publication controller audit

reviewed by gpt-6-astra

Inspected verify-qualification.py, package-records.py, verify-publication.py and their supporting controllers. I did not run qualification. Release, compatibility, benchmarks and Swift security are still incomplete at this checkpoint.

The qualification controller binds the clean source checkout to the intended single commit and three changed files. It checks current source fingerprints, workflow and controller hashes, step-log hashes, actual native result-bundle summaries and Agent/NLP test nodes, benchmark worker identity, and CodeQL's extracted source bytes. It separately checks positive coverage counts in the actual workflow LCOV. These checks support the intended claims without substituting fixture success for full package execution. The main workflow's nine log hashes currently match its passed receipt.

The independent predecessor controller copies the exact final regression file and untouched upstream workflow into a fresh minimal repository. Its receipt records eight tests and eight failures, matching the retained log. This is a useful reproducible replacement for relying solely on the earlier temporary workflow swap.

The publication controller has an explicit allowlist and excludes the raw scoped transcript, process inventory, account telemetry, caches, executable binaries, native result bundles and security database. It records original and transformed hashes, compression identities, archive-member identities and retained failed attempts. The publication verifier checks these published-byte identities and rejects unexpected ordinary files. It validates bundle integrity; it does not itself rerun qualification or prove that all private values have been removed. Inspect the actual generated package before publishing, including decompressed logs and nested archive members.

The updated decision trail now includes the stopped historical lookup, known-path substitution, final source commit, running qualification, benchmark controller correction, independent reviews and completed main workflow. coverage-followup.md now resolves locally. These address the initial trail gaps at the current stage.

## Attention

reviewed by gpt-6-astra

- Tighten the native total predicate in verify-qualification.py. It currently accepts any equal Debug/Release count at least 1673, while the current full Debug receipt establishes 1713 definitions. Both configurations could omit up to 40 tests and still pass this predicate. Use the known expected 1713 count or verify the complete expected identity set. This is a controller check, not a production-source defect.
- Full qualification remains pending. No final qualification or publication package exists for this audit to approve. Recheck actual completed Release, compatibility, benchmark and Swift-security results, then inspect the final publication bytes.
- Publication verification proves recorded-byte consistency. Preserve the separate privacy inspection and the explicit limits on hosted Codecov acceptance, the four known pandas failures, unchanged MD5 finding and MLX cold-start behavior.
