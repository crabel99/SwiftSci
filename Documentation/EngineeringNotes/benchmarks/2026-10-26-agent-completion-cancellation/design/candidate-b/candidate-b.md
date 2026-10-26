# Candidate B: completion as a base-model operation

## Usage (caller's view)

```swift
// A caller with only the base existential gets truthful provenance.
let model: any LLMModel = decoder
switch try await model.generateCompletion(prompt: prompt, options: options) {
case .reported(let text, let info):
    print(text, info.generationTokenCount, info.stopReason)
case .unreported(let text):
    print(text) // Legacy model: no claim about tokens or why it stopped.
}

// Existing external models still implement only generate(prompt:options:).
struct OldModel: LLMModel {
    func generate(prompt: String, options: LLMOptions) async throws -> AsyncStream<String> {
        // Existing implementation.
    }
}

// ReAct's native overload keeps its existing call and result shape.
let (answer, trace) = try await agent.run(query: query, model: model)
print(answer, trace.last?.completionInfo as Any)

// The String-closure API still works and records nil completionInfo.
let result = try await agent.run(query: query) { prompt in
    try await remoteTextModel(prompt)
}
```

## Type and signature sketch

```swift
// SwiftLLM/Core/Generation.swift
public struct GenerationCompletionInfo: Sendable, Equatable {
    public let promptTokenCount: Int
    public let generationTokenCount: Int
    public let stopReason: GenerationStopReason

    // External detailed-model conformers must be able to create exact records.
    public init(promptTokenCount: Int, generationTokenCount: Int,
                stopReason: GenerationStopReason) {
        // not implemented
    }
}

/// Unreported means the model made no assertion about stop or token counts.
/// Reported contains the existing exact GenerationCompletionInfo.
public enum LLMCompletion: Sendable, Equatable {
    case unreported(text: String)
    case reported(text: String, info: GenerationCompletionInfo)

    /// Collect a detailed event stream. Throw on stream failure, missing/duplicate
    /// info, or a chunk after info. Never return partially parsed text.
    public static func collectDetails(
        _ events: AsyncThrowingStream<GenerationEvent, any Error>
    ) async throws -> Self {
        // TODO: append chunks until one terminal info; validate final position;
        // propagate iteration errors and cancellation; return .reported.
        fatalError("not implemented")
    }
}

// Internal to SwiftLLM; callers see failure through the throwing operation.
enum CompletionStreamError: LocalizedError {
    case missingInfo, duplicateInfo, chunkAfterInfo
}

// SwiftLLM/Core/LLMModel.swift
public protocol LLMModel: Sendable {
    func generate(prompt: String, options: LLMOptions) async throws -> AsyncStream<String>
    /// One buffered response. The default reports no metadata.
    func generateCompletion(prompt: String, options: LLMOptions) async throws -> LLMCompletion
}

public extension LLMModel {
    func generateCompletion(prompt: String, options: LLMOptions) async throws -> LLMCompletion {
        // TODO: consume existing generate stream; check caller cancellation;
        // return .unreported(text: collectedText). No fabricated info.
        fatalError("not implemented")
    }
}

// SwiftLLM/Core/TransformerDecoder.swift, existing concrete method retained.
public func generateCompletion(prompt: String, options: LLMOptions) async throws -> LLMCompletion {
    try await LLMCompletion.collectDetails(generateDetails(prompt: prompt, options: options))
}

// SwiftAgent/ReActAgent.swift
public struct AgentStep: Sendable, Equatable {
    // Existing properties retained.
    public let completionInfo: GenerationCompletionInfo?
    public init(thought: String, action: String? = nil, actionInput: String? = nil,
                observation: String? = nil, completionInfo: GenerationCompletionInfo? = nil) {
        // not implemented
    }
}

public func run(query: String, llm: @escaping @Sendable (String) async throws -> String)
    async throws -> (finalAnswer: String, trace: [AgentStep]) // existing API
public func run(query: String, model: any LLMModel, options: LLMOptions = /* existing default */)
    async throws -> (finalAnswer: String, trace: [AgentStep]) // existing API

private func stream(query: String,
    completion: @escaping @Sendable (String) async throws -> LLMCompletion
) -> AsyncStream<AgentStreamEvent> {
    // TODO: existing single ReAct loop. Await full completion; accept .unreported
    // under legacy behavior; accept .reported only for .stop. Throw AgentError
    // for .length or .cancelled before parseResponse, answerDelta, or tool calls.
    // Attach exact info to each accepted AgentStep.
    fatalError("not implemented")
}
```

## Module map and rationale

`Generation.swift` owns completion provenance and detailed-stream validation. `LLMModel.swift` owns the compatibility adapter. `TransformerDecoder.swift` reuses its existing `generateDetails` producer, with no second generation loop or bridge task. `ReActAgent.swift` converts both public entry points into `LLMCompletion` and feeds one private reasoning loop. The existing String adapter that concatenates chunks in `run(query:model:options:)` is removed first; it currently destroys the metadata.

This is a genuine base-protocol requirement, not an extension-only convenience. Swift's protocol witness for `generateCompletion` selects `TransformerDecoder`'s implementation through `any LLMModel`; the default witness keeps `OldModel` source-conforming. A compile/test proof must call the method on `any LLMModel` wrapping a rich mock whose `generate` traps. A plain protocol-extension method without a requirement would statically select the extension and fail that proof.

The base contract can honestly state unknown metadata only because `.unreported` is a first-class outcome. It must not describe that case as normal stop, zero tokens, or successful completion. A detailed conformer should use `collectDetails` so a missing terminal record, duplicate record, late chunk, or thrown iteration error fails before ReAct sees any text. Consumer cancellation may prevent delivery of info and must fail rather than turn a partial stream into `.unreported`. The default text stream cannot detect producer-side truncation, so legacy behavior remains limited. This is a source-compatibility design; binary compatibility needs separate evaluation.

The aggregate is deliberately buffered because ReAct parses only after generation. One public enum and one protocol operation hide event ordering, iteration errors, and legacy adaptation. They avoid a parallel public streaming API. `AgentStep.completionInfo` exposes exact counts for accepted rich responses without changing `AgentStreamEvent.completed` or the tuple return. The existing closure API records nil. Known length and cancelled responses fail before parser or tools; retry policy stays with callers.

## Synthesis decision

This candidate is offered as the base-protocol alternative for arena synthesis. It has not been selected over the other candidates.

## Tradeoffs accepted

- We accept a new base protocol requirement with a default witness in exchange for one unconditional call through `any LLMModel`.
- We accept buffering a detailed stream in exchange for validation before ReAct parses or invokes tools.
- We accept unknown legacy termination in exchange for preserving old conformers without false counts or stop reasons.

## Alternatives considered

An optional refining protocol keeps the base untouched and advertises detailed capability by a runtime cast. It has a smaller base surface, but each generic consumer must branch on capability and consume two stream shapes. An extension-only method cannot dynamically dispatch the concrete decoder through an existential.

## Design red flags checked

The enum and operation hide stream collection and validation behind a small surface, so this is not a shallow wrapper. The result carries domain metadata rather than tokenizer or MLX types. Generation validation stays in SwiftLLM; ReAct owns only its pre-parse safety policy. The two public run forms adapt at the boundary and share the existing loop, avoiding a second temporal pipeline or a pass-through model adapter.

## Open questions and risks

Can the library accept the source-compatible protocol change without an unassessed binary compatibility promise? Should an agent expose failed generation metadata in its error as a later unit, given failed attempts do not become `AgentStep`s? ReAct's separate unstructured-task cancellation lifecycle remains outside this design.

## Next implementation step

Remove the native run overload's String concatenation, then add the `LLMCompletion` collection seam and route both run entry points through the existing ReAct loop.

## Proof targets

Compile the existing one-method mock unchanged and an external-import conformer constructing `GenerationCompletionInfo`. Verify existential rich dispatch, exact stop counts on `AgentStep`, nil for legacy closures, length/cancelled/malformed/throwing detailed streams causing failure with zero tool calls, and no `.completed` for a partial final answer. Run the package's supported compiler plus its prior CI compiler.
