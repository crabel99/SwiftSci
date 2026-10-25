# Evidence trail review

This was a review of saved logs, JSON receipts, scripts, and reports. No active `agent-transcripts` directory exists, so no transcript review was performed and model-attribution claims cannot be independently reconstructed from transcripts.

## Supported claims

- The final smoke artifacts support 24 queues, 192 timed jobs, 48 before/after hash checks, and 96 worker intervals whose strict audit receipts report zero P-core user time. The saved verification replays coverage, scan-gap, RSS, hash, role-accounting, and control decisions. Coverage and RSS controls pass; eight retained failures are CPU or wall-time failures, and the result remains unqualified.
- The native rate-probe files contain 240 samples with one checksum, zero P-core user time, and SDK CPU times from 238.274750 ms to 564.901417 ms.
- The README correctly leaves the mechanism unresolved. The evidence does not independently establish physical core frequency, thermal state, forced idle, or the exact macOS scheduling mechanism.
- The administrator `powermetrics` capture was not run. `power-probe.log` contains only `sudo: a password is required`, and the README and decision trail disclose that limitation.
- The portable verifier checks the archived artifacts; it does not rerun the original external data, native build, live scheduling, or privileged telemetry. The README states this replay boundary.

## Attention

reviewed by gpt-5.6-sol

- **Correct the three-clock accuracy claim.** `rate-probe-summary.json` reports a 0.015434% maximum disagreement because both workload helpers compare only `getrusage` with the SDK CPU clock. Recomputing the saved raw rows across SDK CPU, `getrusage`, and `CLOCK_PROCESS_CPUTIME_ID` gives a 0.024164% maximum. The defensible wording is “SDK CPU and `getrusage` agree within 0.016%; all three clocks agree within 0.025%.” This affects README line 41 and decision row 16.
- **Do not accept `capture-frequency.sh` success as a valid capture without checking its result.** `frequency-workload.py` records checksum count and P-core user-time status but does not fail when either invariant is wrong, so the shell script can print `Capture complete` for an invalid workload. It also does not validate the plist or sample count.
- **Harden the manual capture path before relying on it.** The script uses a host-specific mutable virtual-environment path, creates its temporary directory before applying `umask 077`, has no timeout or termination path for a stuck profiler, and starts workload processes in new sessions but cleans up only their direct PIDs. These are operational and provenance risks for the pending privileged capture.
- **Keep the privileged mechanism test marked skipped.** The listed evidence contains no successful `powermetrics` output. It also contains no saved output for the claimed shell-syntax and helper-compilation checks, so those two checks are assertions in the trail rather than independently reviewable receipts.
- **Treat cleanup as a summary receipt.** `worker-cleanup.json` says 118 owned PIDs were checked and none remained, but it contains no PID identities, process start identities, timestamps, or inspection output. The count is arithmetically consistent with the smoke and native probes, but the cleanup claim cannot be replayed from this file.
- **Bind the test log to its run.** `controller-final-tests.log` shows 269 passing tests, but it does not record the command, revision, environment, or timestamp. `source-commits.txt` and the empty `source-status.txt` provide adjacent provenance, not a cryptographic or in-log binding.
- **Limit the independent-review claim.** Decision rows 4 and 14 name `gpt-5.6-sol`, and saved synthesis/review documents preserve conclusions, but without transcripts the reviewer identity, prompt, and independence cannot be audited. Describe these as saved review conclusions rather than transcript-proven independent review.

## Final disposition

The factual clock claim is fixed. `rate-probe-clock-audit.json` recomputes all three readings at 0.0241703%, the README now uses the defensible 0.025% bound, and the appended decision explicitly supersedes the earlier two-interface result.

The capture changes resolve the previously identified success-validation, interpreter-path, provenance, permission-order, and direct-PID cleanup risks. Static checks and the six synthetic validation cases are preserved as receipts. `worker-cleanup-detailed.json` adds 119 per-PID, timestamped, source-linked inspections; `controller-test-provenance.json` binds the passing 269-test run to its command, clean revision, source hashes, interpreter hash, environment, timestamps, and log hash.

Two limits remain and are accurately disclosed: the authenticated `powermetrics` path has not run, and no external hard timeout for a stuck profiler is guaranteed. Physical frequency, thermal throttling, forced idle, and the exact macOS scheduling mechanism therefore remain unresolved. No transcripts exist; reviewer provenance remains a saved-review claim, not transcript-proven independence.

Verdict: the evidence package is internally accurate for the observer-isolation smoke and native reproduction, with privileged mechanism verification still pending.

### Runtime replay limit

Portable replay is now explicitly runtime-bound. System Python 3.9 changed floating counter component sums by at most 1.907e-6 ns across 14 components, while recorded Python 3.14.6 reproduced them exactly. `runtime-rounding-witness.json` demonstrates ordinary `sum` versus `fsum` rounding; thresholds and raw data are unchanged. Requiring Python 3.14.6 and documenting the 317-check result makes the archival claim accurate, but cross-runtime replay portability remains intentionally limited.
