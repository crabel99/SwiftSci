# Testing and certification suite completion

Local contribution commit `ab7aa2f1dab7256eed5de177fb5060a25740c643` completes the four agreed remaining implementation items. The branch `codex/standardized-benchmarks` remains local and unpushed. Production implementations were not changed.

## Delivered scope

- Eight analytic vision preprocessing fixtures exercise the actual public API, normalized-value preservation, CHW-to-NHWC conversion, grayscale expansion, constant-plane resize and padding. Arbitrary Lanczos interpolation and raw-byte normalization remain outside this contract.
- Six dataframe-to-tensor fixtures cover row IDs through filter/sort, reordered features, aligned targets, non-square shapes, CPU Float32/Float64, GPU Float32 and mutation isolation. They execute MLX affine arithmetic after real dataframe conversion, not an estimator-training API.
- Fifty-four bounded sweeps cover three row sizes, two widths, three supported device/precision pairs and conversion, prepared computation and pipeline stages. The largest source feature payload is 4 MiB. This is measurement infrastructure, not a machine-memory saturation study or formal performance baseline.
- The acceptance policy assigns all 22 canonical profiles to CPU, explicit Apple-silicon or sweep tiers. The runner continues after failed profiles, verifies complete requests and independently reconstructed expected bytes, freezes source/specification identities, and reports infrastructure failures separately. CI runs the CPU tier and retains evidence even when a profile fails.

## Verification

All 135 controller tests passed. The integrated Release worker built successfully. Every one of its 359 recorded source hashes matches the contribution commit. Initial vision and boundary checks passed all 16 and 12 engine cases, respectively, with strict certificate audits. Actual-worker controls passed all 12 unchanged cases and rejected all 72 intentionally malformed inputs or wrong expected answers.

The final all-tier run has complete coverage of all 22 profiles. It records 1,132 engine-case executions: 1,102 passed and 30 failed. No missing evidence or infrastructure errors were accepted as numerical outcomes.

| Profile | Passed executions | Failed executions | Status |
| --- | ---: | ---: | --- |
| boundary-sweep | 108 | 0 | passed |
| vision-conformance | 16 | 0 | passed |
| boundary-conformance | 12 | 0 | passed |
| boundary-cpu-conformance | 8 | 0 | passed |
| certification | 54 | 0 | passed |
| controlled-conformance | 17 | 3 | failed |
| dataframe-conformance | 48 | 0 | passed |
| extended | 84 | 0 | passed |
| migration-smoke | 72 | 0 | passed |
| migration | 216 | 0 | passed |
| model-conformance | 5 | 1 | failed |
| neural-conformance | 23 | 1 | failed |
| neural-cpu-conformance | 10 | 0 | passed |
| neural-loader-conformance | 2 | 2 | failed |
| nist | 162 | 0 | passed |
| numerical-binary64 | 28 | 10 | failed |
| numerical-conformance | 25 | 13 | failed |
| public-data | 66 | 0 | passed |
| public-smoke | 22 | 0 | passed |
| smoke | 28 | 0 | passed |
| standard | 84 | 0 | passed |
| supervised-conformance | 12 | 0 | passed |

A failed profile remains failed and cannot issue a passing certificate. Completing the test infrastructure is separate from all production operations passing it. Held-out quality, numerical conditioning and exact implementation conformance remain distinct claims.

## Preserved failures

- `controlled-conformance` / `controlled-linear-fixed-affine` / `swiftsci`: Model must be fitted before calling predict or transform.
- `controlled-conformance` / `controlled-logistic-fixed-mixed-logits` / `swiftsci`: Model must be fitted before calling predict or transform.
- `controlled-conformance` / `controlled-cosine-small-norm` / `swiftsci`: Output mismatch: 0.0 versus 1.0
- `model-conformance` / `pca-oblique-k1` / `swiftsci`: Output mismatch: 1.0 versus 0.8
- `neural-conformance` / `neural-gpu-rope-cached` / `swiftsci`: Output mismatch: -0.024063661694526672 versus 0.0425054856361493
- `neural-loader-conformance` / `neural-cpu-public-loader` / `swiftsci`: Decoder parameter was not replaced exactly: layers.0.attention.key_proj.weight
- `neural-loader-conformance` / `neural-gpu-public-loader` / `swiftsci`: Decoder parameter was not replaced exactly: layers.0.attention.key_proj.weight
- `numerical-binary64` / `nist-atmwtag-binary64` / `swiftsci`: Output mismatch: 15.946733593790675 versus 15.946733566676926
- `numerical-binary64` / `nist-smls04-binary64` / `swiftsci`: Output mismatch: 21.000000038029 versus 21.0000000007761
- `numerical-binary64` / `nist-smls06-binary64` / `swiftsci`: Output mismatch: 2000.9999826583844 versus 2001.0000001288329
- `numerical-binary64` / `nist-smls07-binary64` / `swiftsci`: Output mismatch: 21.03988962187173 versus 21.00081188781877
- `numerical-binary64` / `nist-smls08-binary64` / `swiftsci`: Output mismatch: 200.89125346619366 versus 201.01300409594845
- `numerical-binary64` / `nist-smls09-binary64` / `swiftsci`: Output mismatch: 1983.9428610886403 versus 2001.1349262209505
- `numerical-binary64` / `nist-wampler4-binary64` / `swiftsci`: Output mismatch: 0.9999999966334049 versus 1.0
- `numerical-binary64` / `nist-wampler4-binary64` / `pandas`: Output mismatch at 0: 1.0000000028854616 != 1.0
- `numerical-binary64` / `nist-wampler5-binary64` / `swiftsci`: Output mismatch: 0.9999996723182715 versus 1.0
- `numerical-binary64` / `nist-wampler5-binary64` / `pandas`: Output mismatch at 0: 1.0000003429656807 != 1.0
- `numerical-conformance` / `nist-atmwtag-decimal` / `swiftsci`: Output mismatch: 15.946733593790675 versus 15.946733567793
- `numerical-conformance` / `nist-smls04-decimal` / `swiftsci`: Output mismatch: 21.000000038029 versus 21.0
- `numerical-conformance` / `nist-smls06-decimal` / `swiftsci`: Output mismatch: 2000.9999826583844 versus 2001.0
- `numerical-conformance` / `nist-smls07-decimal` / `swiftsci`: Output mismatch: 21.03988962187173 versus 21.0
- `numerical-conformance` / `nist-smls07-decimal` / `pandas`: Output mismatch at 0: 21.000811887818774 != 21.0
- `numerical-conformance` / `nist-smls08-decimal` / `swiftsci`: Output mismatch: 200.89125346619366 versus 201.0
- `numerical-conformance` / `nist-smls08-decimal` / `pandas`: Output mismatch at 0: 201.01300409594847 != 201.0
- `numerical-conformance` / `nist-smls09-decimal` / `swiftsci`: Output mismatch: 1983.9428610886403 versus 2001.0
- `numerical-conformance` / `nist-smls09-decimal` / `pandas`: Output mismatch at 0: 2001.134926220951 != 2001.0
- `numerical-conformance` / `nist-wampler4-decimal` / `swiftsci`: Output mismatch: 0.9999999966334049 versus 1.0
- `numerical-conformance` / `nist-wampler4-decimal` / `pandas`: Output mismatch at 0: 1.0000000028854616 != 1.0
- `numerical-conformance` / `nist-wampler5-decimal` / `swiftsci`: Output mismatch: 0.9999996723182715 versus 1.0
- `numerical-conformance` / `nist-wampler5-decimal` / `pandas`: Output mismatch at 0: 1.0000003429656807 != 1.0

These results belong in the separate repair and numerical-analysis phase. Do not automatically label strict decimal-versus-binary64 coefficient differences as algorithm defects without examining conditioning. Retain one commit per diagnosed production error. Establish the formal performance baseline only after the relevant completed suite passes.

## Provenance and review

Source tree fingerprint: `dfdc1bc7facd9e1aea483897ddaa534991f44f1e32a9b4a25fd09e3a464b8146`.
Frozen fixture/specification fingerprint: `7f4c969ba78bd6bf2c2068f5eadac2fa3fe0dd0ccf912a3b4893c114cf4ef0f8`.
Acceptance report SHA-256: `42060e498758e4d82ded8ba39ebedb2223026c105fc2d6bee4369eaa867acb72`.

The archive contains raw runs in a hash-verified compressed tar, member hashes, worker requests/responses, profile certificates, control probes, build identity, controller logs, review and the decision trail. Each profile in the final run uses the same source commit and tree identity. The final build record names the final contribution commit, and its 359 exact source-file hashes match that commit.

The first full acceptance run exposed an audit contract error: the generic Python worker records zero memory on a failed calculation, but the auditor required positive memory even for failures. A failing regression test reproduced this. The correction accepts nonnegative integer memory only on failed responses, while malformed fields and passed-response memory checks remain strict. All profiles were rerun after the correction.

The initial preparation attempt during the Release build was rejected by the benchmark lock. It produced no runtime claim. Snapshot creation copied the repository's generated documentation and took several minutes; the build then succeeded. This was recorded without changing the production build inputs.

The independent reviewer used gpt-5.6-sol and reviewed artifacts rather than an unavailable full transcript. See [the independent review](../archive/2026-09-27/suite-completion/review.md) for the final verdict. Hosted GitHub execution was configured but not run here; the CPU tier executed locally as part of the all-tier acceptance run. Kiraa remains an unofficial research reference, never a correctness oracle.
