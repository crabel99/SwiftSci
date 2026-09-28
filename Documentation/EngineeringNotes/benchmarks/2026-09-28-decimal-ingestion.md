# Original-decimal ANOVA ingestion

The three remaining SwiftSci NIST original-decimal failures are resolved by preserving source decimal differences before binary64 conversion. The implementation is on `codex/apple-silicon-precision` at `3a31534e3604bb0eb516546b2f8ab898f1f87ccd`, based on `ede79c1ad3fda868d3661979360aaeed31dcbf9c`. Engineering evidence belongs only to `codex/engineering-notes`.

## Cause and implementation boundary

SmLs07, SmLs08 and SmLs09 contain small decimal variations around a large offset. Converting absolute observations to `Double` changes those variations. More accurate reductions cannot recover the discarded digits. The unchanged binary64 API correctly targets its supplied binary64 inputs.

The additive public API is `Stats.oneWayANOVA(decimalGroups: [[String]])`. It parses original ASCII decimal tokens, subtracts one common origin exactly, converts residuals to binary64, then calls the existing ANOVA. It does not infer caller intent, center groups independently, reconstruct decimal text from floats, change the ANOVA kernel or replace existing `Double` behavior.

A private decimal coefficient stores sign, digits and exponent. Inputs allow up to 38 significant digits and a normalized coefficient exponent from -128 to 127. The aligned subtraction needs at most 293 digits before a carry. Integer digit arithmetic handles signs, carries and borrows exactly. A residual needing more than 38 significant digits is rejected. Parsing and subtraction never silently round within this contract. The final residual conversion and ANOVA still have binary64 precision and range limits.

The limit bounds the new ingestion facility instead of introducing a general arbitrary-precision public number type. A reusable centered array and wider precision remain separate API design work. The first-observation origin is deterministic; callers with a very wide dynamic range can still need another numerical representation.

## Reproduced results

| Dataset | Before, converted absolute observations | After, exact decimal centering | Certified F |
|---|---:|---:|---:|
| SmLs07 | 21.000811887818774 | 20.999999999999996 | 21 |
| SmLs08 | 201.01300409594845 | 201.00000000000006 | 201 |
| SmLs09 | 2001.134926220951 | 2001.0000000000005 | 2001 |

The before and after probe calls the actual public API over original NIST source rows. An initial probe incorrectly split CRLF lines and was corrected before recording the baseline. Its crash is not a library fault.

An intermediate Foundation implementation passed the three NIST cases but failed the new range test. On this host, checked Foundation subtraction of a tiny term from a large value could discard information without causing the API to throw. Foundation's text parser also accepted trailing junk and rounded oversized coefficients. The final implementation uses strict Swift parsing and exact digit subtraction. The failing Release test is retained as evidence. Apple's [decimal subtraction documentation](https://developer.apple.com/documentation/foundation/nsdecimalsubtract(_:_:_:_:)) describes a potentially rounded operation, which is unsuitable as the sole proof of exact ingestion.

## Maintained certification and regression checks

The tested worker fingerprint is `80897d608cb0ed3619edc474317549cce82a60451e63674355833f54b1c15b11`. Its build record captures all source hashes and proves that the clean build snapshot matches the committed implementation. The record was produced before commit; the same source fingerprint was verified after commit.

| Check | Result |
|---|---|
| Release SwiftStats and SwiftForecast | 149 passed, 0 failed, 0 skipped |
| Benchmark controller tests | 147 passed |
| Original-decimal numerical profile | 19 of 19 passed; audit passed |
| Exact-binary64 numerical profile | 19 of 19 passed; audit passed |
| NIST univariate profile | 81 of 81 executions passed; audit passed |
| Independent 100-digit Decimal qualification | 300 of 300 passed |
| Python/SciPy original-decimal ANOVA | 11 of 11 passed |

Independent cases vary signs, origin size, decimal scale and unequal group sizes. Maximum relative F error was `2.7031652027484026e-14` against independently calculated original-decimal references. Separate checks exercise the supported exponent endpoints. Public tests also reject malformed tokens, excessive precision, exponent overflow and subtraction outside the exact contract.

All eleven original-decimal ANOVA fixtures now retain the original NIST tokens as strings. Their new operation is `nist-anova-decimal`; the separate `nist-anova` operation retains binary64 inputs. The generator reconstructs both from locked originals. Reference numbers, original source hashes, binary64 fixture bytes and tolerances remain unchanged. New references differ only in input identity. The worker receives no expected answers.

The full Python comparator profile has 17 passes and two Wampler least-squares failures. Wampler4 returns intercept `1.0000000028854616` and Wampler5 returns `1.0000003429656807`, each against `1.0`. The pre-patch Python worker reproduces both identical failures. They are separate from decimal ANOVA and were not repaired here. No passing certificate is claimed for that Python profile.

## Cost

In the single-sample diagnostic profile, SmLs09's 18,009 observations took 7.520375 ms with strict parsing, exact decimal centering, residual conversion and ANOVA included. The predecoded binary64 workload took 0.457333 ms. These have different input contracts; this is a cost illustration, not a throughput comparison. Existing binary64 callers do not pay for decimal ingestion.

JSON decoding is outside both measured operations. The Python decimal comparator includes its checked Decimal centering and conversion inside the measured operation before SciPy ANOVA. No GPU or arbitrary-precision ANOVA claim is made.

## Reproduction and evidence

The archive [decimal-ingestion/evidence.tar.gz](../archive/2026-09-28/decimal-ingestion/evidence.tar.gz) contains source snapshots, checksums, original and corrected probe output, independent qualification inputs, build logs, test summaries, benchmark requests and responses, run certificates, and the pre-patch Python failure reproduction. `MANIFEST.json` verifies each archive member.

Run the repository's `Benchmarks/Tools/build_nist_model_fixtures.py` with its pinned Python environment to reproduce fixtures. Run `test_numerical_fixtures.py` to check reconstruction and preservation of source tokens and reference values. Build the maintained worker from the recorded clean source snapshot, then run and audit `numerical-conformance`, `numerical-binary64` and `nist`. The public API guide and regression tests are included in the implementation commit; this report and raw evidence remain on the engineering-notes branch.
