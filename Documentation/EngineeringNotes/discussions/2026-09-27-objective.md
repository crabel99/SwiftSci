# Scientific computing objective, September 27, 2026

Cal endorsed the preceding discussion's summary of SwiftSci as a potential foundation for serious numerical software on Apple Silicon. He asked that every step follow that engineering philosophy, with the goal of a top-tier scientific and numerical library for local models and demanding scientific computation.

The accepted direction connects efficient storage to numerical and model consumers, makes precision and failure behavior explicit, measures complete workflows, and keeps APIs familiar and maintainable. Controlled numerical error, traceable results and understandable algorithms belong alongside execution speed as requirements.

Cal's experience with nuclear engineering codes motivates a rigorous approach to verification and qualification. The discussion distinguished floating-point representation from numerical accuracy, and successful tests from qualification for a particular application. The objective is aspirational; it does not assert that the current library has attained the assurance of an established nuclear code.

We recorded the [engineering charter](../CHARTER.md) as the authoritative statement of that direction. The working-record entry points and decision format now link to it. The existing suite-first order remains in effect, and the internal record stays on our fork's documentation branch.
