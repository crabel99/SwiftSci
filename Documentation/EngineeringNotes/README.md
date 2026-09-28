# SwiftSci engineering working record

This record belongs to `crabel99/SwiftSci`, on branch `codex/engineering-notes`. crabel99 requested a continuing branch for documentation and discussion that will stay in our fork without an upstream PR.

Refer to the project owner as `crabel99` in documentation and discussion records.

The branch starts at upstream commit `fd68e6be058aa9fb10be1627a8b8841b9ee9a7e7`. PR #39 has merged. Production implementation and contribution work continue on their own branches.

## Start here

- [Dot-product implementation](benchmarks/2026-09-28-dot-implementation.md) records the per-operation policy, BLAS crossover, exact recovery, regression tests and integrated performance costs.

- [Dot-product qualification](benchmarks/2026-09-28-dot-qualification.md) identifies the SmLs ingestion fault, compares reduction accuracy and throughput, and records the range limits that block an unconditional replacement.

- [Precision reduction implementation](benchmarks/2026-09-28-precision-kernels.md) records the centered variance fix, ANOVA speedup, memory measurements and retained numerical failures.

- [Efficient precision on Apple silicon](benchmarks/2026-09-28-apple-precision.md) records crabel99's hardware-focused objective, native Swift FMA/SIMD evidence and the next implementation comparison.

- [Scientific precision practices](benchmarks/2026-09-28-precision-practices.md) compares representation, stable arithmetic and diagnostics, with a reproducible NIST input-conversion experiment.

- [PR 41 repair record](benchmarks/2026-09-27-pr41-repairs.md) explains the nine fault commits, complete validation, and retained acceptance limits.

- [Engineering charter](CHARTER.md) sets the objective and the criteria for planning, implementing and reviewing each step. Read it before proposing new work.
- [September 27 objective](discussions/2026-09-27-objective.md) records crabel99's adoption of this direction.

- [Kiraa reference status](benchmarks/2026-09-26-kiraa-reference-status.md) limits our experimental build to optional, independently validated implementation comparisons.

- [NIST univariate coverage](benchmarks/2026-09-26-nist-univariate.md) records the nine-dataset increment, fixed numerical policy, timing correction and final validation.

- [Benchmark contribution boundary](benchmarks/2026-09-26-standardized.md) retains the current benchmark decisions and local validation evidence.

- [September 26 discussion and decisions](discussions/2026-09-26.md) records our needs, contribution approach, compiler fix, coverage work and branch decision.
- [Decision record format](DECISION-RECORDS.md) describes what to retain when choosing an engineering approach.
- [Retained files](RETAINED-FILES.md) indexes 73 original notes and supporting artifacts captured from the existing SwiftSci research and this chat's verification work.
- [PR #39 snapshot](archive/2026-09-26/pr39.json) preserves the description, public discussion and check results observed when this record was created.
- [Draft reply to the maintainer](drafts/maintainer-reply.md) preserves the proposed response from this chat. It has not been posted by this chat.

## Keeping the record

Commit new discussion summaries, research findings, alternatives and evidence to this branch. Date each entry and identify the relevant source revision. Mark proposals, measured results, source observations and unresolved questions separately. Record why a decision changed instead of rewriting an old experiment as if it had reached the new conclusion.

The archived source notes are unchanged originals. Their wording, local paths and historical claims remain as recorded. The index and manifest identify retained copies. New summaries and decisions should use plain language and the unslop self-audit.

The initial collection includes the retained Markdown notes under the local SwiftSci research directory, three uncommitted workspace proposals, the storage research's small supporting artifacts, and the compiler verification snippets. Build caches, binaries, generated datasets and a duplicate source checkout are excluded. Large raw outputs remain in their existing locations or committed benchmark evidence. This is not an export of other chats or every local run artifact.

## Relationship to upstream contributions

Keep this branch on our fork. Push its commits to `origin/codex/engineering-notes`; do not open an upstream PR from it. The fork is public, so this branch is public too.

Start implementation branches from the appropriate upstream revision or agreed dependency branch. Keep our internal research, engineering decisions, discussion summaries and local reports on this branch. Contribution branches may contain implementation, tests, fixture attribution and public usage instructions. Do not copy internal records into a PR; summarize the relevant verified facts for reviewers. Avoid merging this archive branch into them. Upstream remains the owner of its API and architectural decisions; our working proposals do not imply maintainer approval.

Bring upstream changes into this branch when useful, preserving the dated records. A newer codebase does not retroactively validate an older result.

## How we explain a contribution

Explain the observed problem, the alternatives, the chosen tradeoff, the behavior that must remain correct, and the evidence supporting the choice. State limitations and the conditions that would justify revisiting it. Invite the maintainer to challenge assumptions.

The PR should contain enough reasoning to review the change. Lasting design decisions belong in maintained documentation. Code comments should explain constraints that a future maintainer cannot readily infer from the code.
