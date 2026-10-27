## Standards

No actionable findings in `git diff 01d48cbcd940c886546b2bb8d6b177d9b7a0e277...3012a6e52d70306a9437fb8cd8af4343a41560dd`.

Reviewed CONTRIBUTING.md, the required subtract-before-you-add skill, and the code-review smell baseline. The correction replaces process-randomized hashing with the existing FNV-1a helper already used by the tokenizers. Unsigned magnitude avoids the signed minimum-value trap without introducing another validator or abstraction. The engine retains immutable configuration and per-call working buffers, so the change adds no shared mutable state.

Public documentation explains deterministic coordinates, the overlap-based interpretation and the need to rebuild stored vectors/indexes. The added ASCII and UTF-8 golden vectors test exact coordinate selection, rather than repeating the same hash implementation inside the test. The classifier fixture now tests supported literal overlap instead of assuming an untrained hashing engine understands semantic associations. Numeric expectations are small and explicitly typed.

No hard documented-standard breach or meaningful heuristic smell was identified. The short word/ngram bucket-and-sign calculations follow the same operation with different contribution weights; extracting another helper is unnecessary for this bounded correction. Existing normalization and other test assumptions were not attributed to this diff.

This read-only review performed no builds, tests, benchmark runs or remote writes. Tool-enforced concerns were excluded, and no pending qualification result is inferred to have passed.
