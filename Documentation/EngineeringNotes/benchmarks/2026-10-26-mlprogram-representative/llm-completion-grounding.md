# Generic LLM completion information: read-only grounding

Baseline examined: `/private/tmp/swiftsci-mlprogram-20261026/source`, `a1e234d25677d91ce5914062603c41233fe13c09`. This is a conditional later library unit, not a request to build serving, scheduling, company integrations, or another model runtime. No source edits, model execution, dependency changes, or builds performed.

## Components and exact facts

- `Sources/SwiftLLM/Core/LLMModel.swift:111-117`: public `LLMModel: Sendable` has one requirement, `generate(prompt:options:) async throws -> AsyncStream<String>`. It carries text only. No protocol entry point exposes stop reason, counts, or errors during iteration.
- `Sources/SwiftLLM/Core/Generation.swift:3-46`: reusable public `GenerationLimit` distinguishes output/context limits; `GenerationStopReason` distinguishes stop/length/cancelled; `GenerationCompletionInfo` stores exact prompt/generated token counts; `GenerationEvent` carries text chunks or final info. Do not create another set of equivalent types.
- `Generation.swift:23-32`: `GenerationCompletionInfo` has public immutable properties **but no explicit public initializer**. Swift's synthesized memberwise initializer is internal. External model implementations cannot construct this metadata today. Existing tests use `@testable import SwiftLLM`, so this external-consumer limitation is not tested by those construction sites.
- `Sources/SwiftLLM/Core/TransformerDecoder.swift:333`: concrete decoder conforms to LLMModel. `generateDetails` exists only on concrete type (`:595-605`), returning `AsyncThrowingStream<GenerationEvent, any Error>` synchronously. `generateStream` also exists only concretely (`:587-593`).
- Decoder all three entry points share prompt validation and generation loop (`:607-687`). Plain `generate` explicitly filters event.chunk and finishes nonthrowingly, discarding info (`:575-583`).
- `Sources/SwiftAgent/ReActAgent.swift:530-543`: native-model overload accepts `any LLMModel`, invokes only its text stream, concatenates chunks, and returns a String to existing closure-based run. The concrete detailed method cannot be called through this existential contract.
- Existing `AgentStep` has thought, action, actionInput, observation only (`ReActAgent.swift:96-114`). `AgentStreamEvent.completed` returns final answer and trajectory (`AgentStreamEvent.swift:59-63`), with no separate generation metadata. Counts cannot escape through current agent result even if an internal rich-model adapter reads them.

## Flow and what is actually lost

1. `ReActAgent.run(query:model:options:)` delegates to closure run and builds one String from `model.generate` (`ReActAgent.swift:535-541`). There is no count/stop validation.
2. Closure `run(query:llm:)` consumes `stream` and rethrows `.error` (`:280-299`). `stream` constructs a fresh ReAct prompt each reasoning step and awaits `llm(prompt)` (`:333-362`).
3. Returned text is parsed immediately (`:363`). Any `Final Answer:` text emits `.answerDelta`, records memory, appends an AgentStep and emits `.completed` (`:369-376`). A parsed registered action schedules and executes a tool (`:379-438`). The parser requires no completion marker beyond text tags (`:164-250`).
4. The concrete decoder tracks exact token budget and remaining context, excludes EOS from generated counts, distinguishes configured stop tokens from length limits, and reports producer cancellation (`TransformerDecoder.swift:644-686`). Plain generate discards those events **before the generic agent sees them**.

### Concrete consumer consequence

A detailed model can generate text such as `Action: EchoTool\nAction Input: bounded-prefix` and then hit maxTokens/context capacity. The text parser can treat this truncated prefix as a valid tool call and execute it because the generic path cannot see `.length(...)`. Similarly, truncated `Final Answer: incomplete text` can be marked completed. No actual model execution is needed to reproduce this boundary with a deterministic mock that emits known chunks followed by a known completion event.

Producer cancellation is also indistinguishable from ordinary stream exhaustion in the text-only bridge. The decoder's detailed producer emits `.cancelled` where a still-reading consumer can receive it (`TransformerDecoder.swift:679-686`); legacy text consumers only see partial text followed by end. Consumer cancellation can legitimately prevent delivery of any final info, so a richer consumer must not assume cancellation always supplies `.info`.

Exact counts cannot be reconstructed by counting chunks: UTF-8 fragments can span tokens, EOS is excluded, and buffered decoding can yield no chunk for generated tokens (`Generation.swift:24-29`; existing `GenerationResultTests.swift:107-118`). Fabricating zero/unknown-as-stop metadata for a text-only conformer would lie.

### Failure distinction: do not overstate

Initial errors are **not silently swallowed** by the current generic path. Decoder `generate` checks cancellation and validates options/context/prompt before returning its stream (`TransformerDecoder.swift:575-577,607-615`). Those throws reach ReAct's existing catch. Non-AgentError errors are then converted into `AgentError.executionFailed(error.localizedDescription)` (`ReActAgent.swift:454-459`), and closure run throws that AgentError (`:292-293`). This preserves a failed outcome/message but erases original typed GenerationError/CancellationError identity.

The text-only protocol cannot express asynchronous iteration failures, while a rich AsyncThrowingStream could. However, **this concrete decoder currently runs `Task<Void,Never>` with a nonthrowing generation loop** (`TransformerDecoder.swift:637-687`). Its detailed stream's present throwing channel handles request-validation/caller-cancellation setup (`:618-634`), not a demonstrated thrown error from MLX inference. MLX fatal/precondition errors cannot be turned into Swift throws by changing this protocol. Do not claim this bounded correction fixes concrete runtime exceptions that source does not emit.

## Existing coverage and compatibility

- `Tests/SwiftLLMTests/GenerationResultTests.swift`: tiny actual decoder tests cover EOS counts (`:71-78`), output/context boundaries including Int.max (`:81-98`), empty-prompt fallback (`:100-105`), UTF-8 token-vs-chunk behavior (`:107+`), both text adapters preserving detailed text (`:187-199`), all entry points returning typed request errors (`:201-229`), producer cancellation reason (`:231-238`), cancelled callers not starting tokenization (`:252-275`). Rich concrete generation is already implemented and tested; reuse it.
- `Tests/SwiftAgentTests/ReActAgentTests.swift:138-158`: one custom `MockModel: LLMModel` implementing only generate proves legacy source conformity and generic run's happy path. Preserve this consumer unchanged.
- `Tests/SwiftAgentTests/SwiftAgentOmniTests.swift:519-530`: closure run preserves error outcome/message. No test currently proves detailed metadata crosses an existential or that a length-stopped response prevents action/final-answer parsing.
- `Sources/SwiftLLM/SwiftLLM.docc/TransformerDecoderArchitecture.md:169-224`: explicitly documents concrete detailed metadata and that old LLMModel protocol remains unchanged. Documentation must be revised if a new capability is exposed. Existing calls/method signatures should remain working.
- Package is Swift-tools6.0, macOS14 (`Package.swift:1,15-17`); the user additionally requires compatibility checks with prior CI compiler. Do not solve by replacing the existing nonthrowing stream return type or requiring every old custom LLMModel conformer to implement a new method.

## Smallest independently testable correction candidates

The demonstrated need is a **typed optional completion capability at the library boundary and a check before parsing native agent output**. Existing generation event/stop/count types and decoder method should be reused. No scheduler/cache/runtime changes are needed.

One narrow backward-compatible shape is a refining protocol (name to be decided by main) that inherits LLMModel and requires the existing `generateDetails(prompt:options:)` signature. TransformerDecoder can adopt it without duplicating its generation loop. Generic consumers may test that capability from `any LLMModel`. Existing text-only conformers remain valid and retain their current behavior. An explicit public GenerationCompletionInfo initializer is necessary if external conformers are to implement that capability themselves.

The competing option is adding a protocol requirement with a default text-only bridge. That can preserve source conformity, but its default **cannot truthfully promise one final info event** because token counts/stop reason are unavailable. It also creates another bridging task/cancellation obligation. A plain extension method without a requirement is insufficient for dynamic dispatch of a richer concrete implementation through an existential. This is why a small optional refinement is worth considering before changing the base protocol contract.

For ReAct, the smallest meaningful behavior unit can choose the optional rich path, accumulate chunks, validate final completion before returning text to the existing parser, and reject length/cancelled completion through the existing error outcome. That prevents acting on known incomplete output and preserves old conformers. It does **not**, by itself, expose token counts in the agent's existing tuple result; describe this limit honestly.

If the intended unit must also preserve counts all the way to agent callers, the current AgentStep/closure String boundary needs a small internal response envelope and an optional completion property on AgentStep, with nil for existing closure/text models. Existing initializer can gain a defaulted optional argument and completed-event trajectory can carry it without a new enum case. This is a larger but still bounded library unit; main should decide scope explicitly rather than call a stop-gate alone full metadata preservation. Do not duplicate the entire ReAct loop for a second API.

Before adding any path, subtract the String-only adapter work that becomes redundant. Retain one common parser/tool execution loop and reuse existing GenerationEvent and GenerationCompletionInfo. Do not introduce speculative unknown stop cases, fabricated counts, retries, prompt compression, persistence, serving, or tool-policy redesign.

## Cheap proof targets, no model inference required

- Old MockModel still conforms and produces its existing successful final answer unchanged.
- A detailed mock passed as `any LLMModel` dispatches the detailed method; legacy generate can intentionally fail the test if invoked.
- Stop completion permits exact chunks and reports real counts if the chosen API exposes them.
- Both `.length(.maxTokens)` and `.length(.contextWindow)` after otherwise parseable Action text produce failure and **zero tool invocations**. A parseable partial Final Answer must not yield `.completed`.
- `.cancelled` completion is not accepted as success; do not rely on a cancelled consumer receiving final info.
- AsyncThrowingStream failure after yielding a partial parseable Action cannot invoke tools or become completed.
- Public-import (not @testable) mock can construct GenerationCompletionInfo, proving external conformer usability.
- If optional AgentStep metadata is included: exact info travels with each reasoning step; nil for legacy closures/models; no new streaming enum case needed.

## Uncertainty and excluded companion gaps

- These are source-grounded consequences; no concrete pretrained model was run to produce a truncation/action example. A controlled fake makes the independent regression deterministic.
- Appropriate agent behavior on length limit is a product/library contract decision: fail before parsing is the smallest conservative behavior, while retry/continuation/prompt shortening belong to callers and are not necessary to prove this seam.
- Current generic agent has a broader cancellation lifecycle issue: `stream` starts an unstructured Task and supplies no continuation.onTermination cancellation hook (`ReActAgent.swift:312-313,461-462`). `run`'s event loop has no Task.checkCancellation. This should be recorded separately; adding optional completion dispatch alone does not establish end-to-end task cancellation. Do not silently expand this unit into a full agent lifecycle rewrite.
- Current tool approval event does not visibly await approval in this ReAct implementation, but that is unrelated to completion metadata and not assessed here.
- Binary compatibility across previously compiled clients has not been evaluated; SwiftPM source compatibility is the grounded requirement visible here.
