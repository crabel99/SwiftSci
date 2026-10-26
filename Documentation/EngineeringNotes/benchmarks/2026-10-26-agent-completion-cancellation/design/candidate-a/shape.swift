// Design sketch only. These declarations describe changes in their owning files.
// No production code or build is part of this candidate.

// SwiftLLM/Core/LLMModel.swift
public protocol CompletionReportingLLMModel: LLMModel {
    // Successful iteration: chunks*, info, normal end.
    // Throws and consumer cancellation need not deliver info.
    func generateDetails(
        prompt: String, options: LLMOptions
    ) -> AsyncThrowingStream<GenerationEvent, any Error>
}

// SwiftLLM/Core/Generation.swift, inside existing GenerationCompletionInfo.
// Existing public properties and Sendable/Equatable conformance stay unchanged.
public init(
    promptTokenCount: Int,
    generationTokenCount: Int,
    stopReason: GenerationStopReason
) { fatalError("not implemented") }

// SwiftLLM/Core/TransformerDecoder.swift, existing class declaration changes to:
// public final class TransformerDecoder:
//     Module, CompletionReportingLLMModel, @unchecked Sendable
// Existing generateDetails signature already satisfies the new requirement.

// SwiftAgent/ReActAgent.swift, additive changes inside existing AgentStep.
public let completionInfo: GenerationCompletionInfo?
public init(
    thought: String,
    action: String? = nil,
    actionInput: String? = nil,
    observation: String? = nil,
    completionInfo: GenerationCompletionInfo? = nil
) { fatalError("not implemented") }

// Inside existing ReActAgent actor.
private struct Response: Sendable {
    let text: String
    let completionInfo: GenerationCompletionInfo?
}

// Public signatures preserved exactly, including closure return String.
public func run(
    query: String,
    llm: @escaping @Sendable (String) async throws -> String
) async throws -> (finalAnswer: String, trace: [AgentStep]) {
    // return try await run(query: query, completion: { prompt in
    //     Response(text: try await llm(prompt), completionInfo: nil)
    // })
    fatalError("not implemented")
}

public func stream(
    query: String,
    llm: @escaping @Sendable (String) async throws -> String
) -> AsyncStream<AgentStreamEvent> {
    // return stream(query: query, completion: { prompt in
    //     Response(text: try await llm(prompt), completionInfo: nil)
    // })
    fatalError("not implemented")
}

public func run(
    query: String,
    model: any LLMModel,
    options: LLMOptions = LLMOptions(temperature: 0.2, maxTokens: 256)
) async throws -> (finalAnswer: String, trace: [AgentStep]) {
    // return try await run(query: query, completion: { prompt in
    //     try await Self.generateResponse(prompt: prompt, model: model, options: options)
    // })
    fatalError("not implemented")
}

private func run(
    query: String,
    completion: @escaping @Sendable (String) async throws -> Response
) async throws -> (finalAnswer: String, trace: [AgentStep]) {
    // Existing run event fold, consuming private stream(query:completion:).
    fatalError("not implemented")
}

private func stream(
    query: String,
    completion: @escaping @Sendable (String) async throws -> Response
) -> AsyncStream<AgentStreamEvent> {
    // Move existing stream body here. One prompt/parser/tool loop remains.
    // let response = try await completion(prompt)
    // let parsed = parseResponse(response.text)
    // Add response.completionInfo at all three AgentStep construction sites.
    // Preserve existing catch AgentError and executionFailed conversion.
    fatalError("not implemented")
}

private nonisolated static func generateResponse(
    prompt: String, model: any LLMModel, options: LLMOptions
) async throws -> Response {
    // Check task cancellation.
    // If model does not conform to any CompletionReportingLLMModel:
    //   concatenate legacy model.generate output; return Response(text, nil).
    // Otherwise:
    //   var text = ""; var info: GenerationCompletionInfo? = nil
    //   for try await event in detailed.generateDetails(prompt:prompt, options:options):
    //     .chunk: require info == nil, then append.
    //     .info: require info == nil, then retain exact info.
    //   Check task cancellation.
    //   Require info != nil and info.stopReason == .stop.
    //   Missing/duplicate info, trailing chunk, length, or cancelled:
    //     throw AgentError.executionFailed(a specific stable message).
    //   Return Response(text:text, completionInfo:info).
    // Any thrown stream error exits before parser; never fall back to legacy generate.
    fatalError("not implemented")
}
