# Specification review

Reviewed `git diff c906c3fbbb0baf1357438a7079921a6448e0c9e5...HEAD`, including commits `f9a99ce54c` and `167d9a4e6f`, against `synthesis.md`, `chosen-sketch.swift`, and `how.md`.

No actionable specification findings.

The requirement to "Add one CSVColumnConversion case; do not add whole-batch decoder protocols or a stored closure" is met. Selection occurs once in the UTF-8 factory. The decoder remains immutable within an attempt, and the existing scalar loops and hashed fallback are unchanged.

The requirement to "Precharge each token visit by subtracting tokenCount from selectedRowCount, then decrement the remaining budget for each UTF-8 byte in one pass" is implemented. Empty and tiny sets, insufficient row budgets, non-ASCII tokens, and saturated masks all reject preparation. Exact-budget completion succeeds. Failed preparation publishes no decoder.

The eager reader supplies its selected total for initial attempts and retries. Indexed streaming supplies the actual chunk row count; retry probes supply one. Renaming `Initial.capacity` to `totalRows` and the factory argument to `selectedRowCount` matches the agreed ownership boundary.

The decoder parses each field once. Only impossible ASCII starts skip membership lookup; empty values and non-ASCII starts retain native `Set<String>` equality. Kelvin-sign coverage checks a non-ASCII spelling canonically equal to ASCII `K`. Invalid UTF-8, escaping, whitespace, owned token values, saturated masks, and eager/streamed selection boundaries have focused tests. No public API or unrelated behavior changed.

The specification also says "Before keeping the combined change, run Release, Debug, Address Sanitizer, grammar parity, actual-source-path reference and control timings, Unicode scalar validation, and the standard production-default benchmark audit." That acceptance gate is still a qualification responsibility. This read-only review did not run builds or tests and does not claim the gate has passed.
