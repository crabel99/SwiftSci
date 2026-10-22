# Separate ASCII-prefix String decoder

## Problem

String columns currently choose between direct equality for one or two null tokens and hashed `Set<String>` membership for every other set. Measurements show that hashed membership costs enough to matter on bulk String work, while preparing a prefix screen costs too much when a column has few rows and many tokens. Preparation scans token bytes, so token count alone does not bound setup for long tokens. The design must preserve eager retry, streamed chunk behavior, existing public APIs, and the original decoders. It must also remove the unused `CSVNullMatcher` construction that String and Boolean conversion never consumes. The existing `capacity` argument is the exact selected row count for a full eager attempt or one streamed chunk, and one for a retry probe. That makes it the available work budget for decoder selection.

## Usage (caller's view)

Readers keep calling the existing plan method. They do not select a String strategy.

```swift
// Full eager attempt. selectedRowCount includes every selected data row.
let conversion = plan.conversion(type: .utf8, capacity: selectedRowCount)

// Streamed chunk. records.count is the exact row count in this chunk.
let conversion = plan.conversion(type: .utf8, capacity: records.count)

// Candidate probe after rejection. A capacity of one prevents prefix preparation.
let probe = plan.conversion(type: candidate, capacity: 1)
```

All three call sites receive the same `CSVColumnConversion` abstraction and append through its existing methods. Selection remains inside `CSVColumnPlan.conversion`. Empty token sets use `CSVStringDecoder`; one or two tokens use `CSVSmallStringDecoder`; larger eligible ASCII sets use `CSVASCIIPrefixStringDecoder`; every other set uses `CSVStringDecoder`.

## Shape

The change stays in `CSVColumnConversion.swift`. `CSVColumnPlan` already owns immutable null tokens and creates attempts, so it also owns the one-time decoder choice. `CSVColumnConversion` gains one concrete enum case for `CSVColumnAttempt<CSVASCIIPrefixStringDecoder>`. Its existing `append`, rejection, and column extraction switches dispatch that case. There is no public type, scheduler change, cache, or state shared between attempts.

Selection uses this order:

1. Empty set: original hashed decoder.
2. One or two tokens: original equality decoder.
3. More tokens than rows in this attempt: original hashed decoder without scanning tokens for ASCII.
4. No more tokens than rows: ask the failable prefix decoder initializer to scan the tokens once with a byte budget equal to the row count.
5. Exhausted byte budget or a non-ASCII token: original hashed decoder.
6. Completed scan whose two masks are both saturated: original hashed decoder because the screen cannot reject a leading ASCII byte.
7. Completed useful scan: prefix decoder with its prepared leading-byte mask.

The cheap `nullValues.count <= capacity` gate bounds token iterations. The initializer then decrements a byte budget from `capacity` as it visits each token's UTF-8 bytes. It returns nil as soon as the next byte would exceed the budget or a byte is non-ASCII. It does not compute `utf8.count` first or allocate a byte array. Together these checks bound visited token iterations and bytes by the value work available to benefit from preparation. This is a conservative policy, not a claim about the exact CPU crossover. The checks use the existing exact row budget, so an eager retry recreates the right decoder for its full replay and every streamed chunk makes an independent choice for its own rows.

`CSVASCIIPrefixStringDecoder` owns a fully ASCII token set and its prepared leading-byte mask. Its initializer is the boundary that validates the ASCII invariant and enforces the byte budget in one pass. Partial mask work is discarded if initialization fails. It also returns nil when both 64-bit masks equal `.max`, since that screen cannot reject any leading ASCII byte. Its row method parses the String, rejects an ASCII leading byte absent from the mask, and otherwise delegates to `Set` equality. A value with a non-ASCII leading byte always reaches `Set` equality. Empty values also reach equality because the token set may contain the empty String. No per-row flag selects between prefix and fallback strategies because fallback is a separate enum case and concrete decoder.

`CSVNullMatcher` construction moves into the integer, floating-point, and date cases that retain it. Boolean and both String paths do not construct it. This subtraction precedes the new decoder and leaves one owner for each prepared representation.

The interface remains deep enough for the change: callers provide the type and existing row budget, while `CSVColumnPlan` hides token-count gating, byte-budget enforcement, ASCII validation, mask preparation, and fallback. Adding a policy option would expose internal cost choices and weaken that boundary. Validation happens once in the failable decoder initializer, and decoding trusts the resulting concrete type, per boundary discipline.

## Synthesis decision

Arena fills this section after comparing candidates.

## Tradeoffs accepted

- We accept row count as both the token-iteration and token-byte budget in exchange for a simple upper bound on wasted preparation.
- We accept rebuilding the prefix decoder for each streamed chunk in exchange for preserving the cursor's current stateless chunk boundary.
- We accept `Set` equality for possible prefix matches and all non-ASCII values in exchange for preserving Swift String equality semantics.
- We accept one additional internal enum case in exchange for removing a per-row strategy branch from the fallback decoder.
- We accept falling back when both masks saturate in exchange for avoiding a prepared decoder that cannot reject any ASCII prefix.

## Alternatives considered

An unconditional prefix screen lost because it scans every token even for tiny attempts. The setup controls show this work can dominate, and callers have no way to amortize it.

A count-only `nullValues.count <= capacity` gate lost because a few long tokens can require far more setup work than their count suggests. It has a cheaper eligibility check, but it does not bound the token bytes visited. The chosen single scan retains that count guard and adds a conservative byte limit without a separate length pass.

A strategy flag inside `CSVStringDecoder` lost because every row would inspect policy selected at construction time. It hides less behind the enum's existing one-time dispatch and makes fallback pay for the feature.

A cached prepared decoder across eager retries or streamed chunks lost because it adds lifetime and coordination rules. Existing attempts already have the exact work budget, and retries and chunks deliberately construct fresh attempts.

## Open questions and risks

- At what nearby row, token-count, and token-byte counts does the prefix decoder first beat cleanup-only hashed membership in fresh eager and streamed reads?
- Does a byte budget equal to row count remain beneficial around the eligibility boundary, or should a later measured rule require more rows per token byte?
- How does the byte-budget policy compare with count-only selection for short tokens and long tokens at the same token count?
- Do boundary tests cover a token scan using exactly the byte budget, exceeding it by one byte, and failing before reading a byte when the budget is zero?
- Do mask tests cover one unsaturated mask, one saturated mask, and both masks saturated, with the last case selecting the hashed decoder?
- Do tests cover empty tokens, leading ASCII mismatches, possible prefix matches, non-ASCII values with ASCII token sets, and non-ASCII token-set fallback under both eager retry and short final chunks?
- Does Release, Debug, and sanitizer qualification preserve output and keep the new enum dispatch from changing the existing one-token and two-token paths?

## Next implementation step

Implement the cleanup and concrete decoder selection in `CSVColumnConversion.swift`, then measure the neighboring row-count and token-count crossover cases before changing the conservative eligibility rule.
