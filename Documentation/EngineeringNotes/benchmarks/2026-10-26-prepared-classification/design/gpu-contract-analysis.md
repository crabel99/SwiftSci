# Original logistic GPU and NaN contract analysis

## Scope and current conclusion

This record qualifies two failures from `native-debug/tests.log` without changing production code, tests, or tolerances.

The NaN expectation is contradicted by the original implementation. The original CPU prediction path clamps its scalar sigmoid input with `Swift.min` and `Swift.max`; with NaN in the argument position used here, that expression selects the upper finite clamp and returns a positive-class probability that rounds to `1.0`. The observed `[0.0, 1.0]` therefore follows the pre-prepared implementation rather than indicating a prepared-path regression.

The GPU disagreement with the CPU reference is also not evidence of a prepared-path regression. Prepared and row GPU fits agree within the existing `1e-6` same-route checks, while the original GPU solver already used the same Float MLX loss and update sequence as the current solver. The `3e-5` CPU/GPU requirement has no historical basis: the original routing test checked one probability with a tolerance of `0.1` after 100 epochs.

An isolated run of the exact original commit remains the deciding evidence for the absolute GPU values. Until that capture is available, the zero-logit loss derivative described below is a strongly supported cause of the CPU/GPU offset, but it is still an inference rather than a captured original-binary result.

## Evidence from the original implementation

The reference revision is `e19db7dda4567c425b7eb002da82e234e6c7980f`.

At that revision, `Sources/SwiftML/Core/LogisticRegression.swift`:

- converted row values and targets to `Float` before creating MLX arrays;
- initialized `w` and `b` to zero;
- computed `matmul(X, w) + b`;
- called the project-local `Losses.binaryCrossEntropy`;
- created `valueAndGrad(lossFn, argumentNumbers: [0, 1])`;
- updated `w` and `b` from `grads[0]` and `grads[1]`; and
- evaluated the arrays before publishing Float values as Double snapshots.

The current GPU solver preserves that formula, Float policy, initialization, argument selection, and update order. Its material changes are the prepared input owner, scoped GPU reads, cancellation checks, validation, and atomic publication of a local candidate state. Those changes do not replace the numerical algorithm.

The original `Tests/SwiftMLTests/Regression+RoutingTests.swift:54-75` compared CPU and GPU only on rows `[-2], [-1], [1], [2]`, with learning rate `0.2` and 100 epochs. It asserted only that the first positive probability differed by less than `0.1`. It did not establish parameter equality or a `3e-5` route tolerance.

The MLX Swift dependency is revision `4657976edcdd2c60642424985d474b45ddddb390` in both the reference revision's `Package.resolved` and the current resolved package. The current checkout describes it as `0.32.3-1-g4657976`. The baseline can therefore hold the MLX revision constant while comparing the two SwiftML revisions.

## NaN prediction behavior

Both the original revision and the current source define the scalar CPU sigmoid as:

```swift
1.0 / (1.0 + exp(-Swift.max(-50.0, Swift.min(50.0, x))))
```

This is `Sources/SwiftML/Core/Numerics.swift:8-10` in the current tree, and the file is identical at the reference revision. With `x = .nan`, this call order retains the first finite operand in `Swift.min(50.0, x)`, then selects `50.0` in the outer maximum. `sigmoid(50.0)` rounds to `1.0` in Double, so `predictProbability` returns `[1.0 - p, p] == [0.0, 1.0]`.

The native Debug log confirms exactly those two values at `tests.log:1273-1279`. The failed test expected two NaNs, but that expectation does not match the unchanged legacy scalar sigmoid. The isolated old-commit probe should still capture this public behavior so the fixture records the binary contract as well as the source explanation.

This finding applies to the legacy row CPU prediction route. The prepared boundary's finite-value rejection is a separate, intentionally stricter contract.

## Why the GPU result can differ from the CPU result

### Mean reduction is equivalent

The CPU solver forms `diff = sigmoid(logit) - target`, sums each gradient, and multiplies by `1 / N`.

The project-local GPU loss at `Sources/SwiftML/Losses/Losses.swift:13-18` is:

```swift
mean(maximum(logits, 0.0) - logits * targets
    + log(1.0 + exp(-abs(logits))))
```

For the `[N, 1]` logits used here, `mean` divides by `N`. The broadcast bias gradient aggregates those `N` mean-scaled contributions into one scalar. The reduction therefore matches the CPU solver mathematically. A missing bias reduction does not account for the observed difference.

### The zero-logit subgradient is the likely cause

For nonzero logits, the derivative of the expression above is `sigmoid(logit) - target`, which matches the CPU formula. At exactly zero, the expression is assembled from `maximum(logit, 0)` and `abs(logit)`, both of which require an autodiff subgradient convention. The smooth binary-cross-entropy derivative at zero is `0.5 - target`, but the derivative of this decomposed graph depends on MLX's tie behavior for those two operations.

Every first-epoch logit is exactly zero because both parameters start at zero. If MLX contributes zero from the `maximum` and `abs` branches at that point, the first GPU derivative becomes `-target`, differing from the CPU derivative by `-0.5` for every row. With learning rate `0.05`, that produces a one-step bias offset of exactly `0.025`:

```text
0.05 * 0.5 = 0.025
```

After four updates, the native log reports a CPU/GPU bias difference of `0.024075167779072558`. This is close to the predicted first-step offset after three later updates. The same constant first-step derivative offset changes each weight in proportion to its feature mean. For the exact generated fixture, the feature means are `-0.00525` and `-0.0014`. The predicted first-step weight-offset magnitudes are therefore `0.00013125` and `0.000035`. After four updates, the log reports `0.00011904652994189358` and `0.00003217521151128652`. The matching scale and decay across the bias and both weights strongly identify the zero-logit subgradient as the cause. The resulting positive-probability differences are approximately `0.0060`, also matching the sigmoid midpoint slope: `0.25 * 0.024075` is approximately `0.006019`.

This numerical pattern makes the zero-logit subgradient the leading root-cause explanation. It should be confirmed cheaply by capturing the original GPU bias after one epoch. If the old binary's one-epoch bias differs from the analytical CPU bias by about `0.025`, the public result directly confirms the explanation. No loss rewrite belongs in the prepared integration: changing to a smooth `logAddExp` formulation would change the established GPU optimizer trajectory.

For context, MLXNN's own BCE implementation uses `logAddExp(0, logits) - targets * logits`, but SwiftML's logistic solver does not call that implementation. It calls its local `Losses.binaryCrossEntropy`, which already existed at the reference revision.

## `valueAndGrad` argument selection is valid

The MLX Swift API uses `[MLXArray]` as its canonical positional-input representation. In `.build/checkouts/mlx-swift/Source/MLX/Transforms+Grad.swift:58-66`, the overload accepts a collection of argument indexes and forwards it to `buildValueAndGradient`. In `Transforms+Internal.swift:47-62`, that collection is passed directly to `mlx_value_and_grad`, and the resulting closure is applied to the array of inputs.

Accordingly:

```swift
let gradFn = valueAndGrad(lossFn, argumentNumbers: [0, 1])
let (_, grads) = gradFn([w, b])
```

requests gradients for positional input slots 0 and 1, then returns those gradients in the corresponding array. It is the intended multi-input pattern for the canonical `[MLXArray]` overload. It does not mistakenly request two argument numbers from one opaque Swift collection value. The identical pattern in the original and current solvers also rules it out as a prepared-integration change.

## What the current native run proves

The current run proves the following facts:

1. The legacy CPU supplied-parameter NaN prediction returns `[0.0, 1.0]` in this configuration.
2. For `.gpu`, `.auto`, and `.ane`, row and prepared fits agree within `1e-6` for parameters and sampled probabilities. This supports equivalence of the two representations on the same routed solver.
3. All three non-CPU requests resolve to the same GPU numerical result for the 1,000-row fixture.
4. That GPU result differs from the Double CPU result after four epochs, including a bias difference of `0.024075167779072558`.
5. The run does not prove whether the absolute GPU result changed from the original revision.

The last fact is why a CPU reference cannot qualify compatibility here. The compatibility question is old GPU versus new GPU on the same environment and dependency graph.

## Independent baseline fixture strategy

Use a tiny public-API probe built from an isolated checkout at the exact reference revision. Do not copy the old optimizer into a test and do not generate the expected values from the current branch. Either approach would cease to be an independent compatibility baseline.

Capture these cases:

1. A CPU model initialized with `weights: [1.0]`, `bias: 0.0`, and a row containing NaN. Record the full two-class probability.
2. The exact 1,000-row routed fixture now used by `PreparedLogisticRegressionTests.swift:70-83`, with learning rate `0.05`, for GPU epochs 0, 1, and 4. Epoch 1 isolates the zero-logit derivative; epoch 4 matches the failing comparison.
3. Fixed probability samples, preferably indexes 0 through 15, plus weights, bias, requested device, and resolved device.
4. One routing capture for `.auto` and `.ane` if the original public API exposes the resolved route. Their numerical values need not be duplicated once they are shown to resolve to the same GPU backend.

Record enough provenance to reproduce the capture:

- SwiftML source SHA;
- complete `Package.resolved` hash and MLX revision;
- Swift and Xcode versions;
- macOS and hardware model;
- Debug or Release configuration;
- fixture generator description or checksum; and
- three repeated runs per configuration to detect nondeterminism before freezing expectations.

GPU values originate as Float. Store each captured parameter and probability both as a decimal value and as `Float.bitPattern`. If the three runs and Debug/Release captures are bit-identical, use the bit patterns as the baseline. If they are not, preserve separate configuration fixtures or derive an explicit ULP envelope from the repeated old-binary captures. Do not derive a tolerance from the CPU result.

A compact fixture can use this shape:

```json
{
  "swiftMLRevision": "e19db7dda4567c425b7eb002da82e234e6c7980f",
  "mlxRevision": "<resolved old-checkout revision>",
  "configuration": "debug",
  "fixture": "routed-logistic-v1",
  "requestedDevice": "gpu",
  "resolvedDevice": "gpu",
  "epochs": 1,
  "weights": [
    { "decimal": 0.0, "floatBits": 0 }
  ],
  "bias": { "decimal": 0.0, "floatBits": 0 },
  "positiveProbabilities": [
    { "index": 0, "decimal": 0.0, "floatBits": 0 }
  ]
}
```

The zeros above are schema placeholders, not expected results.

## Decision after the old-binary capture

| Old versus new GPU result | Interpretation | Compatibility requirement |
|---|---|---|
| Same Float bits, or within an old-run ULP envelope | Prepared integration preserves the original GPU solver | Keep strict row/prepared same-route parity and use the old GPU fixture for absolute GPU behavior |
| Different at epoch 1 | The solver or dependency behavior changed before representation can matter | Compare exact dependency revisions and first-step parameters before attributing the change to prepared input |
| Same at epoch 1, different at epoch 4 | Later update, evaluation, or state publication changed | Compare per-epoch old/new parameter captures to locate the first divergence |
| Old NaN output is `[0.0, 1.0]` | Current observation is legacy behavior | Correct the NaN contract expectation |
| Old NaN output differs | Binary/toolchain behavior requires explicit version qualification | Preserve the captured supported configuration and document the version dependency |

No production change is justified by the current failures. The immediate evidence-gathering step is the isolated original-commit probe that the parent task is preparing.
