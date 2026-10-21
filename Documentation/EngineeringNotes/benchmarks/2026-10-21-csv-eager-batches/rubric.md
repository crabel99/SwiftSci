# Architecture scoring

Score each 0–3 with source evidence.

1. Preserves first1000 eligibility, exact source replay, null and override policies, public API and chunk-local streaming semantics.
2. Bounds field metadata and borrowed lifetimes without whole-file prepasses; keeps output ownership explicit.
3. Concrete inner loops, no per-cell dispatch, accumulated Array CoW copies or accidental O(rows×batches) work.
4. Deletes duplicate conversion loops, shares prepared parsing and keeps call chains short.
5. Can measure complete eager CPU, wall and peak/held memory against immutable full-index baseline, including late failures.
