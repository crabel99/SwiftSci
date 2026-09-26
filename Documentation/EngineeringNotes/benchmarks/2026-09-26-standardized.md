# Standardized benchmarks: contribution boundary

The implementation belongs on `codex/standardized-benchmarks`, based on upstream main `fd68e6be05`. Our architecture discussion, roadmap, local validation narrative and captured run evidence belong only on `codex/engineering-notes` in our fork.

The first local implementation commit included these internal records. They were copied here byte-for-byte before removal from that unpublished commit. Keep the records for development; do not merge or cherry-pick this notes branch into a contribution branch.

- [Architecture and future coverage](../archive/2026-09-26-standardized-benchmarks/workspace/Benchmarks/ARCHITECTURE.md)
- [Local validation report](../archive/2026-09-26-standardized-benchmarks/workspace/Benchmarks/Results/StandardizedValidation/README.md)
- [Preservation checksums](../archive/2026-09-26-standardized-benchmarks/manifest.json)

The archived files retain their original paths and wording. References to the old contribution-branch locations are historical. The measured implementation fingerprint remains `40e7b07ce9ab9027f5f0179e0c3d0e1128560064efca4792a258eee60fd9593a`; relocating these notes does not change code or invalidate those runs.

Keep public usage instructions, fixture attribution, implementation and regression tests on the contribution branch. Internal research, discussion summaries, decision records and development reports must stay here. Review both the PR diff and its commit history, since deleting a file in a later commit does not remove it from earlier commits.

A local pre-push hook checks outgoing commit history for internal paths. It permits this notes branch only at `origin/codex/engineering-notes` on our fork. Its maintained copy is [guardrails/pre-push.py](../guardrails/pre-push.py). Hooks do not prevent someone from creating a PR directly on GitHub; do not open a PR from the notes branch.

The guard treats new files under `Benchmarks/Results/` as internal evidence, with an exception for its public README. Existing upstream evidence is outside the outgoing commit range. The compact-storage branch still contains APIConsolidation and CompactIntegration development reports, including `decisions.tsv`; the guard blocks that branch until those records are separated. Its implementation history has not been rewritten during this cleanup.
