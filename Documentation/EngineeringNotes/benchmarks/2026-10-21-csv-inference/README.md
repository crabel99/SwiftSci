# Validate CSV inference beyond its sample

Local branch `codex/csv-inference-validation` fixes silent loss of values after the CSV inference sample. Commit `548a783f02678c95c027a733e3cbd51df363dc47` is based on the compact parser integration at `2be6fc01a80d520d637f85f9f4bbde0a855e309b`. This report remains on `codex/engineering-notes`, outside the production branch.

All twelve original Beijing air-quality station files now pass numeric inference against the independent oracle. The repair restores 398 fractional measurements across 23 columns. All 26 supplied-schema and numeric-inference cases pass. The separate ambiguous-date interpretation defect remains unchanged.

## Cause and repair

The reader sampled up to 1,000 rows and treated the resulting type as authoritative. An integer sample followed by a fraction produced null for that fraction. The same conversion loop could discard later text after a numeric, Boolean, or date sample. Explicit type overrides intentionally retained this conversion-failure behavior, but automatic inference was silently losing data.

The sample now selects candidate types. Each existing conversion loop validates its candidate against all requested rows. A parse failure that is not a configured null rejects the candidate. The partial builder stays within the rejected candidate's scope. The next candidate reads the original field bytes. A later fraction can select Double; text that fits none of the typed candidates retains its original strings. Missing fields and configured null tokens remain null.

Successful typed inference keeps its existing conversion pass and adds a validity check. A rejected candidate can require another pass and another column allocation. There is no unconditional full inference scan, new public option, dependency, or generic parsing abstraction. Explicit type overrides and `inferTypes = false` remain unchanged. The existing numeric conversion rules still govern Double rounding; this is not arbitrary-precision ingestion.

Streaming continues to infer each chunk independently. This change does not establish one schema across all chunks. An all-null initial sample still follows the existing String-column path. Date text that parses successfully to the wrong ambiguous date is outside this repair.

## Failing-before and passing-after evidence

The new `CSVInferenceValidationTests` exercises a fraction after 1,000 integers through full-file and streaming reads, both quoted and unquoted. It also places text after integer, Double, Boolean, and date samples, verifies original leading-zero text, and checks explicit integer override behavior.

Before the production fix, two new test functions failed across six parameterized cases. The Debug target reported 340 passes and two failures. The explicit-override test passed. The first test launch had a missing Swift argument label in the new fixture; that compilation error was corrected before recording the actual failing-before run.

After the fix, the new tests passed. One old test still required late text to become a missing integer. That assertion documented the behavior being repaired, so it was replaced with stronger checks for every original prefix string, the final text value, and zero nulls. Explicit override tests still require conversion failures to be null.

| Validation | Result |
|---|---|
| Full SwiftDataFrame Debug target | 342 passed, zero failures or skips |
| Full SwiftDataFrame Release target | 342 passed, zero failures or skips |
| Added executable production lines | 31 of 31 covered locally |
| Standard tabular smoke, SwiftSci and pandas | 190 validated samples across 19 cases and five process rounds |
| Standard certificate audit | Passed |
| Original-file supplied schemas | 13 of 13 pass |
| Original-file numeric inference | 13 of 13 pass; energy timestamps explicitly retained as text |
| Existing date-prefix diagnostic | Fails identically to the previous head |

The original-data oracle checks row and column order, null positions and counts, exact UTF-8 strings, and binary64 numeric hashes. Energy numeric inference supplies the same Date and Time text overrides as the prior experiment. It is not full timestamp inference. Provenance, licenses, and the original files are documented in the [reference-data comparison](../2026-10-21-csv-reference/README.md).

## Resource cost on already-correct reads

Only cases that pass the independent oracle before and after the repair enter this comparison. The old station-inference failures are excluded; dropping valid measurements cannot count as efficient work. This test measures the cost of validation on existing correct reads, not a speedup from the repair.

The previous integrated parser and repaired parser use identical probe bytes, dependency objects, compiler settings, input files, schemas, and validators. Runs alternate process order across six timing rounds. Each timing worker has two warmups and three samples. Three separate memory rounds use one read per fresh process. There are 72 workers, 144 timing samples, and 24 memory samples, all validated. Builds and tests finish before timing. AC power is checked at both ends, CPU parallelism is native, and normal desktop activity is retained.

Times include public read plus output release. Validation is excluded and runs after the held-memory snapshot. CPU time is user plus system time, not FLOPs or energy. Process peak RSS and retained output heap are separate measures. Inputs are page-cache warm. Duration columns are medians of worker medians; percentage changes use paired within-round ratios.

| Original file / schema | CPU ms, before → fixed | Paired CPU change | Elapsed ms, before → fixed | Peak RSS MiB, before → fixed | Held heap MiB, before → fixed |
|---|---:|---:|---:|---:|---:|
| energy / known | 581.96 → 624.91 | +18.9% | 158.79 → 172.06 | 720.16 → 720.16 | 285.06 → 285.06 |
| energy / infer | 554.32 → 588.81 | +0.9% | 148.65 → 148.26 | 720.22 → 720.20 | 285.06 → 285.06 |
| Aotizhongxin / known | 11.70 → 11.52 | -1.5% | 5.60 → 5.61 | 25.70 → 25.72 | 9.86 → 9.86 |
| Wanliu / known | 11.57 → 11.56 | -2.4% | 5.71 → 5.62 | 25.53 → 25.53 | 9.86 → 9.86 |

The initial supplied-schema energy run is unstable: its paired CPU ratios range from 0.89 to 1.59, with a median increase of 18.9%. The numeric-inference energy run has a median CPU increase of 0.9%; the station controls are slightly lower. All retained-memory medians are unchanged. The first run is retained in full. A separate identical-binary control tests whether the large-file slowdown repeats. Individual ratios and ranges are retained in the archive. Tiny standardized smoke timings are not used as production performance evidence.

### Identical-binary control

The follow-up uses the unchanged executable under two labels alongside the fixed executable. All six permutations run once, with two warmups and three measured reads per fresh process. The eighteen workers and 54 samples all pass the original oracle, on AC power. No source changes or cooldown waits intervene.

The identical-binary CPU ratio has median 1.0026 and range 0.9809 to 1.0138. The fixed/before CPU ratio has median 0.9931 and range 0.9798 to 1.0118. Fixed/before elapsed time has median ratio 0.9638, versus 0.9987 for the identical-binary control. The CPU ranges overlap; the initial 18.9% increase does not repeat. This supports no persistent CPU regression in this follow-up, not a useful speedup or a proven explanation of the earlier window. Both runs are retained. The cause of the initial variability remains unproven, and no production code was changed in response to it.

## Review and remaining work

Manual review checked that only inferred typed conversions reject candidates, that configured nulls remain accepted, that retries use original bytes rather than converted values, and that partial builders leave scope before the next type allocation. The public options documentation explains widening and the unchanged explicit-override behavior. The tests are small and explicitly typed.

The next separate repair is date interpretation. This branch is committed locally but has not been pushed or submitted as a PR. Hosted CI, its compiler version, and the full SwiftSci all-module suite have not run on this head. The local tests and benchmark worker used Swift 6.4 and Xcode 27.0 on Apple silicon. The reference probe targets macOS 14. Address Sanitizer was not repeated for this repair, which changes no pointer or ownership implementation; the parent integration's sanitizer evidence remains in its own report.

## Evidence

- [Evidence archive](evidence.tar.gz): failing/passing test receipts, coverage, production patch, source fingerprints, original-data validation, restored-measurement inventory, standard benchmark requests/responses and certificate, and resource measurements.
- [Archive manifest](evidence-sha256.json): SHA-256 for every archive member and the archive.
- [Compact parser integration](../2026-10-21-csv-integration/README.md): parent implementation and validation.
- [Original reference comparison](../2026-10-21-csv-reference/README.md): dataset attribution, oracles, and failure inventory before this repair.

Scripts retain the exact local cache paths used for replay. Dataset bytes, compiled binaries, Xcode result bundles, and caches are not committed. This is recorded local evidence, not a new portable benchmark command.
