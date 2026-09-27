# Scientific computing charter

Adopted by Cal on September 27, 2026. This is the guiding objective for our SwiftSci work. It states our contribution direction; upstream retains ownership of its roadmap and public architecture.

## Objective

Build a top-tier scientific and numerical library that can form the foundation for local models and demanding scientific computation on Apple Silicon.

Judge progress by the engineering work the library makes possible, the correctness of its results, its memory and execution costs, and the ability of another engineer to understand and maintain it. Treat this objective as the standard for how we work, not a claim about the library's current maturity.

## Engineering commitments

- Preserve numerical meaning. Define precision, missing-value behavior, ordering, convergence and failure contracts. Retain row identity through transformations. Make any lossy conversion or reduced-precision execution explicit and justify its error against the workload's requirements.
- Design storage and consumers together. Follow data through loading, selection, mutation, preprocessing, solver or model execution, and result access. Measure allocations, retained memory and conversions where they matter. Preserve ownership, lifetime and snapshot guarantees when reducing copies.
- Choose execution from requirements and evidence. Account for dtype, layout, data residence, preparation, synchronization and result materialization. Use the CPU or GPU when that path satisfies the numerical contract and benefits the measured workload.
- Make results independently checkable. Use analytical answers, trusted reference datasets, appropriate higher-precision calculations and independent implementations. Include adverse cases, malformed inputs and deliberate wrong-result checks. Preserve failures and distinguish implementation correctness, numerical accuracy, model quality and performance.
- Keep scientific APIs familiar and maintainable. Familiar names help migration when their behavior is documented and tested. Prefer a coherent, dependable set of capabilities over breadth that hides inconsistent semantics or unsupported paths.
- Explain the decisions. Retain the alternatives, evidence, costs, limitations and reasons for revisiting each substantial choice. Give the maintainer enough reasoning to challenge a proposal and maintain the result.

## Applying the charter to each step

Before implementation, state which scientific or local-model capability the change supports, the requirement or failure it addresses, and the evidence that will establish success. Record substantial choices using the [decision format](DECISION-RECORDS.md). For a small change, a concise explanation in the work record is enough.

At completion, report the actual result against that criterion, including regressions, unresolved cases and the tested configuration. Scale validation to the change. A documentation correction needs an accurate record and working references; a numerical algorithm change needs evidence about numerical behavior.

Follow the current [suite-first work order](benchmarks/2026-09-27-controlled-suite.md#required-work-order). A failed numerical check remains a failed check. Changes to tolerances or workload contracts require independent justification and an explicit record. Keep exploratory timings distinct from an accepted performance baseline.

Demonstrate progress with complete, representative workflows as well as focused tests. Define the reference answer or quality target before comparing performance. Include preparation and result consumption where the workload requires them. Report precisely which operations and configurations pass; reserve certification claims for the defined scope and qualification process actually completed.

When a proposal improves one property at the expense of another, state the tradeoff. Accuracy requirements and safe ownership are acceptance conditions. Performance, memory use, API convenience and maintenance cost are evaluated within those conditions.

## Contribution boundary

Keep this charter and internal decision history on our engineering-notes branch. Implementation branches carry the code, tests, public usage instructions and relevant verified explanations appropriate for upstream review. Discuss public API or architectural changes with the maintainer. Openness to contributions does not transfer project ownership.

Revise this charter when Cal changes the objective. Preserve the dated rationale for a revision so future work can distinguish a deliberate change in direction from an undocumented exception.
