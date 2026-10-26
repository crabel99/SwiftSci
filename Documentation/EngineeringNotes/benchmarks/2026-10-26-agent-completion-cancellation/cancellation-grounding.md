# ReAct consumer cancellation grounding

Read-only source: `/private/tmp/swiftsci-llm-completion-20261026/source`, verified `6ef1a4b35be11a611d8d101d1db2c56cd3c5a953`. No source edits, builds, or model execution. Read explainer prompt and current ReActAgent, AgentDialogueController, completion tests inventory.

## Trace and defect

Both public closure `run` and `stream` adapt text into private Response and share one loop (`Sources/SwiftAgent/ReActAgent.swift:298-348`). Native-model run also uses that loop (`:572-579`). Private stream constructs an unstructured `Task` but discards its handle (`:349-350`) and installs no `continuation.onTermination`. This task inherits actor context, not structured parent cancellation.

Private `run` consumes AsyncStream (`:311-325`). A cancelled consumer's awaiting iterator can end without any `.completed` or `.error` event; run then returns default empty answer/trace as **successful result** (`:312-313,327`). It has no initial or final cancellation check.

Meanwhile the producer can remain in the model closure (`:399`) after its consumer exits. When a noncooperative closure resumes normally, the closure path immediately parses text (`:400`) and can schedule/execute tools (`:438-475`) or publish a final answer (`:406-413`). The native helper's checks (`:587,594,614`) only help if the producer task itself is cancelled; discarded ownership prevents that cancellation from reaching it.

Tool timeout uses structured children (`:512-526`). Cancellation of their owning producer would propagate, but the operation must cooperate. Inner tool catch currently turns every error, including cancellation, into an observation and continues (`:477-485`). Thus adding only onTermination is insufficient: cancelled producer could still continue a new step or emit maxSteps fallback success (`:488-490`).

A pre-cancelled caller has the same gap: run starts a producer before iteration can terminate. Direct stream callers also need a pre-cancel guard because starting an unstructured Task does not preserve the caller's cancelled flag. These findings concern ordinary public APIs, independent of model implementation/GPU.

## Small ownership correction

Keep public signatures and the single private loop. Retain producer Task in the AsyncStream builder and set onTermination to cancel it. Check caller cancellation before creating work; a pre-cancelled nonthrowing stream can return an already-finished stream, while run must throw CancellationError before opening the stream.

Run must check cancellation while handling events and after iteration, before returning success. This converts cancellation-driven stream exhaustion to typed CancellationError instead of empty success. Check before processing a queued `.completed` too, since cancellation may race with buffered events.

Producer checkpoints belong at work boundaries: before initial memory/model work, each new reasoning step, immediately after awaited completion **before parsing**, before tool invocation, after tool completion, and before publishing successful final/fallback completion after intervening awaits. Tool wrapper/child checks should prevent knowingly launching work from an already-cancelled task, including timeout-disabled direct execution. Do not duplicate the loop.

Let cancellation escape the inner tool-observation catch when the producer is cancelled; ordinary tool errors should keep existing observation behavior. A final producer cancellation handler can finish its stream quietly; public stream cannot throw CancellationError because its element/error contract remains unchanged. Run derives typed consumer cancellation from its own Task flag. A model that independently reports `.cancelled` remains the existing model failure contract, distinct from cancellation of run's caller.

Cancellation is cooperative. This correction requests cancellation and prevents later parsing/tools once cancellation is observed. It cannot interrupt arbitrary noncooperative model/tool code, undo an already-started side effect, or promise producer drain before cancelled run returns. Structured timeout scopes also await noncooperative child completion; timeout is not forceful termination.

## Deterministic no-GPU tests

Use actor-backed checked-continuation gates with explicit entered/released/cancellation-observed signals; no timing sleeps as synchronization. Always release gates during teardown, even on failed assertions.

| Boundary | Handshake and required result |
|---|---|
| Pre-cancelled run | Cancel current task before run; completion/tool counters remain zero; catch typed CancellationError, never successful tuple. |
| Pre-cancelled public stream | Cancel caller before obtaining/iterating stream; no completion/tools and no successful completed event. |
| Waiting completion | Wait for closure-entered; cancel consumer; await run returning CancellationError and producer cancellation handler signal. This catches missing onTermination deterministically. |
| Ignored cancellation | Closure suspends on continuation, observes cancellation handler but deliberately returns parseable Action after release; assert no tool calls or next completion. Also test parseable Final Answer. |
| Cancelled public stream iterator | Consume stream in Task; cancel after completion-entered; producer observes cancellation; releasing ignored closure cannot run tools. |
| Tool execution | Tool starts then suspends cooperatively; cancel consumer; tool sees cancellation; no next model call/fallback success. Cover positive and zero timeout. |
| Successful control | Uncancelled one-tool trajectory still completes and retains completion metadata. Ordinary tool error still becomes observation. |

For ignored-cancellation zero-tool assertions, avoid reading counters immediately after releasing the gate: that races the producer. Use a test-only lifetime sentry owned solely by the producer completion closure (or an inherited TaskLocal owner); drop all consumer-side references and await its deinit signal after cancelled consumer has returned. This proves producer quiescence before final counters, without exposing a production task handle or inserting sleeps. A cancellation-observed signal alone proves propagation but not producer completion.

Existing completion tests remain necessary: this unit changes outer task ownership, not model stop-reason policy. AgentDialogueController's stream consumption (`AgentDialogueController.swift:105-159`) is a real consumer that benefits; no UI/API redesign is required.
