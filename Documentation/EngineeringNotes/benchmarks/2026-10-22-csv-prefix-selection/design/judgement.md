# Architecture judgment

## Recommendation

Use the separate concrete decoder as the base. It keeps the current scalar decoder protocol, attempt type, builder flow, and generic row loops. The only new dispatch is one private conversion-enum case chosen when the attempt is created. That is the smallest design that keeps fallback rows free of strategy checks.

Graft two points from the unified candidate into that base:

1. Rename the internal factory argument from `capacity` to `selectedRowCount`, then pass that value unchanged to the builder reserve. The count already has this exact meaning at every grounded caller. Once decoder selection also consumes it, the allocation-oriented name hides a second semantic role.
2. Document preparation as a bounded-work policy and test the boundary at one below, exactly at, and one above the budget. Keep the document explicit that this bound does not identify the CPU-optimal crossover.

Do not graft the unified batch protocol split or its mode-owning String decoder. Removing one enum case does not repay a change to the decoder contract and append path for every converted type.

## Scores

Scores use 0 for unmet, 1 for partial, and 2 for met.

| Criterion | Separate | Unified | Judgment |
| --- | ---: | ---: | --- |
| 1. Preserve CSV, String, Unicode, null semantics and public APIs | 2 | 2 | Both parse through the existing String path and use canonical `Set<String>` equality for possible matches, empty values, and non-ASCII-leading values. Both leave public read options unchanged. |
| 2. Select at the existing column or batch boundary and avoid per-value strategy checks on fallback rows | 2 | 2 | Separate selects once per attempt through the existing conversion enum. Unified switches mode once per appended batch, outside the cell loop. Neither puts a strategy test in hashed fallback rows. |
| 3. Bound preparation with a real row-work estimate | 2 | 2 | Separate gates token visits by row count and token-byte visits by the same row count. Unified charges token visits and bytes against one combined row-count budget. Both handle long tokens and avoid a dataset-fitted token threshold. |
| 4. Keep ownership immutable and worker-local | 2 | 2 | Both publish only immutable prepared state owned by an attempt. Neither adds a retained cache, cursor state, or scheduling change. Failed preparation publishes no partial masks. |
| 5. Remove unused matcher preparation and keep the change small in the existing generic design | 2 | 0 | Both move `CSVNullMatcher` creation into the numeric and date cases that consume it. Separate otherwise extends the existing generic design. Unified replaces the decoder protocol contract, moves row loops, changes all scalar conformances, and changes attempt dispatch to remove one String enum case. That is too broad for this optimization. |
| 6. Define observable tests and matched CPU and memory controls near eligibility boundaries | 1 | 1 | Both name semantic boundary cases and a cleanup-only performance comparison. Neither design specifies a complete matched CPU and peak-memory matrix with fixed input bytes, selected rows, token contents, reader mode, build mode, and repeated-run method. `resource checks` is too vague for full credit. |
| **Total** | **11/12** | **9/12** | **Separate wins.** |

## Minimality findings

### Mask storage

The separate sketch's `CSVASCIILeadingByteSet` is a private one-consumer wrapper around two `UInt64` values. Its invariant is already established by the failable prefix-decoder initializer. Store `lowStarts` and `highStarts` as two private fields on `CSVASCIIPrefixStringDecoder` and use one private inline membership method there. This removes a type without weakening ownership or validation.

The unified `CSVASCIINullPrefixes` does more than wrap masks because it owns preparation and the negative-prefix query. That makes the type defensible in isolation. It still does not justify adopting the broader unified decoder hierarchy. In the selected base, the failable decoder initializer already provides the same boundary.

### Factory argument

The unified name `selectedRowCount` is better than the separate candidate's retained `capacity`. The grounded trace establishes that the argument is the exact selected row workload for a full eager attempt, an indexed chunk, or a one-row retry probe. Builder reservation is one use of that count. Prefix eligibility is now another. Rename this internal argument and keep the public API unchanged.

### Preparation budget

A count-only rule is insufficient because a small number of long tokens can perform unbounded byte work. Both candidates correctly reject that rule.

The separate candidate uses two simple ceilings: at most `selectedRowCount` token visits and at most `selectedRowCount` byte visits. Its total preparation is therefore bounded by a small constant multiple of row work. The unified candidate uses a stricter combined token-plus-byte budget. That is a coherent policy, but it charges token iteration separately from bytes and rejects some workloads that the separate policy admits. The designs contain no measurements showing that this stricter cutoff is closer to the profitable crossover.

Use the separate two-ceiling policy for the initial implementation because it is simpler and still proves bounded setup. Record both token visits and bytes in benchmark cases so later measurements can replace it with a combined or weighted rule if that rule wins.

## Bounded work versus crossover

The row-derived budget proves only that preparation cannot grow independently of the attempt's selected rows. It does not prove that prefix preparation is faster than hashed lookup for an eligible attempt. Row visits, token visits, UTF-8 byte visits, String parsing, hashing, and successful-prefix rates have different CPU costs. The fraction of values rejected by the prefix mask also changes the payoff.

No design result here establishes the CPU-optimal crossover. Promotion needs matched measurements around the eligibility boundary, including cleanup-only hashed lookup, count-gated byte-bounded preparation, and the combined token-plus-byte alternative. Those runs should hold source bytes, row count, null-token set, eager versus streaming mode, build configuration, and measurement procedure constant, and should report both CPU time and peak memory. Until then, the selection rule is a conservative complexity bound.

## Concrete grafts into the separate base

- Rename `conversion(type:capacity:)` and its private String helper to use `selectedRowCount`, updating the grounded internal callers and continuing to pass the same value to `CSVColumnBuilder` reservation.
- Keep the existing scalar `CSVValueDecoder` contract and generic attempt row loops.
- Add the prefix decoder as one concrete conversion case selected once per attempt.
- Store the two masks directly on that decoder unless implementation reveals a second owner that needs the mask abstraction.
- Move `CSVNullMatcher` construction into the integer, floating-point, and date branches before adding prefix preparation.
- Add semantic tests for empty tokens, possible prefix matches, ASCII misses, non-ASCII values, non-ASCII token fallback, saturated masks, retry probes, and short final chunks.
- Add exact budget tests and a matched CPU and peak-memory comparison near each eligibility boundary. Report results before changing the conservative rule or claiming a crossover.
