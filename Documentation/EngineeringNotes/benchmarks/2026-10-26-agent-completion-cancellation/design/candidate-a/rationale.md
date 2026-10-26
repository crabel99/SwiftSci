# Candidate A: optional completion capability with one agent loop

## Problem

At frozen source `c4de6cc866fff6f52100535dbcb38dd708558200`, `LLMModel.generate` returns text only. `TransformerDecoder.generateDetails` already reports exact counts and stop reason, but native `ReActAgent.run` erases them before parsing. A length-stopped action can therefore execute. Existing custom models and String closures must continue compiling. This design changes the capability boundary and carries accepted metadata through the existing trace. It adds no inference runtime.

## Usage, written first

```swift
import SwiftAgent
import SwiftLLM

// Existing call sites and closure annotations remain valid.
let complete: @Sendable (String) async throws -> String = { _ in
    "Thought: Done\nFinal Answer: 42"
}
let legacy = try await agent.run(query: "Compute", llm: complete)
assert(legacy.trace.allSatisfy { $0.completionInfo == nil })
let events = await agent.stream(query: "Compute", llm: complete)

// The existing existential accepts the rich decoder without an overload cast.
let model: any LLMModel = decoder
let result = try await agent.run(query: "Compute", model: model)
if let info = result.trace.last?.completionInfo {
    print(info.promptTokenCount, info.generationTokenCount, info.stopReason)
}

// External rich conformers construct the existing metadata type publicly.
let info = GenerationCompletionInfo(promptTokenCount: 17,
    generationTokenCount: 9, stopReason: .stop)
```

`agent` and `decoder` are instances already constructed by the caller. Existing custom `LLMModel` implementations need no changes. Rich implementations opt into `CompletionReportingLLMModel` and still provide their existing legacy `generate` implementation. A rich response stopped by length, cancellation, invalid event ordering, or iteration failure makes `run` throw the existing `AgentError` outcome before any parsing, tool event, or answer event for that response.

## Shape

First remove the native adapter's unconditional conversion to String. Move the existing ReAct loop, without duplicating it, behind a private completion closure returning `Response`. Both public String closure APIs wrap their String in `Response` with nil metadata. Native `run` chooses the rich capability dynamically; only legacy models use the old text collection behavior. Per subtract-before-you-add, this replaces the lossy adapter rather than adding another agent loop.

The optional protocol inherits `LLMModel` and requires the concrete decoder's existing synchronous `generateDetails` signature. Replace the decoder's `LLMModel` conformance spelling with the refining protocol. Add the missing public initializer to `GenerationCompletionInfo`. All existing event, count, and stop types remain authoritative.

`Response` is private to `ReActAgent`. The native collector owns event validation and text accumulation, per boundary-discipline. A rich successful sequence is zero or more chunks, exactly one info, and normal end. Reject missing or duplicate info and any chunk after info. Do not return immediately upon seeing `.info`; a later throw must fail the response. Only `.stop` is accepted for ReAct parsing. Both length cases and `.cancelled` fail. Propagate iteration throws into the loop's existing error handling. Check task cancellation at entry and after collection, without claiming this repairs the existing unstructured outer stream lifecycle.

The collector does not count chunks, retokenize text, invent metadata, or retry. It copies the producer's info verbatim. A public conformer's counts carry the producer's existing truthfulness obligation; this unit does not add speculative count or tokenizer validation. Existing `executionFailed` messages identify incomplete or malformed completion; no public error enum expansion is required.

After collection, the common loop calls `parseResponse(response.text)`. All three existing `AgentStep` creation sites receive `response.completionInfo`: final answer, unknown tool fallback, and executed tool observation. Existing `.completed(finalAnswer:trajectory:)` already transports those steps. No new stream event or public response wrapper is needed. Rejected generations produce no new step; callers needing their raw metadata can consume `generateDetails` directly.

The public additions hide capability selection, event validation, and metadata retention behind existing native `run`. Callers see one optional step property and one opt-in protocol, per interface-depth. No transport-specific type escapes beyond the existing domain `GenerationEvent`.

## Module map

- `SwiftLLM/Core/LLMModel.swift`: add refining protocol alongside unchanged base protocol.
- `SwiftLLM/Core/Generation.swift`: add explicit public initializer; reuse stored properties and enums.
- `SwiftLLM/Core/TransformerDecoder.swift`: change conformance only; reuse `generateDetails` and its generation loop.
- `SwiftAgent/ReActAgent.swift`: optional step metadata, private response collector, common completion closure loop, unchanged public entry points.
- Existing generation architecture docs: describe the optional capability and distinguish legacy text behavior from rich agent validation.
- Existing agent tests plus one public-import mock: deterministic regressions without model inference.

## Synthesis decision

Candidate A recommends the refinement and private response envelope. The parent arena selects the base and records any grafts here. No other candidate has been assumed.

## Tradeoffs accepted

- We accept nil metadata and unchanged completion uncertainty for legacy models in exchange for source compatibility and truthful counts.
- We accept failure on known incomplete rich output in exchange for avoiding parser or tool side effects from truncated responses.
- We accept existing AgentError conversion and failed generations absent from trace in exchange for keeping this contract narrow.
- We accept an additive AgentStep stored property under SwiftPM source compatibility; compiled-client ABI compatibility is outside the established requirement.

## Alternatives considered

A base `LLMModel.generateDetails` requirement with a default text bridge would allow every existential to call it, but its default cannot supply truthful terminal counts or stop reason. It either weakens the event contract or exposes unknown-completion policy to all consumers, and adds bridging task cancellation work. The optional refinement keeps that uncertainty on the existing text path.

A separate public completion response API plus a second agent execution path would expose collection policy and duplicate orchestration. Its larger caller contract hides less, because callers must choose APIs and retain alignment with existing run/stream behavior. The private envelope retains the existing caller experience.

A gate-only adapter is smaller, but accepted counts still disappear at the String closure boundary. The defaulted optional AgentStep property is the smallest change that preserves those counts to generic callers.

## Red flag screen

No pass-through public method is added; existing `generateDetails` becomes a protocol requirement. Collection and validation stay together. No parallel loop or staged public methods require caller coordination. The only duplicated adaptation is the two small public String closure wrappers, each hiding the same private representation.

## Open questions and risks

Does the supported previous CI compiler accept these exact Swift 6 existential and Sendable signatures? Implementation must run the cheap tests on both required compilers. Can the existing outer agent stream cancellation issue remain a separately tracked change? This design deliberately makes no end-to-end cancellation guarantee.

## Next implementation step

Add the public-import rich mock and strict terminal-sequence regression matrix, then replace the lossy native adapter and thread the private response through the existing loop.
