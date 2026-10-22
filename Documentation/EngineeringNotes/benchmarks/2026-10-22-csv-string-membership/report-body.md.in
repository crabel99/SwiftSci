# CSV String lookup cost and prefix trials

This study follows the [optional-return investigation](../2026-10-22-csv-string-value-path/README.md), which found identical generated instructions for the hashed decoder rewrite. It measures String construction and null membership separately, then tests a generic negative membership filter.

## Decision

Retain the refined prefix implementation as an experimental candidate, alongside the cheaper preparation-only alternative. Do not promote an unconditional prefix filter. Its bulk benefit is substantial, but tiny files with large token sets do not amortize its preparation cost as well as cleanup alone.

The implementation checkout remains `codex/csv-local-batch-builder` at `c906c3fbbb0baf1357438a7079921a6448e0c9e5`, unchanged and clean. No implementation branch, production commit, push, or PR was created. Prototype sources, patches, controllers, and observations are preserved here on `codex/engineering-notes`.

## Questions and phase measurements

The ranked hypotheses were that membership dominates String-column cost, construction dominates, or short-read setup variation obscures the difference. An allocating replay tests four operations on the actual String fields: copy prepared values, match prepared values, parse raw fields, and parse then match. All four store optional Strings. Each output is checked against an independent native-value digest.

The replay uses six fresh processes per input and eight observations per operation and column within each process. Eighteen complete public reads and 1,152 recorded phase outputs validate. A separate pilot validates one public read and 64 phase outputs. Raw unfiltered String hashes come from Python CSV decoding and ASCII whitespace trimming. Null-filtered hashes remain the existing reference contracts.

The following table sums the per-column medians for each mode. These are diagnostic replay costs, not additive fractions of complete-read CPU. Parsing/index construction and preparation of decoded inputs occur outside phase timing. Replay storage and access order differ from production.

| Input | Copy CPU ms | Match CPU ms | Parse CPU ms | Parse and match CPU ms |
|---|---:|---:|---:|---:|
| Air quality, default tokens | 0.409 | 1.476 | 0.976 | 1.934 |
| All-String text, default tokens | 0.381 | 2.280 | 0.943 | 3.047 |
| Household, default tokens | 24.328 | 103.207 | 51.245 | 134.089 |

Membership is a useful target. Three diagnostic thread-stack profiles of repeated complete public reads also contain `String.hash(into:)`, `Hasher.combine(bytes:)`, and String conversion under the column conversion calls. Sampling starts after independent full native-output validation. Subsequent profile iterations check row totals and release each frame through a separate async function. Stack sample counts are not process CPU percentages or hardware counters.

See [per-column phase costs](phases.md), [complete-read summaries](phases/full-read-summary.json), and the preserved profile files.

## Filter and equality boundary

The initial filter prepares two `UInt64` masks from the leading bytes of null tokens. If every token is ASCII, a parsed value with a leading ASCII byte absent from those masks cannot be a token. It returns that String directly. Empty values, possible matches, and values with a non-ASCII leading byte use the original Set lookup. Any non-ASCII token disables negative rejection. String construction, trimming, unescaping, invalid-UTF-8 behavior, and output representation remain unchanged.

Swift String equality uses canonical Unicode equivalence. ASCII tokens remain unchanged under normalization. Our inference from the normalization rules is that a different leading ASCII starter cannot become an ASCII token's first character through canonical ordering. The filter rejects only that case and does not establish equality. See [Swift String comparisons](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/stringsandcharacters/) and [Unicode normalization](https://www.unicode.org/reports/tr15/tr15-58.html).

An independent semantic dataset includes every Unicode scalar, two ASCII-prefixed variants of each, and 17 additional multi-scalar, quoted, whitespace, and long-String rows. It contains 1,112,081 rows and 3,336,243 String cells. Four source variants each pass parallel and serial reads against the same native digests, for eight semantic workers. Python's Unicode reference version is recorded in the contract. This is broad scalar coverage, not proof over every possible multi-scalar string or a replacement for the project's full tests.

## Initial trial and rejected costs

The first complete-read matrix has 648 validated workers and no CPU or peak-memory review flags. A 448-worker follow-up retains the default-token reference gains but flags one serial high-null text case. Its CPU median increases by 10.9%. That flag remains recorded.

A focused repeat uses 32 fresh workers per implementation, policy, and read mode. Fresh and steady reads remain separate. Steady workers perform two warmups and five recorded reads, with output checks on every read. These 512 workers do not reproduce the high-null penalty; their high-null medians use 24.1% to 26.7% less CPU. They do reproduce a 3.1% to 4.8% empty-set cost. Neither result erases the earlier flag or explains the host-level timing variation.

An additional 256-worker matrix exposes setup cost on 8-row and 257-row files with zero, ten, 2,048, or 32,768 null tokens. The first filter has seven CPU review flags. Preparing its masks adds a token scan on top of the factory's unused byte-pattern preparation. On eight rows with 32,768 tokens, CPU grows from about 3.0 ms to 4.1 ms. This version is rejected for promotion.

## Subtract unused preparation before selecting a filter

`CSVColumnPlan.conversion` previously constructs `CSVNullMatcher` before switching on the selected type. String and Boolean decoders do not use it. The cleanup trial moves construction into the Integer, Double, and Date cases that consume it. String and Boolean choices avoid those unused byte-pattern arrays.

The refined filter includes that cleanup and returns the parsed String immediately when the token set is empty. It retains the existing one-token and two-token decoder. These changes introduce no new data cache, normalization rule, parser, batch bound, or concurrency policy.

The refined screen compares the frozen current binary, cleanup alone, and cleanup plus the filter. Its 648 workers validate complete native output. The following 576 setup-control workers also validate. Both matrices have zero CPU and peak-memory review flags against the frozen current implementation.

## Refined complete-read results

Each cell reports the median of six fresh processes. CPU is process user-plus-system time for a complete read plus output release. Elapsed time and peak RSS are preserved separately. Policies, input bytes, schemas, null tokens, native output types, null positions, and row and column order match within each comparison.

| Input and scope | Policy | Current CPU ms | Refined filter CPU ms | CPU change |
|---|---|---:|---:|---:|
| Household default tokens, eager | parallel | 513.370 | 402.779 | -21.5% |
| Household default tokens, eager | serial | 335.186 | 257.954 | -23.0% |
| Household default tokens, streaming | parallel | 475.457 | 379.002 | -20.3% |
| Household default tokens, streaming | serial | 320.231 | 241.524 | -24.6% |
| Air quality default tokens, eager | parallel | 12.932 | 12.398 | -4.1% |
| Air quality default tokens, eager | serial | 9.391 | 8.872 | -5.5% |
| All-String default tokens, no scheduled null injection | parallel | 3.844 | 2.241 | -41.7% |
| All-String default tokens, no scheduled null injection | serial | 4.247 | 2.199 | -48.2% |

The original household configuration uses two null tokens and already has its specialized decoder. Its refined CPU changes range from 1.3% lower to 1.6% higher. It has no demonstrated additional consistent benefit. Do not apply the default-token gains to that configuration or compare different configurations as equivalent workloads.

The largest refined-screen median peak-RSS increase is 0.72 MiB. Default-token household eager parallel peak RSS is 422.45 MiB before and 422.47 MiB after. RSS is a whole-process high-water mark, not an allocation count. This does not prove zero additional allocation. No FLOP, energy, cache, SRAM, or contention claim follows from these measurements.

See the [complete refined screen](refined-screen.md), [initial screen](screening.md), [follow-up](followup.md), and [fresh versus steady controls](edges.md). Every result and flag remains available.

## Why preparation still needs a selection rule

The refined filter beats the old implementation in the setup controls, but cleanup alone is cheaper when there is little data to process. This comparison matters even though neither refined candidate crosses a review trigger against the older baseline.

| Input | Policy | Current CPU ms | Cleanup CPU ms | Cleanup and filter CPU ms |
|---|---|---:|---:|---:|
| 8 rows, 32,768 tokens | parallel | 3.152 | 0.302 | 1.393 |
| 8 rows, 32,768 tokens | serial | 3.132 | 0.292 | 1.365 |
| 257 rows, 32,768 tokens | parallel | 3.231 | 0.429 | 1.488 |
| 257 rows, 32,768 tokens | serial | 3.256 | 0.418 | 1.429 |

For the last parallel case, peak RSS falls from 12.48 MiB to 10.95 MiB with cleanup and 10.93 MiB with the filter. The remaining filter preparation buys no useful speed on that workload. A baseline-only success criterion would miss this avoidable CPU work.

See [all refined setup results](refined-setup.md) and the [rejected initial setup results](setup-controls.md).

## Next implementation boundary

Select the decoder once at the existing column or batch boundary. Keep the original hashed decoder for empty sets, non-ASCII token sets, or inputs that cannot amortize preparation. Preserve the current small-set decoder. Use a separate prepared prefix decoder for eligible bulk work so fallback rows do not pay a feature-selection check. Establish a work-based preparation rule and test neighboring row-count and token-count cases before choosing its policy. Do not tune a threshold to the household fixture.

Only after that selection design is implemented should it receive actual-source-path compilation, bounded functional tests, Release, Debug, and sanitizer suites, the full reference/width/null/long-key matrices, grammar comparison, and the standard production-default benchmark audit. None of those production-qualification checks is claimed for these prototypes. The prior builder tests remain attached to their recorded head.

## Reproducibility and scope

The six resource stages retain 3,088 worker responses with native-output validation. The edge stage includes multiple reads per worker. Eighteen phase-study workers, one pilot, eight semantic workers, and three sampled profile runs are recorded separately. Repeated scalar data and replay observations are not counted as distinct scientific datasets.

All manual modules use the same optimized compiler flags and dependency objects. Fresh-process comparisons use matched `argv[0]`, AC power, warmed input bytes, native scheduling, and native hash randomization. Parallel compares with parallel and serial with serial. Build, semantic-check, profiling, and accepted timing stages run sequentially. No build or profiler overlaps resource timing. Unrelated host activity remains uncontrolled, and no observation is removed as an outlier.

- [Resource and semantic controllers](run-refinements.py)
- [Phase probe build receipt](PhaseProbe.build.json)
- [Source identity](source-state.json)
- [Unicode semantic results](semantics/summary.json) and [refined results](refined-semantics/summary.json)
- [Refinement stage status](refinement-status.json)
- [Source snapshots, patches, generated inputs, and contracts](experiments.tar.gz)
- [Artifact hashes](artifact-sha256.json)

Controllers retain original paths and hashes. Reference data remains with its existing dataset owner. The archive includes generated inputs and input contracts. Paths may be adapted on another checkout while retaining byte hashes, schemas, conversion policies, and output checks.
