# Predeclared CPU counter evidence

The benchmark now records its analysis method before collecting a new comparison and reports CPU work beside throughput and memory. The implementation changes benchmark tooling only. The existing timed controller, production Swift code, and acceptance limits are unchanged.

This follows the [E-core frequency investigation](../2026-10-25-e-core-frequency-correlation/README.md). That investigation observed real clock-rate changes during a fixed native loop. This work makes the queue accounting easier to inspect without claiming that a derived counter rate independently measures hardware frequency.

## Implementation

The local source branch is `codex/cpu-operating-state-evidence`, based on `117dc92a64cfca3d15aea1dc268d4ed5a7b317e8`. Its tested head is `06adea701994f8fbbe82481684dfdafd77958a09`. See the [implementation patch](implementation.patch) and [source commits](source-commits.txt). Two commits add the analyzer, collection wrapper, six focused tests, protocol reference, and explanatory P-kernel caveat. Nothing was pushed or submitted.

The `--collect` wrapper writes `method.json` before invoking the existing observer-isolated controller. It records the command, source head, analyzer and protocol definitions, controller fingerprints, core profile, original quality limits, and capture location. After collection, it checks the unchanged manifest and its agreement with the measured plan before writing diagnostics.

The analyzer reruns the complete existing audit in a temporary directory. Every saved capture file remains unchanged. Worker counts are summed before division and stay separate from controller counts. Total-minus-P counters define E-core work. Worker P-core counts describe permitted kernel work because P-core user time must remain zero.

The report presents both primary and twin resource measurements, instructions, cycles, accounted rates, and all original control failures. It adds no rate threshold, timing normalization, automatic causal classification, energy estimate, or library ranking.

## Final verification

| Check | Result |
| --- | --- |
| Clean source controller suite | 275 passed, no skips |
| New focused tests | 6 |
| Completed predeclared smoke | 24 queues, 192 jobs |
| Full native-bit checks | 48 passed before and after timing |
| Worker application placement | Zero P-core user time in all timed workers |
| Observation coverage | All queues passed |
| Largest observation gap | 19.428 ms |
| Longest scan | 2.520 ms |
| RSS twin controls | All conditions passed |
| CPU and elapsed-time controls | Five failures retained |
| Comparative performance qualified | False |
| Replayed diagnostics | Equal to saved diagnostics |
| Immutable new capture files | 143 verified |
| Recorded worker/controller PIDs | 109 absent after completion |

The five control failures belong to SwiftSci optional CPU and elapsed time, SwiftSci compact elapsed time, and Polars CPU and elapsed time. Their exact ratios remain in the original audit and diagnostic report. A smoke panel cannot qualify comparative performance even if every control passes.

The separate retrospective replay preserves all eight failures from the previous observer-isolation smoke. Its 143 original capture files also remain unchanged. A real altered P-user counter is rejected, as is an attempt to write diagnostics inside the capture.

Different failure counts between the two smokes do not establish improved repeatability. The timed code and thresholds did not change. This is one integration run, not repeated selection for a favorable result.

## Evidence and limits

Read the [predeclared diagnostic report](declared-report.md) with the [original comparison report](comparison-report.md), [original audit](audit.json), [pre-run method](method.json), and [live replay and cleanup receipt](declared-smoke-verification.json). The [final test receipt](final-test-provenance.json) binds the clean source, interpreter, command, source fingerprints, and log. The [retrospective report](retrospective-report.md) remains explicitly retrospective.

The original review identified missing resource context, missing pre-run declaration, and stale intermediate receipts. The final report includes resource context and the live path exercises predeclaration. The authoritative verification is `final-controller-tests.log`, `final-test-provenance.json`, `declared-smoke-verification.json`, and `integrity-verification.json`. Earlier test logs in the experiment directory describe intermediate work and are not the final validation.

Cycles per CPU nanosecond shares a denominator with CPU time. Its relationship with CPU timing is not independent evidence of clock scaling. These queue receipts have no concurrent direct frequency trace, and the earlier fixed-loop capture cannot assign hardware states to them. Instruction mix, cache behavior, and scheduling can also affect the observed quantities. Near-zero P-core work makes its ratios unstable.

The next measurement is a full balanced panel under the frozen method. It must retain its failures and all attempted panels. These smoke results establish no comparative baseline.

The engineering archive preserves raw receipts, the reviewed source, the local patch, test evidence, and the decision trail. Archive integrity and source fingerprints support review. Full audit replay still requires the recorded source checkout, executable, interpreter, native calibration library, and external reference inputs. The predeclared capture location is part of the method, so relocating it is not a transparent replay. See [replay instructions](REPLAY.md), [review](review.md), and [review disposition](review-disposition.md).
