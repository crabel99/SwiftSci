# Sorting experiment phases

- [x] Ground the existing public sort path and ownership.
- [x] Compare two independent designs and judge the invariants.
- [x] Record the selected implementation plan and frozen evaluation rules.
- [x] Implement both candidates from d23bf7cac9 without the gather change.
- [x] Validate permutations and full materialized sorts.
- [x] Measure paired operation costs and held-out cases.
- [x] Preserve or reject candidates, with evidence on engineering-notes.

Architect checkpoints are autonomous. Source control preserves each candidate separately. No push or PR is requested. The experiment does not change schema, precision, stable tie order, null placement, output lifetime, existing NaN fallback, or public API.

Radix passes registered operation qualification and 15 integration conformance controls. Its mixed narrow case remains variable. The current merge dispatcher fails protected-loss limits. Both source branches remain local; combined application timing and any production policy decision require a new plan.
