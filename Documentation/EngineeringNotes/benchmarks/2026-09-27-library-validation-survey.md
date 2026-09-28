# Library validation survey and SwiftSci's intended use

Research date: 2026-09-27. This is an engineering assessment, not a release certification or a new performance comparison. It belongs only on `codex/engineering-notes`.

SwiftSci has a useful validation architecture, but the current evidence supports specific computations and bounded workflows. It does not yet establish general scientific or AI readiness. The most valuable next work is to prove the path from an input file to a scientifically meaningful result through the public APIs. Adding more isolated operation timings would leave the principal risks unresolved.

## Intended use determines the acceptance criteria

The proposed primary use is native scientific data preparation and numerical computation on Apple silicon. A user imports typed observations, selects and combines rows, constructs aligned vectors or matrices, runs a statistical calculation or model, and exports a result whose meaning survives the process. Tabular model training and local inference are closely related uses. This is a proposed focus for our contribution, not an assertion that upstream has adopted a new mission.

A useful acceptance workflow therefore preserves observation identity, feature order, missingness, precision, and any externally owned units or time definitions. It checks mathematical results and failure behavior. It measures the complete task within the target Mac's memory budget. A fast filter followed by a silent target permutation fails this use case even if both operations pass separate value tests.

The supported scope should be explicit. Distributed query processing, broad deep-learning training, a large pretrained model catalogue, and full replacement of pandas, SciPy, or PyTorch are not prerequisites for this purpose. A new benchmark belongs in the suite when it answers a named user's question, exercises a supported contract, and has an independent acceptance rule.

## Evidence reviewed

The local implementation inspected was `ab7aa2f1dab7256eed5de177fb5060a25740c643` on `codex/standardized-benchmarks`. The existing uncommitted `Benchmarks/README.md` documentation edit was preserved. This survey read representative upstream test and benchmark code as well as official documentation. It did not run new benchmarks or re-execute library tests. The detailed reviews separate observed source coverage from recorded passing evidence.

The existing acceptance run records 22 profiles and 1,132 engine-case executions: 1,102 passed, 30 failed, and zero infrastructure errors. The controller suite recorded 135 passing tests. These are not counts of unique algorithms or the library's entire test suite. See the [suite completion record](2026-09-27-suite-completion.md), [acceptance artifact](/Users/LOCAL_USER/Documents/src/SwiftSci/Benchmarks/Runs/finish-acceptance-02/acceptance.json), and [benchmark guide](/Users/LOCAL_USER/Documents/src/SwiftSci/Benchmarks/README.md).

Three specialist reviews supply the detailed comparisons and source links:

- [Dataframes, ingestion, and interchange](library-survey-2026-09-27/dataframes.md).
- [Numerical computing and statistical validation](library-survey-2026-09-27/numerical.md).
- [AI pipelines, tensor operations, and inference](library-survey-2026-09-27/ai.md).

These are representative reviews, not audits of every upstream release. Pinned source links identify exact inspected revisions. Documentation links labeled stable or main can change and are not dependency lockfiles.

## Practices worth adopting

| Library or standard | Observed practice | Consequence for SwiftSci |
| --- | --- | --- |
| pandas | Parametrized semantic tests and generated cases cover combinations of types, missingness, and joins. ASV retains performance history. | Declare semantics before using another implementation as a reference. Expand realistic joins and retain benchmark history. |
| Polars | Conversion tests check layout, buffer identity, read-only state, and whether copying is allowed. Streaming tests compare results with ordinary execution. | Equal values do not prove zero-copy conversion or global streaming equivalence. Test those promises separately. |
| Apache Arrow | Cross-language integration tests exchange fixtures. Ownership tests check lifetime and release. Parser fuzzing exercises malformed inputs. | Qualify the actual Swift bridge and parsers, including ownership and rejection behavior. |
| NumPy and Swift Numerics | Tests cover precision, noncontiguous layouts where supported, IEEE edge cases, and error measured in meaningful scales. | Broaden supported dtype and layout combinations. Use error criteria suited to the operation. |
| SciPy and LAPACK | Independent high-precision references, mathematical identities, and residual-based accuracy analysis supplement example answers. | Record conditioning and solver behavior so numerical failures can be interpreted and repaired. |
| xarray | Testing includes dimensions, coordinates, names, and attributes. | Scientific meaning needs an explicit preservation or rejection policy at conversion boundaries. |
| scikit-learn | Estimator checks cover public prediction contracts and persisted state. Its workflow guidance addresses leakage. | Validate the fitted public pipeline, including reload and feature order, rather than only the arithmetic inside it. |
| PyTorch, JAX, and MLX | Operator tests distinguish metadata, values, differentiation, randomness, and device execution. Benchmarking accounts for delayed execution. | Keep those contracts separate. Time completed work and identify actual precision and backend. |
| MLX-LM and MLPerf | Inference measurement identifies workload size, memory, throughput, latency, and, for MLPerf workloads, quality requirements. | A tiny decoder fixture proves bounded correctness. Production inference needs sustained workloads and separate quality evidence. |

The [dataframe review](library-survey-2026-09-27/dataframes.md), [numerical review](library-survey-2026-09-27/numerical.md), and [AI review](library-survey-2026-09-27/ai.md) link the primary test code behind these comparisons. xarray's [identity assertion](https://docs.xarray.dev/en/stable/generated/xarray.testing.assert_identical.html) provides the metadata example. Swift Numerics' pinned [elementary function tests](https://github.com/apple/swift-numerics/blob/0c0290ff6b24942dadb83a929ffaaa1481df04a2/Tests/RealTests/ElementaryFunctionChecks.swift) provide an Apple-native accuracy example.

## Current fit to scientific and AI work

| Intended workflow | Evidence already present | What still limits the claim |
| --- | --- | --- |
| Prepare numeric observations for analysis | Exact integer transport, explicit null and NaN distinctions, stable sorting, composite grouping, aligned matrix extraction, independent scalar answers | Standardized join multiplicity, mixed-type interactions, temporal meaning, and external interchange need broader coverage. Existing library tests already cover parts of these areas. |
| Fit and interpret numerical models | NIST datasets, independent high-precision answers, controlled models, and retained numerical failures | Required failing cases block qualification of their affected workflows. Coefficients alone do not establish solver stability or prediction reliability. |
| Train and use a tabular predictor | Frozen partitions, training-only scaling, held-out perturbation checks, fixed-update classification, and prediction comparisons | Public pipeline serialization, feature-schema errors, and representative held-out quality need qualification. Fixed-weight prediction currently has reported API failures. |
| Convert dataframe storage to model inputs | Non-square layouts, row and feature alignment, precision checks, source isolation, and staged conversion measurements | Largest logical source matrix in the bounded sweep is 4 MiB. This does not establish a production memory envelope or zero-copy behavior. |
| Run local neural inference | Independent fixed-weight logits, cache checks, CPU/GPU requests, and analytic vision fixtures | Public decoder loading and GPU cached RoPE have retained failures. Four-token tests and constant-image resize fixtures do not qualify sustained decoding or general spatial interpolation. |
| Process large files incrementally | Chunked APIs and a CSV streaming workload | Per-chunk grouping does not prove global aggregation. Bounded memory with a slow consumer, cancellation, and repeated use still needs operational evidence. |

Existing unit tests include typed joins, Unicode and dates, externally generated Parquet, Arrow ownership, sparse operations, concurrent pipeline state isolation, and cached decoder comparisons. Missing standardized coverage does not mean an implementation or all its tests are missing. Conversely, a test name is not evidence of its asserted property. The inspected Core ML export tests check files and metadata, while some vision loading tests finish with unconditional assertions. Those cannot establish prediction equivalence after loading. See the detailed reviews for the specific files.

## Changes that matter most

### Tie public claims to workload evidence

The main [README](/Users/LOCAL_USER/Documents/src/SwiftSci/README.md) makes broad zero-copy, data-race freedom, memory advantage, and complete parity claims. The bounded suite does not substantiate those claims across the library. This survey does not prove all those claims false. It shows that they exceed the evidence reviewed.

The next documentation contract should map each claim to its public API, supported input domain, checked environment, required profile, and remaining exclusions. Numerical conformance, predictive quality, and performance eligibility need separate statuses. The existing failed evidence must remain visible. An aggregate pass count must never turn a known failing loader or estimator into a qualified workflow.

A release coverage map should also identify which checks actually run in ordinary CI, the benchmark CI tier, and local GPU acceptance. The current ordinary CI exclusions mean a test file's presence is insufficient. Minimum and current supported Swift, macOS, and dependency combinations need a stated validation policy. This concerns Apple silicon compatibility, not an Intel target.

### Preserve meaning through the complete data path

Scientific data has identity as well as values. Duplicate-key joins can multiply observations. Missing-key policies can change sample membership. A feature permutation can produce valid-shaped tensors with wrong predictions. Timestamp units or an unrecorded physical-unit conversion can invalidate an otherwise accurate calculation.

xarray demonstrates why label semantics matter: arithmetic can align coordinates automatically, with intersection behavior that differs from positional arrays. SwiftSci need not adopt those rules or become xarray. It should state whether a boundary preserves, transforms, rejects, or delegates each piece of meaning. An external schema adapter can own units and time conventions when the dataframe does not. No implicit unit conversion or coordinate semantics should be inferred from plain numeric columns. [xarray alignment](https://docs.xarray.dev/en/stable/user-guide/computation.html#automatic-alignment).

The proposed next fixtures combine row IDs, duplicate keys, missing values, exact large integers, feature permutations, and supported temporal fields. Independent scalar models check membership and values after each stage. Generated cases need recorded seeds, minimized failures, and retained regressions. Existing deterministic random-byte parser tests are a useful start. A sanitizer-backed malformed-input campaign adds a different kind of evidence because serial and parallel implementations may share the same defect.

### Explain numerical failures before changing algorithms or tolerances

NIST and high-precision fixtures should remain. They need companion diagnostics for condition, rank, residual, and the chosen solver route. For linear solves, a small scaled residual measures a different property from coefficient accuracy. In least squares, a nonzero residual can be correct, so optimality and rank matter too. LAPACK's [accuracy analysis](https://www.netlib.org/lapack/lug/node72.html) provides the relevant distinction.

The recorded Wampler4 and Wampler5 failures affect both input interpretations and both the SwiftSci and SciPy paths. Some difficult ANOVA cases expose decimal-to-binary64 conversion limits plus additional SwiftSci arithmetic failures. Comparator agreement or shared failure cannot settle correctness. Each retained failure needs a reproduced input, reliable reference, error measure, justified bound, and explicit disposition.

The next test work should characterize well-conditioned, nearly collinear, rank-deficient, scaled, and offset cases. Production repairs follow on the separate repair branch. A tolerance chosen after seeing a failure is not a diagnosis. Mathematical identities can increase coverage, but independent answers remain necessary because related functions can share errors.

### Qualify the public model pipeline

The existing supervised fixtures already protect training-only scaling and fixed partitions. Extend that evidence through supported public preprocessing, fitting, persistence, and prediction APIs. Reload the fitted pipeline in a fresh process and compare every prediction and probability. Check feature-count errors, class order, missing weights, and format compatibility.

For model-quality claims, use paired frozen evaluation splits and a declared selection procedure. Group or time boundaries should follow the scientific sampling process. Repeated timing runs do not measure generalization. A fixed number of gradient updates is a useful arithmetic contract, but it is not equivalent to another estimator's default convergence algorithm. The [AI review](library-survey-2026-09-27/ai.md) explains these distinctions and the supporting scikit-learn checks.

Gradient checks belong only to operations that SwiftSci promises to train. Forward inference does not prove backward correctness. PyTorch explicitly distinguishes operator integration checks from mathematical gradient checks, a separation we should preserve. [PyTorch operator testing](https://docs.pytorch.org/docs/2.14/library.html#testing-custom-ops).

### Measure Apple silicon workflows at useful scales

Unified memory removes a hardware memory-pool boundary. It does not prove that a particular Swift array conversion avoids copies, that exported storage survives its owner, or that CPU/GPU synchronization is cheap. Those are implementation contracts. MLX documents [shared CPU/GPU memory](https://raw.githubusercontent.com/ml-explore/mlx/main/docs/src/usage/unified_memory.rst). Metal still requires completion and synchronization before dependent processor access. [Shared storage](https://developer.apple.com/documentation/metal/mtlstoragemode/shared).

For the supported conversion paths, require value, dtype, layout, lifetime, and mutation-isolation checks. Add buffer or allocation evidence before describing a path as zero-copy. Keep whole-process peak RSS, allocator bytes, logical payload size, and device allocation separate. They answer different questions and should not be added as though they were disjoint pools.

After correctness repairs, establish the performance baseline across small inputs, cache-sized work, and a representative resident working set selected from the machine's memory budget. Include narrow and wide matrices, skewed groups, missingness, and duplicate-heavy joins. Measure conversion, prepared computation, and the complete workflow. Record cold and warm conditions, actual device, precision, thread counts, and independent repetitions. Current environment recording already captures much of the host identity. Power, thermal conditions, and allocation evidence need an explicit policy.

Streaming acceptance should include a deliberately slow consumer, cancellation, repeated runs, and a declared memory ceiling. The current chunked implementation warrants these tests; source inspection alone does not prove an unbounded-memory defect. Global aggregation needs its own semantics and reference if it becomes a supported workload.

For neural inference, add context and batch sweeps only after the associated correctness repairs. Measure cache growth, reset behavior, time to first token, per-token latency distributions, and completed throughput. One licensed pinned checkpoint with a declared quality set is a more useful next step than a model zoo. CPU NumPy remains a numerical reference for a GPU result, not a matched-device performance competitor.

## What certification can mean here

A SwiftSci certificate should mean that a named workload contract passed for recorded inputs, source, dependencies, and hardware. The current unsigned local record is suitable for that purpose if its scope and failures remain explicit.

NIST certifies reference values for specified computations. It does not endorse software or guarantee behavior on another dataset. Our use of those values does not establish NIST certification, accreditation, or general numerical stability. [NIST FAQ](https://www.itl.nist.gov/div898/strd/general/faq.html).

Predictive quality also requires appropriate evaluation data and a scientifically defensible method. It is separate from arithmetic agreement. MLPerf adds prescribed quality and measurement rules for its particular workloads. A custom SwiftSci workload can adopt useful measurement practices without claiming an official MLPerf result. [MLPerf inference rules](https://github.com/mlcommons/inference_policies/blob/master/inference_rules.adoc).

Kiraa remains an unofficial research comparator. Its implementation can suggest experiments, but it is not a correctness oracle or a production baseline.

## Recommended next increment

The next testing increment should qualify two complete public workflows. The first reads scientific observations, filters and joins them, preserves IDs and schema, forms a matrix, and produces checked numerical results. The second fits preprocessing and a tabular estimator using training rows, reloads the fitted state, and predicts on held-out rows. Existing pinned datasets and analytic fixtures should supply these workflows before adding more dataset dependencies.

Completion requires the following evidence:

1. Every stage names its semantics, independent reference, supported layouts and types, and error or rejection rule. Unsupported cases are explicit.
2. Generated boundary cases replay deterministically. Discovered failures become fixed regressions. A bounded parser campaign records its scope and outcome.
3. Numerical failure reports include enough diagnostics to distinguish input conversion, conditioning, reference limitations, and implementation defects.
4. Public workflow checks verify row/feature identity, training-state isolation, and fresh-process prediction consistency. Deliberate corruption must make the checks fail.
5. A coverage map identifies which environment runs each required check. Performance records remain ineligible for affected failing cases.

This increment can expose more defects without repairing them on the testing branch. Once its contracts are reviewed, the repair branch addresses each defect separately. Passing repaired workflows then become the basis for memory-envelope measurements and the formal performance baseline. That order keeps the library's intended use central and preserves the evidence when an optimization changes behavior.
