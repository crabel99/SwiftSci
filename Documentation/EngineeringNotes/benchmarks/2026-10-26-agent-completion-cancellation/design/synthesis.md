# Selected completion capability

Use candidate A. Parent scores match the cross-judge's 23/25 for A and 21/25 for B. Both preserve truthful metadata, but A reuses the existing detailed method and avoids a new public aggregate and collector for one known generic consumer.

The optional `CompletionReportingLLMModel: LLMModel` requires the decoder's existing synchronous detailed-stream signature. The unchanged base protocol preserves old conformers. A private response carries text and optional producer metadata into the single existing ReAct loop. Only normally exhausted, structurally complete rich streams with stopReason `.stop` reach the parser. Length, cancellation, missing/duplicate info, chunks after info, and any stream throw fail the agent before that response's tool or answer side effects. Counts are copied exactly. Legacy metadata stays nil.

Grafts and corrections from the judge and candidate B:

- Preserve the exact four-argument AgentStep initializer, including typed initializer references. Add a second overload with a required completionInfo argument. Old initialization sets nil; no ambiguous fifth default.
- Document producer ordering separately from ReAct acceptance policy. Length and cancelled are valid producer outcomes but rejected by this consumer.
- Test public run failure, zero tool invocations and no assistant-memory writes. The public rich API is run, so do not promise direct forbidden-event assertions or add a public stream overload just for tests.
- Explicitly test stop info followed by a thrown error. Collection waits for normal stream end.

Candidate B's buffered aggregate truthfully represents unreported metadata and needs no bridge task. It loses here because it adds public concepts and modifies the base protocol before a second consumer requires them. It remains a viable alternative for a future multi-consumer need. No graft of its public aggregate, operation or collector is needed.

Red flag screen: no second reasoning loop, transport type, staged public API, retry machinery, retokenization or runtime change. The two small public closure wrappers adapt existing String calls to one private representation. Broad cancellation of the outer unstructured agent task remains open and is not claimed solved. SwiftPM source compatibility is tested; compiled-client ABI compatibility is not promised.

Implementation starts with additive protocol/public metadata construction and a deterministic truncated-action regression, then removes the lossy adapter and threads accepted info into all three AgentStep sites. External public imports prove conformer usability. The qualified integration parent remains unchanged in its separate checkout.
