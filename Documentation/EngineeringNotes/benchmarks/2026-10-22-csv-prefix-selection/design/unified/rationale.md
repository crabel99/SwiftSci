## Usage

The CSV reader still creates one conversion attempt and appends record batches. The caller supplies the exact selected row count, which also reserves the output array. No public read option changes.

```swift
// Eager reader, including retry attempts. This count spans all selected batches.
let conversion = plan.conversion(type: candidate, selectedRowCount: initial.capacity)
conversion.appendIndexed(buffer: bytes, records: records,
    startRow: 0, rowCount: rows, column: column)

// Indexed conversion, including a streaming chunk's short final batch.
let conversion = plan.conversion(type: candidate, selectedRowCount: dataRowsToRead)
conversion.appendIndexed(buffer: bytes, records: records,
    startRow: startRow, rowCount: dataRowsToRead, column: column)

// The rejected-token probe is a separate one-row workload.
let probe = plan.conversion(type: laterCandidate, selectedRowCount: 1)
```

The three counts come from the grounded reader trace. Rename the internal factory argument instead of making allocation capacity silently acquire selection semantics.

## Problem

The measured prefix filter avoids useful String hashing work, but scanning a large token set for a tiny read wastes CPU. The existing factory also builds a `CSVNullMatcher` that String and Boolean conversion never consume. The existing generic row loop invokes a decoder per cell, so merely storing a mode inside `CSVStringDecoder` would move the selection branch into every row. This candidate keeps one String conversion case and chooses its stored mode once per append batch.

## Shape

First move `CSVNullMatcher` construction into Integer, Double, and Date factory cases. Preserve the original hashed and one-or-two-token algorithms as concrete cell decoders. Remove `stringWithSmallNullSet` from `CSVColumnConversion`; one `.string` attempt now owns `CSVStringDecoder`, whose immutable mode contains a hashed, tiny-set, or prefix decoder. No global state or cross-attempt cache appears, per subtract-before-you-add.

Make whole-batch decoding the requirement of `CSVValueDecoder`. Move the existing scalar requirements to `CSVCellDecoder`, which supplies the current generic validating and optional-value loops as its default batch implementation. The numeric, Boolean, Date, hashed String, tiny String, and prefix String decoders satisfy this narrower scalar protocol. The unified String decoder implements only the batch requirement. This avoids a required but unused scalar mode switch, per minimize-reader-load.

The hot call chain is explicit. `appendIndexed` selects a concrete record view. `CSVColumnConversion.append<Records>` selects `.string` and calls `CSVColumnAttempt<CSVStringDecoder>.append`. That method swaps out its local builder and makes one generic protocol requirement call to `decoder.appendRows<Records>`. The unified implementation switches on its stored mode once, then calls a generic scalar row helper with a concrete decoder. Inside the hashed loop, the original `CSVStringDecoder` algorithm parses text and calls `Set<String>.contains`; there is no mode test or stored closure. The tiny loop retains its two equality checks. The prefix loop alone tests its masks. Generic numeric attempts reach the default batch implementation and retain their validation contract. The existing Double-specific validating loop stays intact.

A generic protocol requirement may remain a witness call at the batch boundary. The inner scalar loop is generic over its concrete decoder, so specialization can produce direct per-cell calls, just as the current generic loop does. The design adds no per-cell existential or closure call. Inspect generated code before claiming the compiler removed generic witnesses; a type sketch cannot establish that result.

Preparation uses a work ceiling rather than a token-count cutoff. Empty sets use the original hashed decoder, and sets of one or two use the existing tiny decoder. For larger sets, reject preparation immediately when `tokenCount > selectedRowCount`. Otherwise spend a budget of `selectedRowCount` work units, charging one for each token visit and one for each UTF-8 byte inspected. Choose hashed lookup when the next charge would exceed the budget or any non-ASCII byte appears. Finishing with exactly zero budget succeeds. Successful preparation proves that its token-plus-byte traversal costs no more work units than the selected workload has row visits. This bounds setup even for a single huge token and avoids multiplying counts that could overflow. It deliberately does not claim that one byte visit and one row visit have equal CPU cost, or that the filter will reject enough rows to repay setup. The one-for-one budget is an explicit conservative complexity policy, not an empirically established break-even rule. Measurements must judge it against cleanup alone before promotion.

Masks cover the first byte of every ASCII token. If both masks become `.max`, choose hashed mode because no leading ASCII byte can be excluded. This decision occurs before publishing a prepared decoder. Filtering occurs only after the existing String parse. Empty values, non-ASCII-leading values, and possible prefix matches use the original canonical String equality through `Set.contains`. The filter proves only negative membership. A failed preparation retains the original set and never publishes partial masks. No normalization, scheduling, lifetime, or public API changes.

All new ownership stays in `CSVColumnConversion.swift`. The existing record-access types, builders, readers, and parser keep their responsibilities. The external conversion interface is unchanged apart from an internal argument rename, and callers never coordinate preparation stages, per boundary-discipline. This is a deeper String implementation behind a smaller conversion enum, but a broader decoder protocol change than the concrete-decoder alternative.

## Synthesis decision

Pending parent synthesis. This candidate demonstrates a coherent unified design. I favor the separate concrete-decoder alternative for this measured optimization unless removing String variants from the conversion enum is itself a project requirement. One additional enum case is less churn than changing the decoder contract used by every type.

## Tradeoffs accepted

- We accept a batch decoder requirement and a scalar subprotocol in exchange for one String conversion case and no per-cell mode switch.
- We accept retaining three concrete cell algorithms behind the unified owner in exchange for static inner-loop decoder types. Stored modes alone cannot remove these concrete algorithms.
- We accept losing possible gains on workloads that fail the work ceiling in exchange for bounded setup without a test-specific threshold.
- We accept a policy that bounds preparation work but cannot predict token hit rate in exchange for avoiding sampling, caches, and another parse pass.

## Alternatives considered

- A new prefix case in `CSVColumnConversion` uses the existing generic attempt unchanged. It hides selection equally well from reader callers, keeps current scalar protocols, and requires fewer edits. It is the stronger default for this narrow change.
- A per-cell enum switch inside the current String decoder has a smaller implementation diff but exposes every hashed fallback row to feature selection. It does not meet the dispatch goal.
- A stored lookup closure moves branching to construction but introduces an indirect call in every cell. It hides the same policy behind no smaller reader interface and weakens the hot-loop contract.
- A String-specific `appendString` overload mirrors `appendDouble`, but leaves either unused scalar mode dispatch or a second String ownership path. The bulk protocol states the actual capability more clearly when unification is required.

## Open questions and risks

- Does generated optimized Swift retain direct concrete decoder calls inside all three record-view row loops after the batch protocol change?
- Do neighboring row and token-byte workloads show enough prefix benefit to justify the one-for-one work ceiling over cleanup alone?
- Is avoiding one String enum case worth changing the batch contract for Integer, Double, Boolean, and Date decoders?

## Next implementation step

After synthesis, prototype the chosen dispatch, verify token-count and combined token-plus-byte budget boundaries at minus one, exact, and plus one selected rows, verify saturated masks choose hashed mode and late non-ASCII tokens discard partial masks, then compare cleanup-only and selected-prefix paths using the existing native-output and resource checks.
