# Eager CSV implementation plan

1. Ground: complete. Exact conversion/inference/ownership contracts traced.
2. Sketch: complete. Two candidates and independent cross-judge; reference-owned typed accumulators with joined batch dispatch selected.
3. Agree: continue under approved strategy; no extra permission checkpoint required.
4. Implement: complete as local experiments. Shared conversion, scoped eager replay, geometric and chunked variants, then exact sizing. Unsuccessful output chunking removed from final experiment.
5. Verify: 375 DataFrame tests pass each Release/Debug/ASan. Final 108-worker resource comparison validates every output. Standardized tabular run passes 190 samples and certificate audit. CPU review remains unresolved for late Boolean replay and wider CSV data.
6. Review: standards/spec reviews clean, including exact-sizing delta. Verified implementation units committed locally; engineering evidence retained on the engineering-notes branch.
7. Promotion: blocked by CPU regression gates despite large-file RSS improvement. No push or PR. Next isolate framing/count, compact access and batch scheduling on wider/replay cases before selecting a default or explicit policy.
