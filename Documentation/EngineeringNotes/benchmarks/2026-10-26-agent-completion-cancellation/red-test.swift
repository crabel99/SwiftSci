import Testing
import SwiftAgent
import SwiftLLM

private actor CompletionToolCounter {
    var calls = 0
    func record() { calls += 1 }
}

private struct TruncatedModel: CompletionReportingLLMModel {
    let text = "Thought: Use the tool\nAction: Echo\nAction Input: truncated"

    func generate(prompt: String, options: LLMOptions) async throws -> AsyncStream<String> {
        AsyncStream { continuation in
            continuation.yield(text)
            continuation.finish()
        }
    }

    func generateDetails(prompt: String, options: LLMOptions) -> AsyncThrowingStream<GenerationEvent, any Error> {
        AsyncThrowingStream { continuation in
            continuation.yield(.chunk(text))
            continuation.yield(.info(GenerationCompletionInfo(
                promptTokenCount: 17, generationTokenCount: 9, stopReason: .length(.maxTokens))))
            continuation.finish()
        }
    }
}

@Suite("Completion reporting at the native agent boundary")
struct CompletionReportingTests {
    @Test("A known truncated action cannot execute a tool")
    func truncatedAction() async throws {
        let counter = CompletionToolCounter()
        let tool = CustomAgentTool(name: "Echo", description: "Count calls") { input in
            await counter.record()
            return input
        }
        let model: any LLMModel = TruncatedModel()
        let agent = ReActAgent(tools: [tool], maxSteps: 1)
        await #expect(throws: AgentError.self) {
            _ = try await agent.run(query: "Test", model: model)
        }
        #expect(await counter.calls == 0)
    }
}
