# Selected decoder design

Use the separate concrete decoder. Both independent candidates and the cross-judge prefer this shape for the current scope. The judge scores separate 11/12 and unified 9/12. Keep the existing scalar protocol and typed loops. Add one CSVColumnConversion case; do not add whole-batch decoder protocols or a stored closure.

Graft the unified candidate's explicit selectedRowCount factory label and token-plus-byte work budget. The eager reader supplies its exact selected total, streaming supplies actual chunk rows, and probes supply one. Rename eager Initial.capacity to totalRows so allocation capacity cannot silently become a work estimate.

A prefix constructor rejects empty and tiny sets, token counts exceeding selected rows, non-ASCII tokens, and saturated masks. Precharge each token visit by subtracting tokenCount from selectedRowCount, then decrement the remaining budget for each UTF-8 byte in one pass. This permits at most selectedRowCount total token/byte visits and avoids a separate length scan, allocation, sampling, or data cache. Exact-budget completion succeeds. The policy bounds preparation work; it is not a measured CPU-optimal crossover.

Store two private UInt64 masks directly on the new decoder. The proposed one-consumer mask helper adds a layer without hiding more policy and is omitted. Keep selection directly in the existing UTF-8 factory arm, rather than adding a one-caller forwarding factory. Fallback remains the unchanged hashed decoder and tiny sets keep the existing concrete equality decoder. Preparation failure publishes no partial mask.

First commit removes the unused CSVNullMatcher construction, with Release tests. Second commit adds selected decoding and bounded tests. Before keeping the combined change, run Release, Debug, Address Sanitizer, grammar parity, actual-source-path reference and control timings, Unicode scalar validation, and the standard production-default benchmark audit. No push or PR.

Near-boundary controls must compare cleanup alone and selected decoding at preparation work minus one, exact, plus one, and larger row budgets. Vary token count, token length, String layout, null density, eager/streamed scope and scheduling policy; record CPU and peak RSS separately. Preserve every flag. Avoid tuning the rule to one reference dataset.
