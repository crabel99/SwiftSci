# Scientific computing charter

Adopted by crabel99 on September 27, 2026. Apply this charter when planning, implementing, validating or reviewing our SwiftSci work.

## Objective

Build a top-tier scientific and numerical library that can form the foundation for local models and demanding scientific computation on Apple Silicon.

Judge progress by supported engineering workflows, correct results, memory and execution costs, and maintainability. This objective describes the quality we intend to earn.

Numerical correctness and safe ownership are acceptance conditions. Evaluate speed, memory use and API convenience within those conditions. Prefer coherent, dependable capabilities that another engineer can understand and maintain.

## Apple silicon precision priority

Refined by crabel99 on September 28, 2026. Engineer core data structures, mutations and common scientific and AI algorithms together for Swift on Apple silicon. Treat numerical requirements, memory capacity, data movement, execution cost and safe ownership as design constraints.

Choose the least costly implementation that meets the declared accuracy and behavior requirements. Evaluate representation, algorithm, compiler output and hardware execution together. Extra precision or GPU use alone does not establish an improvement. Preserve explicit conversion semantics and measure complete workflows as well as isolated kernels.

Use hardware features where evidence supports them, including native fused arithmetic, SIMD and appropriate Accelerate operations. Verify their numerical contracts. Established libraries already contain hardware optimizations; compare measured behavior instead of assuming our language or platform focus guarantees an advantage.

See the [hardware precision record](benchmarks/2026-09-28-apple-precision.md) for the verified compiler probe, candidate implementations and validation gate. This objective does not change upstream API ownership or certification tolerances.

## Workflow

1. Define the step. Name the scientific or local-model workflow it supports, the requirement or failure it addresses, and the evidence that will establish success. For testing, certification, production repair or baseline work, first read the [required work order](benchmarks/2026-09-27-controlled-suite.md#required-work-order). Planning is complete when the affected behavior and acceptance checks are explicit and the scope follows that order.

2. Choose the approach. Apply every relevant row in the change guidance below. For substantial choices, use the [decision record format](DECISION-RECORDS.md) to explain alternatives and tradeoffs. For a small change, retain a concise explanation in the work record. The choice is ready when each affected contract has an explicit preservation rule or justified change, and the validation plan can detect a violation.

3. Verify the result. Run the acceptance checks against the changed artifact. Retain failures and regressions. A tolerance or workload-contract revision needs independent justification and its own record. Verification is complete when every acceptance check has a recorded result; claim success only for criteria actually met and identify unmet criteria as unresolved.

4. Report the decision and evidence. State the achieved scope, limitations and remaining work. Link the relevant record and identify the tested configuration for executable claims. Separate implementation correctness, numerical accuracy, model quality and performance conclusions. Before publishing a contribution, read the [upstream contribution boundary](README.md#relationship-to-upstream-contributions). Delivery is complete when each claim has supporting evidence and the recipient can distinguish verified behavior from a proposal or unresolved result.

## Change guidance

Apply the rows relevant to the change. Scale the work to its scope.

| Changed area | Required reasoning and evidence |
|---|---|
| Numerical behavior | Define precision, missing values, ordering, convergence and failure behavior. Preserve row identity. Check results against analytical answers, trusted datasets, appropriate higher-precision calculations or independent implementations. Justify any lossy conversion or reduced precision against the workload's error requirements. |
| Storage or mutation | Follow the affected data through loading, selection, preprocessing, computation and result access. Check ownership, lifetime and snapshot guarantees. Measure the allocations, retained memory and conversions relevant to the proposed benefit. |
| CPU/GPU execution or performance | Account for dtype, layout, data residence, preparation, synchronization and materialization. Define the reference answer or quality target before comparing speed. Include a representative complete workflow for workflow-level claims; label isolated timings and exploratory runs with their narrower scope. |
| Test or certification infrastructure | Establish independent expected results and prove that relevant wrong outputs and malformed inputs are rejected. Include adverse numerical cases. Bound any certificate to the operations, configurations and qualification process actually checked. |
| Public API or architecture | Check promised behavior as well as familiar naming. State unsupported paths and maintenance costs. Discuss proposed public changes with the maintainer, who retains ownership of the upstream roadmap and architecture. |
| Documentation | Verify factual claims, references and status labels. Preserve historical evidence and distinguish it from current instructions. |

## Revisions

crabel99 owns the objective. Record a dated rationale when it changes. Editorial revisions may clarify execution while preserving the adopted commitments.
