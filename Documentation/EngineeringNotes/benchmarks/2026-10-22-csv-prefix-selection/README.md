# CSV null-prefix selection and its resource limits

The selected decoder passes functional validation and reduces CPU on large default-token reference reads. It is **not approved for promotion**. Boundary controls retain CPU regressions against cleanup alone, including repeated-read observations. A metadata-preflight alternative does not resolve them consistently. No review tolerance changed and no flag was waived.

## Source and delivery state

The parent is `c906c3fbbb0baf1357438a7079921a6448e0c9e5` on `codex/csv-local-batch-builder`. It remains intact. The local child branch is `codex/csv-prepared-string-membership`.

- `f9a99ce54c77909bdd6f95fadd5fa3b5d15490f2` removes unused `CSVNullMatcher` preparation from String and Boolean choices. Integer, Double, and Date construct the matcher they consume. This commit independently passes 391 Release tests.
- `167d9a4e6f8cb923342dea3236721c8722015bf3` selects a separate bounded ASCII prefix decoder at the existing column-attempt boundary. This is the tested experimental head, not a qualified production change.

The source worktree is clean. Neither commit was pushed and no PR was opened. All reports, research, raw results, and design sketches belong to this engineering-notes branch. The source changes contain only implementation and regression tests. See [source identity](source-state.json), [cleanup patch](cleanup.patch.gz), [selected-decoder patch](selected.patch.gz), and [decision](decision.json).

## Design and alternatives

The subtraction comes first. String and Boolean conversion do not consume the byte-pattern matcher previously prepared before the type switch. Removing that work also avoids making a new filter compete against an unnecessarily expensive baseline.

The selected design adds one concrete decoder and one case to `CSVColumnConversion`. Empty sets retain hashed lookup. One-token and two-token sets retain their existing equality decoder. Larger ASCII-only sets can prepare two `UInt64` masks of possible leading bytes. Impossible ASCII starts skip Set membership. Possible matches, empty values, and non-ASCII-leading values retain the original native String equality check. Parsing, trimming, unescaping, output representation, and invalid-UTF-8 behavior do not change.

Selection happens once per attempt. Eager reads supply the exact selected total, retries reuse that total, streaming supplies actual chunk rows, and single-field probes supply one. The internal argument is named `selectedRowCount`; eager `Initial.totalRows` no longer presents that work count as an allocation hint.

The first policy precharges token visits, then scans bytes within the remaining row-derived budget. Accepted preparation fits token count plus byte count within selected rows. A rejected scan may still walk most of the tokens before returning to hashed lookup. This bounds work but does not establish a CPU-optimal crossover.

A byte-only snapshot tests the cost of a looser budget. A later preflight snapshot checks native UTF-8 storage and byte lengths before validating ASCII. It budgets two token traversals plus byte visits, with overflow-safe subtraction. Foreign storage falls back without forced conversion. [Swift's storage predicate](https://developer.apple.com/documentation/swift/string/iscontiguousutf8) and [UTF8View.count implementation](https://github.com/swiftlang/swift/blob/main/stdlib/public/core/StringUTF8View.swift#L292-L299) support the guarded metadata path. The installed SDK implementation and its hash are preserved in [toolchain evidence](design/stdlib-storage-evidence.txt).

The preflight snapshot is an experiment. It has grammar and native-output resource checks, not the selected source head's complete test qualification. It was not copied into production sources.

The [architecture grounding](design/how.md), [independent alternatives](design/separate/rationale.md), [second alternative](design/unified/rationale.md), [judge](design/judgement.md), and [selection record](design/synthesis.md) preserve the reasoning. The judge preferred separate token and byte ceilings. The implemented first policy uses the stricter combined budget; that choice remains a hypothesis under evaluation.

## Functional verification

The selected source head passes all 394 DataFrame tests in each of Release, Debug, and Address Sanitizer, with no failures or skips. The new tests are 50 and 37 lines, with explicit types and small expressions. They cover exact budgets, unsuitable token sets, saturated masks, owned values, canonical String equality, invalid UTF-8, quotes, whitespace, and eager/streamed selection boundaries.

All four manual variants pass the same 30,720-case grammar digest. The selected source validates 3,336,243 String cells in each scheduling policy against independent native-value hashes. The Unicode fixture includes every scalar, two ASCII-prefixed variants, and additional multi-scalar cases. This is not proof over every possible String.

The uninstrumented production-default `tabular-smoke` run produces 190 SwiftSci and pandas responses and passes its audit. This is the profile's regression-policy result, not full numerical certification. Results for one head do not validate another head.

The independent [standards review](design/standards-review.md) finds no documented violations or actionable smells. The independent [specification review](design/spec-review.md) finds no actionable implementation gap and explicitly leaves resource qualification pending. The later [preflight review](design/preflight-review.md) recommends a trial, not promotion.

## Reference-data CPU and memory

Each median uses eight fresh workers per implementation and scheduling policy. Comparisons match input bytes, schema, null tokens, native types, values, null positions, and order. CPU is process user-plus-system time for read and output release. Validation is outside timing. Elapsed time remains separate in the [complete reference table](acceptance.md).

| Input and scope | Policy | Parent CPU ms | Candidate CPU ms | CPU change | Peak RSS before / after MiB |
|---|---|---:|---:|---:|---:|
| Aotizhongxin-default, eager | parallel | 12.393 | 11.701 | -5.6% | 23.15 / 23.11 |
| Aotizhongxin-default, eager | serial | 9.178 | 8.484 | -7.6% | 22.88 / 22.84 |
| energy-default, eager | parallel | 509.538 | 426.428 | -16.3% | 422.41 / 422.45 |
| energy-default, eager | serial | 323.307 | 249.047 | -23.0% | 420.56 / 421.09 |
| energy-default, stream | parallel | 495.773 | 382.808 | -22.8% | 139.20 / 139.23 |
| energy-default, stream | serial | 294.892 | 223.925 | -24.1% | 137.67 / 136.50 |

The largest median peak-RSS increase across the four broad matrices is 1.42 MiB. No memory review threshold is crossed. RSS is a process high-water mark, not an allocation count. These results establish no FLOP, energy, cache, SRAM, or contention claim.

The gains above apply to default-token configurations. The household fixture's original two-token configuration already uses its specialized decoder. Do not attribute default-token gains to a different configuration.

## Boundary evidence prevents promotion

The 84 generated contracts vary three, ten, and 64 null tokens, short and long tokens, zero and high null injection, and row counts around both byte-only and combined budgets. Eager and streamed comparisons use both native scheduling policies. Boundary streams use the contract's selected row count as chunk size; broad reference streams keep 10,000 rows. A streaming boundary comparison is never paired with a different chunk bound.

The first boundary matrix has 22 CPU review flags. Six belong to the byte-only alternative and 16 belong to the selected candidate. The same source candidate has no flags in the 2,432 broad reference, width, numeric-null, text-null, and long-key workers. Those broad successes do not erase the boundary failures.

The follow-up compares cleanup, the selected candidate, and metadata preflight on every flagged scope/input pair plus real reference data. All 1,656 workers validate. Four CPU flags remain, two for the selected candidate and two for preflight. Some initial flags do not recur; the two recurring streamed inputs remain material.

A separate 1,440-worker study uses two warmups and five recorded reads per worker. Eager reads validate every result outside timing. Streams check every row total, then perform a separate full native-output validation. Each worker contributes its median, so repeated reads are not counted as independent workers. Peak memory includes preceding warmups. Nine selected-candidate and four preflight CPU flags remain. Some preflight increases exceed 30%, so metadata admission cannot be called a demonstrated fix.

These observations support two separate facts. Failed preparation performs avoidable work. Preparation alone has not been shown to explain every CPU difference, because the alternative still regresses. No internal runtime or hardware mechanism is proven. Do not tune a row threshold to hide these cases.

See [boundary results](crossover.md), [small-file setup controls](setup.md), [preflight follow-up](preflight-screen.md), and [repeated-read results](steady-boundaries.md). Raw worker records and every review flag remain in their matching folders.

## Evidence inventory and next boundary

| Resource stage | Workers |
|---|---:|
| acceptance | 608 |
| mode-controls | 544 |
| text-controls | 1024 |
| long-key-controls | 256 |
| crossover | 6048 |
| setup | 576 |
| preflight-screen | 1656 |
| steady-boundaries | 1440 |

The resource stages retain 12,152 validated worker responses. Unicode semantic workers and the 190 standard responses are separate. Workers and repeated reads are not distinct scientific datasets.

All accepted timings run after builds, tests, and grammar checks finish. Input bytes are warmed. Power is AC, CPU scheduling is native, and parallel compares with parallel while serial compares with serial. Screening uses matched executable names. No outlier is removed. Unrelated host activity is not controlled.

The next experiment must separate constructor cost from the unchanged hashed fallback loop on recurring cases. It must retain fresh and repeated reads separately. Neither moving the budget nor adding another pass is justified solely by a plausible cost model.

- [Qualification controller](run-qualification.py) and [stage receipts](qualification-status.json)
- [Final resource decision](decision.json)
- [Width and numeric-null controls](mode-controls.md), [text-null controls](text-controls.md), and [long-key controls](long-key-controls.md)
- [Standard audit artifacts](standardized/)
- [Unicode semantic results](unicode-semantics/summary.json)
- [Source snapshots, build receipts, generated boundary inputs, and logs](experiments.tar.gz)
- [Artifact hashes](artifact-sha256.json)

Controllers preserve original paths and hashes. Shared reference datasets remain with their existing owner. Earlier source snapshots and Unicode input generation are retained in the [preceding String-membership study](../2026-10-22-csv-string-membership/README.md).
