# Decoder selection rubric

1. Preserve exact CSV/String/Unicode/null semantics and current public APIs.
2. Select at the existing column/batch boundary; fallback rows avoid per-value strategy checks.
3. Use a real row-work estimate, not a token threshold fitted to one dataset, to bound preparation.
4. Keep ownership immutable and worker-local; no retained data cache or scheduling changes.
5. Remove unused byte-matcher preparation and keep the change small in the existing generic conversion design.
6. Define observable tests and matched CPU/memory controls near eligibility boundaries.

The configured gpt-5.6-sol runner is available. Other configured families are unavailable, so use the inherited model as the second runner. The cross-judge uses the available configured gpt-5.6-sol model. Two structurally distinct candidates remain required.
