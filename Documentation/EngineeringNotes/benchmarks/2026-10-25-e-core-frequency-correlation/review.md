# Capture-correlation review

## Verdict

The raw capture supports the narrow result: 600 telemetry reports overlap 240 identical-checksum, E-only native runs; 239 runs have full reconstructed coverage and one first-edge run has 84.37% coverage and is excluded from the coefficient. Across the four evaluated native clock-offset cases, hardware-frequency versus effective-rate correlation remains 0.9403–0.9838. Together with stable fixed work, this is credible evidence that E-cluster clock scaling materially contributed to the native loop’s timing variation during this capture.

## Material findings

1. **The clock alignment is plausible, with unresolved provenance and semantics.** The end-of-window model has a narrow 1.211 ms origin intersection, and the later live Mach/Unix bridge falls inside the 143.231 ms historical envelope. However, no bridge-producing program or hash is archived, and `capture-provenance.json` does not hash the telemetry, anchors, bridge, or correlator. The CoreFoundation receipt proves whole-second truncation during serialization, not where `powermetrics` takes its timestamp. The start model misses consistency by only 2.441 ms. State that it was attempted and rejected under the strict model; `correlation.json` currently overstates this as both interpretations being included in sensitivity. Four selected offsets, including both endpoints, do not constitute a continuous test of every admissible offset or the telemetry-origin endpoints.

2. **The test receipt is narrower than the archival replay.** The final correlator emits the saved duration and period fields, but the three tests cover only toy overlap and timestamp constraints. They do not replay the raw capture, assert bridge selection, exercise the four sensitivity cases, check partial-edge handling, or verify the output schema. `correlation-tests.log` also lacks its command, interpreter, and input hashes. This does not contradict the result, but it leaves end-to-end replay dependent on the instructions rather than a bound receipt.

3. **Keep the causal claim scoped to this fixed loop.** The stable work and independent hardware signal support frequency as a major contributor here. The 0.9838 coefficient still pools temporally ordered and overlapping runs, including concurrent workers that share telemetry windows and a cluster-wide average. It does not establish the sole cause of CPU duration, identify each worker’s instantaneous clock, explain wall-minus-CPU time, or isolate macOS policy. The plot title “Slower CPU timing follows lower hardware clock rates” should use “covaries with.”

4. **Thermal, SFI, and energy evidence is limited.** “Nominal” means reported thermal pressure was nominal at sampled endpoints; it does not exclude temperature-driven clock behavior. Every SFI window size is zero and no endpoint is nonzero; transient or per-process forced idle remains unmeasured because process wait times were not collected. Raw system energy estimates exist, but the analysis neither uses nor attributes them to workers, so it supports no energy conclusion.

5. **The scope boundary is correct.** The capture does not normalize, qualify, or repair the old benchmark. Its saved caveats should remain attached to every reported coefficient and figure.

## Attention

reviewed by gpt-5.6-sol

This is a saved-artifact review. No transcript verification was performed.
