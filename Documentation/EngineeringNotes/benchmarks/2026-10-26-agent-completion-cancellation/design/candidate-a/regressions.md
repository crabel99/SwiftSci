# Cheap regression specification

Use a deterministic Sendable rich mock whose `generate` throws if called and whose detailed stream emits an injected event array followed by normal end or a chosen error. Import SwiftLLM publicly, without @testable, where constructing GenerationCompletionInfo. Use an actor counter in EchoTool and observe agent stream events when checking forbidden events. No decoder or inference is needed.

1. Keep `ReActAgentTests.testReActAgentWithLocalLLMModel` unchanged. Existing generate-only conformance and answer still work; its step metadata is nil. Explicitly typed String closures still compile for both public run and stream, with nil metadata.
2. Pass rich mock as `any LLMModel`. Emit two chunks and `info(17,9,.stop)`. Assert expected text and exact metadata equality, proving existential dispatch and absence of chunk counting.
3. Two reasoning turns: valid action with stop info, then valid final answer with different stop info. Assert one tool call and each corresponding AgentStep has the exact originating info. Exercise unknown-tool fallback similarly to cover the third step construction site.
4. Parameterize `.length(.maxTokens)`, `.length(.contextWindow)`, and `.cancelled`. After otherwise parseable Action text, assert failed outcome, zero tool calls, and no thought/answer/tool-scheduled/completed event for that response. Repeat with parseable Final Answer text, asserting no completed or answer event.
5. Missing info, duplicate info, chunk after info, and no events must fail before parser or tool events. A sole stop info with zero chunks is a structurally valid completion; existing parser behavior remains authoritative for empty text.
6. Partial parseable action then thrown error must fail. Also emit valid stop info followed by a thrown error to prove collector waits for normal end. Never invoke the legacy method as recovery.
7. Prior valid action followed by an invalid rich turn must not execute the invalid turn's tool or emit completed. Previously completed tool side effects are not rolled back.
8. Check equality/default initializer compatibility for old AgentStep calls. Compile public-import mock on current and previous required CI compilers. Record results during implementation; none were run in this design phase.
