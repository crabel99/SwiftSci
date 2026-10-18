# Recording engineering decisions

For each substantial choice, create a dated Markdown entry with a descriptive filename. Link it from the working record. Keep the explanation proportional to the decision; a small compiler fix can fit in a few paragraphs.

Follow the [charter workflow](CHARTER.md#workflow) when selecting and validating the approach. This record retains the supporting rationale and evidence.

Record the following:

1. Problem and constraints. Name the affected workload, users, source revision, compatibility requirements and observed bottleneck or failure.
2. Evidence. Link the source inspection, failing check, profile or benchmark. Separate measurements from hypotheses.
3. Alternatives. Describe the options actually considered and why each was kept or rejected. Preserve adverse results.
4. Choice and costs. Apply the [library-wide resource objective](CHARTER.md#resource-efficiency-across-the-library). Explain how the approach meets the workload latency requirement and resource budget. State measured total CPU time, device work, live and retained memory, data movement and maintenance costs where relevant. Identify unmeasured costs and keep resource tradeoffs explicit.
5. Correctness. Name the required behavior, numerical and missing-value semantics, ownership rules and tests.
6. Validation. Record the tested source, toolchain, command, result and limitations. Attribute benchmark results to the code that produced them.
7. Revisit conditions. Identify workloads, measurements or requirements that would change the decision.
8. Contribution status. Distinguish a local proposal, an implemented experiment, a submitted PR and a merged change. Link the upstream record when one exists.

Use this record to make the reasoning reviewable. It should explain the decision well enough that another engineer can disagree with it or maintain the code without reconstructing the chat.
