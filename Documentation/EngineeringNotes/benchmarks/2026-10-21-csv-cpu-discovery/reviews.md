# Independent review results

Standards review found no actionable findings against the previous exact-sizing prototype. The private output specialization preserves target boundaries. Original-token offsets remain internal. Borrowed memory stays scoped to joined workers, and tests use small typed expressions.

Specification review found no actionable findings. Counting shares the existing grammar, including delimiter precedence, quoted and ragged records, EOF behavior, limits, and cancellation. Rejected offsets are rebased into the original retained source. Pruning only eliminates originally eligible types. Surviving candidates still replay all rows. Overrides do not enter fallback, missing fields stay distinct from invalid values, and streaming inference remains chunk-local.

The final cleanup removes a redundant rejection switch, and the added regression test covers the offset of a rejection beyond the first eager batch. Release, Debug, and Address Sanitizer validation cover that final head.
