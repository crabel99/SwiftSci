# Generic generation completion contract

## Architect
- [x] Ground: reuse traced LLM/agent source from ../swiftsci-mlprogram-20261026/llm-completion-grounding.md. Existing types, concrete implementation and callers traced.
- [x] Sketch: compare optional refining protocol vs backwards-compatible base requirement. Existing configured model names are unavailable; use available families for two structurally distinct candidates.
- [x] Agree: autonomous by user instruction, no checkpoint.
- [ ] Implement: separate source branch after integration freeze; preserve existing conformers, shared ReAct loop and exact completion info.
- [ ] Scrap: redesign if repeated workarounds reveal wrong shape.

## Arena
- [x] Frame: use existing detailed types and streaming API; metadata must reach generic consumers without fabricated legacy counts. Known incomplete/error output must never reach parser or execute tools. Existing LLMModel conformers and closure APIs remain source compatible.
- [x] Fan out: independent candidate directories.
- [x] Cross-judge: read completed candidates only.
- [x] Pick: grade source compatibility, truthful metadata, pre-parser completeness gate, interface depth and bounded implementation/verification.
- [x] Graft: record what is adopted and rejected.
- [ ] Verify: deterministic mocks plus external public-import consumer; native/fullCI and older compiler on final source.

No server/runtime/dependency migration. Broader ReAct consumer cancellation lifecycle remains separately scoped. Production source c4de6cc866 remains frozen for current qualification.
