# Numeric decoder review

Both reviews inspect commit `5375f261c28c5cb1ee94f6c0892ba6d830e4312a` against parent `a5856aa40f8de2bbcc3653976419202a41222190`. Neither reviewer ran builds or benchmarks. Final validation records supply that evidence.

## Standards review

No actionable findings. The change stays within one private implementation file, adds no public API or deployment dependency, and follows the existing direct Date decoder. The measured alternative of inlining the shared adapter did not recover the gain. The small repeated parser sequence avoids additional mutable state or machinery.

## Specification review

No actionable findings. Both direct decoders preserve the classified methods' exact null-check and parser order. Explicit invalid values still become nil. Numeric-looking and Unicode nulls, floating-point special values, Int64 conversion, and Double rounding use the existing parser contracts. Classified inference is unchanged, including sample eligibility, ordered fallback, original tokens, and chunk-local streaming inference.
