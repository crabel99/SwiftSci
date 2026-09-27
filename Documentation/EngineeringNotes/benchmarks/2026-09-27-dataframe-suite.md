# Dataframe semantics and logical layout checkpoint

Local contribution commit `e5995732c253a83d9074e072481075fc7af9c2a2` adds 24 bounded dataframe cases and a CI step on `codex/standardized-benchmarks`. The contribution remains unpushed. It changes benchmark tooling, fixtures, tests and CI only. Production repairs remain deferred to a separate branch, one commit per error.

## What this increment establishes

The fixtures test Int64 extrema and neighboring integers above 2^53, nullable IEEE comparisons, stable sort ties with nulls last, component-wise grouping with null and separator text, functional replacement isolation and logical row-major exports. Matrix fixtures include nulls, repeated columns, empty column selection, non-square shape and intentional Int64-to-Double rounding.

The transport uses exact unsigned 32-bit words for 64-bit payloads and explicit presence tags. This avoids passing large integers through Double and avoids erasing the difference between a missing cell and present NaN. Every comparison has zero tolerance. A scalar reference independently computes expected operations, with literal hand-checked test answers for filtering, ordering, grouping and matrix layout. Input and answer bytes are pinned by manifests.

Pandas uses explicit compatibility conversions. Object columns retain None separately from NaN and full-width integers; nullable grouping keys retain typed identity. Empty results follow the existing Swift schema-less contract. This is conformance to a declared API, not a benchmark of pandas defaults.

## Validation

- 97 controller tests passed after final fixture regeneration.
- Release build succeeded with coverage instrumentation absent in the build record.
- Final dataframe run `suite-dataframe-02` passed all 48 engine cases and 96 measured samples.
- Both workers passed 14 unchanged controls and rejected all 64 wrong-answer or malformed/changed-input controls. This includes actual rejection of floating JSON gather indices, Boolean indices, negative indices and Int64 overflow.
- The existing smoke profile passed 28 engine cases and 28 measured samples.
- Final dataframe and smoke certificate audits passed.
- All 342 compiled source files match the contribution commit. Source fingerprint `3ac56155fd6a870de796da8e60acc5c63056b92ad374e23e7735c48b638e98be`.

The negative controls used `suite-dataframe-01` request files. A final wording correction changed the generator and reference provenance hashes, so the complete dataframe profile was rerun as `suite-dataframe-02`. Every input hash and expected binary-answer hash remained identical. The negative controls therefore exercise the same worker, input and answer bytes as the final run. Earlier logs remain archived without replacement.

The development build record names the parent HEAD. The separate commit verification compares each recorded source hash with the committed file bytes; it does not rewrite the build record.

## Review and corrections

The gpt-5.6-sol review found a missing profile allowlist entry, a mismatch in JSON gather-index typing, and ambiguous use of finite to describe fixtures containing infinities and NaN. All were corrected. The profile test now calls the real loader. Swift rejects floating NSNumber indices before integer conversion. Fixture prose uses bounded cases.

The review had repository artifacts and the decision trail, but no complete transcript. It cannot claim a transcript audit. Private notes and cloud-sync duplicate files are absent from the contribution commit.

## Limits and next work

These cases establish logical outputs and isolation for built-in TypedColumn values. They do not establish physical buffer layout, Arrow zero-copy behavior, GPU execution, allocation efficiency, or deep-copy guarantees for custom reference columns. NaN sorting remains outside the declared ordering contract. Int32 and Float32, broader mutations, invalid public API error cases and working-set sweeps need separate coverage.

No production defect was found by this bounded pack, and none was repaired here. Earlier numerical failures remain preserved. These diagnostic timings do not establish the formal performance baseline.

Next, add fixed neural forward-pass fixtures with explicit dtype, weights, device and execution-completion rules. Then complete integration coverage and review the suite gates before beginning the separate production-repair branch. The full dataset strategy is still in progress.
