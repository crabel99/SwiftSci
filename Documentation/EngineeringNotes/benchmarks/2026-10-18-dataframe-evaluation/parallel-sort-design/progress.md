# Sorting experiment phases

- [x] Ground the existing public sort path and ownership.
- [x] Compare two independent designs and judge the invariants.
- [x] Record the selected implementation plan and frozen evaluation rules.
- [ ] Implement both candidates from d23bf7cac9 without the gather change.
- [ ] Validate permutations and full materialized sorts.
- [ ] Measure paired operation costs and held-out cases.
- [ ] Preserve or reject candidates, with evidence on engineering-notes.

Architect checkpoints are autonomous. Source control preserves each candidate separately. No push or PR is requested. The experiment does not change schema, precision, stable tie order, null placement, output lifetime, existing NaN fallback, or public API.
