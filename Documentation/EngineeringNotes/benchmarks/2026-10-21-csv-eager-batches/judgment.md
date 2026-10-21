# Cross-judge verdict

## Scores

| Criterion | Design A | Design B |
|---|---:|---:|
| 1. Semantic compatibility | 3 | 3 |
| 2. Bounded metadata and ownership | 3 | 3 |
| 3. Concrete inner loops and work bounds | 3 | 2 |
| 4. Subtraction and call-chain depth | 3 | 3 |
| 5. Complete baseline measurement | 2 | 3 |
| **Total** | **14/15** | **14/15** |

## Evidence

Design A states the first-1,000 selected-row rule, independent candidate eligibility, fixed `Int64`, `Double`, `Bool`, `Date`, `String` order, all-null String result, immutable sample decisions, exact source replay, explicit failure-as-nil, and unchanged chunk-local streaming inference. It keeps one scoped record batch alive through joined column work. Reference-owned `ColumnAttempt` values make Array ownership clear and keep the enum switch outside the specialized cell loop. It also says current column concurrency should remain the starting policy.

Design B preserves the same public and inference contracts. Its `CSVFieldValue` cleanly distinguishes missing and invalid values. Concrete typed groups mutate sinks in place, which gives a credible answer to Array copy-on-write risk without reference owners. Failed columns share replay sweeps and successful columns move into ordinal output slots. The weak point is deliberate serial traversal of all groups. That removes established per-column parallelism before measurement, so it earns 2 on the execution criterion. Its measurement section is stronger than A's because it explicitly requires CPU, latency and RSS comparisons, Release specialization inspection, narrow and wide fixtures, and accounting for completed columns retained during replay.

## Recommendation

Use design A as the base. Its per-column worker model fits the existing concurrency boundary, states the candidate rules more completely, and gives each date parser one column-local owner. The reference owner is a small, contained cost for reliable Array mutation through an enum.

Graft two points from design B:

- Retain the first scoped data batch, derive the sample from its first `min(totalRowsToRead, 1000)` selected rows, and feed that same retained metadata into the first conversion wave before releasing it. Do not require a separate sample-only scan. If the first batch exceeds 1,000 rows, only the first 1,000 affect eligibility while the whole batch may enter conversion after decisions are fixed.
- Run one shared replay wave for all columns that failed on the same candidate stage. Frame each batch once, dispatch only unfinished workers, and retain completed output columns while measuring peak memory.

Strengthen A's verification plan with B's explicit baseline protocol. Compare complete eager CPU, elapsed time, peak RSS and held RSS against the immutable full-index reader. Validate native values independently and include late failures, since a smaller metadata index can hide extra replay CPU.

## Rejections

- Reject B's initial serial group traversal. Keep the existing per-column parallel dispatch until measurements justify a change.
- Reject making a separate 1,000-row sample pass mandatory in A. A retained first scoped batch can supply both eligibility and the first conversion input without changing semantics.
- Reject candidate promotion based on converted values. Fallback must consider every candidate admitted by the original sample, including `Bool`, and replay original bytes so String preserves lexical forms.
- Reject all-null inference from later rows. If the original sample has no non-null values, force String even when later rows are numeric.
- Reject per-column scans, retained whole-file token metadata, exact-row count prepasses, and type-erased per-cell dispatch. They either multiply framing work, restore input-proportional temporary storage, add unconditional work, or move runtime dispatch into the hot loop.

The synthesized direction is A's reference-owned workers and existing column parallelism, with B's retained-first-batch sampling, shared replay waves, invalid-versus-missing result type, and stronger measurement checklist.
