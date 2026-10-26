# CSV standards review

Reviewed `git diff 962fd9ff4d155e5116baf6f177abfa3e84fd8754...da03a63015`, five commits, against `CONTRIBUTING.md` and the Fowler smell baseline. No builds or tests run for this review.

No actionable documented-standard breaches or design-smell findings in this diff.

- The changes remain within the dataframe CSV implementation and its tests, consistent with the contribution rule to keep target responsibilities separate. They introduce no public API requiring additional DocC comments.
- `CSVColumnConversion.swift` extracts the repeated integer/Double fallback into one private function. Its generic parameter supports the two existing numeric decoders. It does not add speculative dispatch or a public abstraction.
- `CSVColumnBuilder.swift` keeps pending validity-word state with the builder that owns append and finalization. The new fields describe one buffering operation and need not become another type.
- `SystemsCSVParser.swift` changes mask representation inside the private structural scanner. Both SIMD and scalar tail paths use the same nibble position convention, with comments explaining the representation.
- The integer-boundary and empty-field tests exercise the public CSV reader as well as internal parsing boundaries. Numeric fixtures use explicit types and small expressions, following the repository's test-type-checking guidance.

Compiler checks, runtime correctness, performance evidence, and numerical parity remain separate verification responsibilities. This standards pass does not certify them.
