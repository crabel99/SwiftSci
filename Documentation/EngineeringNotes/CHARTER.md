# Scientific computing charter

Adopted by crabel99 on September 27, 2026. Apply this charter when planning, implementing, validating or reviewing our SwiftSci work.

## Objective

Develop scientific data structures and numerical operations for local models and demanding scientific computation on Apple silicon.

Judge progress by supported engineering workflows, correct results, memory and execution costs, and maintainability. This objective describes the quality we intend to earn.

Numerical correctness and safe ownership are acceptance conditions. Evaluate speed, memory use and API convenience within those conditions. Prefer coherent, dependable capabilities that another engineer can understand and maintain.

## Resource efficiency across the library

Refined by crabel99 on October 18, 2026. This priority applies to the whole SwiftSci design: data structures, mutations, numerical algorithms, preprocessing, model operations, CPU execution, GPU execution and Neural Engine integration.

Maximize useful, validated computation within the application's resource budget while meeting its declared accuracy, behavior and latency requirements. Favor lower total resource cost per correct result over the shortest isolated execution time. Correctness, safe ownership and maintainability remain acceptance conditions. A fast result that requires more aggregate processor time or memory is a tradeoff, not an automatic improvement.

Treat latency requirements as constraints supplied by the workload. A longer operation can be the better default when it uses fewer resources and still meets those requirements. A latency-critical workload can justify extra resources, but that decision must be explicit. Do not invent a universal speed, CPU or memory weighting. Preserve distinct choices when workloads have different constraints.

Evaluate accumulated CPU time, accelerator work, peak live storage, retained storage, allocation and data-movement costs, and energy where measurements support it. CPU time is useful for CPU-path comparisons; it is not a universal cost unit across performance cores, efficiency cores, GPUs and the Neural Engine. Low host CPU usage does not account for work offloaded to an accelerator. Include preparation, conversion, synchronization, output materialization and ownership lifetimes when judging a complete operation.

This changes how we design, not only how we report benchmarks:

- Choose representations and algorithms that reduce work, full-data passes, copied bytes and temporary materialization while preserving the numerical contract.
- Carry compact native data into its consumers when possible. Include compatibility conversions and mutation costs in the design rather than hiding them behind an inexpensive-looking interface.
- Reuse preparation and workspace when actual reuse justifies it. Bound retained storage and concurrent work, and make ownership and release conditions clear.
- Use parallelism and hardware acceleration when they meet the workload's resource and latency constraints. Faster completion alone does not establish better resource efficiency.
- Prefer existing well-tested implementations and simpler maintainable code when added complexity has no demonstrated workflow benefit.

Validate the intended capacity benefit with sustained useful throughput under a fixed resource budget and bounded concurrency. Reduced CPU time or memory in one operation alone does not prove increased application throughput.

The [parallel sorting experiment](benchmarks/2026-10-18-dataframe-evaluation/parallel-sort-results.md) exposed the distinction: lower elapsed time came with higher accumulated CPU time. Preserve its original acceptance rules and evidence. Subsequent default-selection decisions follow this clarified project objective. The [dataframe evaluation protocol](benchmarks/2026-10-18-dataframe-evaluation/README.md) applies it to the current experiments.

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
| CPU, GPU or Neural Engine execution | Define the reference answer or quality target, latency requirement and resource budget before comparison. Account for dtype, layout, data residence, preparation, device work, synchronization, materialization and total CPU time. Compare complete-workflow resource costs for workflow-level claims; label isolated timings and exploratory runs with their narrower scope. |
| Test or certification infrastructure | Establish independent expected results and prove that relevant wrong outputs and malformed inputs are rejected. Include adverse numerical cases. Bound any certificate to the operations, configurations and qualification process actually checked. |
| Public API or architecture | Check promised behavior as well as familiar naming. State unsupported paths and maintenance costs. Discuss proposed public changes with the maintainer, who retains ownership of the upstream roadmap and architecture. |
| Documentation | Verify factual claims, references and status labels. Preserve historical evidence and distinguish it from current instructions. |

## Revisions

crabel99 owns the objective. Record a dated rationale when it changes. Editorial revisions may clarify execution while preserving the adopted commitments.
