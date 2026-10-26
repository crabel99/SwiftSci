# Cross-judge recommendation

Choose candidate A as the base. It closes the demonstrated agent failure with the smallest public contract and reuses the decoder's existing detailed method directly. Candidate B is viable, and its buffered operation would be useful for several generic consumers. This bounded unit has one identified consumer, so that extra public aggregate, collector, and base-protocol operation are premature.

I read all three candidate A files, candidate B's complete package, the grounding document, and the architect red flags. I checked the relevant contracts and entire ReAct execution loop against the frozen integration source. This is a design review only. No builds, model execution, or production edits were performed. Configured cross-judge models were unavailable; this review used the available family and does not claim independent model-family agreement.

## Scores

Each score is out of five.

| Criterion | A | B | Reason |
| --- | ---: | ---: | --- |
| Source compatibility | 4 | 4 | Both retain generate-only conformers and String closures. A leaves the base protocol unchanged; B adds a defaulted requirement, with the necessary existential witness stated correctly. Both replace AgentStep's initializer with an extra defaulted parameter, which preserves ordinary calls but can break explicitly typed references to the old initializer. Neither claims binary compatibility. |
| Truthful metadata | 5 | 5 | Both retain producer counts unchanged and use nil or an explicit unreported case for legacy text. Both make the existing metadata initializer public. Neither counts chunks or invents a stop reason. |
| Validation before parsing, including late errors | 5 | 4 | A expressly requires chunks followed by exactly one info and normal stream end, including a regression for an error after valid stop info. B's collector contract covers malformed and throwing streams, but its proof targets do not explicitly require the late-error case. Make normal exhaustion after info explicit in either final contract. |
| Interface depth and small public contract | 5 | 4 | A exposes one optional capability backed by an already implemented method; collection and agent acceptance remain private. B provides a useful generic buffered operation, but also exposes LLMCompletion and collectDetails before a second consumer requires them. |
| Bounded implementation and cheap verification | 4 | 4 | Both reuse the existing generation loop and one ReAct loop, with deterministic mock proofs. A supplies the stronger matrix. Both need a concrete way to test rejected rich responses' agent events, because only native run is public today. Compiler checks remain unperformed. |
| Total | 23 | 21 | A is the better fit for this scope. |

## Contract details to preserve from A

- An existential typed as any LLMModel must detect CompletionReportingLLMModel and consume generateDetails. A rich-path error must never trigger a legacy fallback.
- Rich responses become eligible for parsing only after normal stream exhaustion, exactly one final info event, and stopReason equal to .stop. Seeing info alone is insufficient.
- Duplicate info, any chunk after info, missing info, either length reason, cancelled, and an iteration error all fail before parseResponse. An error after valid stop info still fails.
- Keep the String closure API signatures exact. Its accepted steps have nil completionInfo. Preserve generate-only models without requiring new methods.
- Attach exact metadata at all three AgentStep construction sites: final answer, unknown-tool observation, and tool result. One reasoning response can create one trace step. Do not attach a later response's counts to an earlier step.
- Keep the existing error conversion. The guarantee is a failed agent outcome before this response's parsing and tool side effects, not preservation of arbitrary underlying error types.

## Grafts and required clarifications

Take B's ownership explanation into the protocol documentation. The generation contract describes event ordering and truthful records; ReAct's consumer policy accepts only .stop. Length and cancelled remain legitimate producer records, although ReAct rejects them. A private collector may enforce both rules in one place without introducing another public operation.

Correct A's rationale about the rejected base-protocol alternative. B is not a fabricated-info detailed-stream bridge and does not add a bridging task. It returns a buffered aggregate with explicit unreported provenance, using a default witness for compatibility. Reject B for its additional public concepts in this bounded unit, not for an obligation its actual design avoids.

Preserve the old AgentStep initializer declaration if source compatibility includes initializer function references. Keep the four-parameter initializer and add a new overload whose completionInfo argument is required. The old overload can initialize nil. This also avoids ambiguous overload selection caused by defaulting completionInfo in both forms. If the accepted compatibility scope excludes function references, document that restriction rather than calling a defaulted argument completely source-compatible.

Make test access concrete before implementation. The actual public stream overload accepts a String closure; native run consumes its private stream internally. A rich fake passed to public run cannot expose thoughtDelta, answerDelta, or toolCallScheduled to the test. Do not add a public native stream overload just to fulfill the test prose. Test public run failure, zero tool calls, and absence of answer-memory writes with existing seams, or choose a narrowly internal test seam for exact event assertions. The final design must identify which proof it actually runs.

Require an explicit regression with chunks, valid stop info, then finish throwing. A shorter test that throws before info does not prove the collector waits for normal end. Also cover zero events and sole stop info, whose empty text goes to the existing parser only after structural validation.

## Rejections

Do not graft B's public LLMCompletion enum, base generateCompletion requirement, or public collectDetails helper into A. Doing so would combine two alternatives and lose A's small contract. Revisit B as a whole if multiple non-agent consumers need a single buffered completion API.

Do not add a second ReAct loop, a new completion stream event, fabricated legacy metadata, automatic retries, or token recounting. Do not claim this change fixes the existing unstructured agent-task cancellation lifecycle. Task cancellation checks in the collector apply to that collecting task; public run cancellation does not automatically propagate into the existing unstructured stream task.

The concrete decoder's generation task is currently nonthrowing. The rich contract supports future/custom throwing producers and request failures; it does not convert fatal inference failures into Swift errors.

## Verification still owed

The implementation must prove unchanged legacy mock conformance, public-import construction of metadata, rich existential dispatch with legacy generate forbidden, exact per-step metadata, nil legacy metadata, both length reasons and cancelled failing before a tool runs, malformed sequences, and errors before and after info. Include current and previous required CI compiler checks. This review establishes the design recommendation, not those implementation results.
