# Serial gather resource qualification

Frozen before measurement on October 19, 2026. Compare the existing serial specialization against its exact parent baseline. No production changes or retuning.

Use identical compiler options, dependency objects and deterministic fixtures for both builds. Release, arm64 macOS 14 target, no coverage or sanitizers. Native CPU scheduling, no worker cap. AC power required.

Twelve complete sort or row-gather cases cover numeric controls, mixed String/Bool payloads and Date payloads. Include small and large shapes, ties, missing keys and both sort directions. Use five alternating timing pairs, two warmups and five measured operations per worker; three separate fresh-process memory pairs without warmup. Validate all output values and row identity against an independent stable comparison-sort permutation outside measured clocks.

Measure process CPU user plus system time across threads and elapsed time for API call plus output release. Measure live malloc bytes before call, with output held and after release. Capture peak RSS before validation. Input and independent permutation construction are excluded from CPU clocks but included in RSS high-water. This is not a full import-to-prediction workload or an energy measurement.

Interpret paired ranges as observed variability, not confidence intervals. A default resource benefit requires consistently lower CPU across the affected large cases without increased live output storage. Preserve any control regression or mixed result; do not average unrelated cases into a score. Timing gains alone do not qualify the candidate.

## Checker amendment before the final run

The inherited checker converted nonnumeric values to strings. Stop the preliminary run and retain its receipts under `preliminary/`. Replace conversion with direct typed equality for every output value, retaining bit-pattern comparison for Double and exact null counts. Run every declared case again on both builds. The production sources, fixtures, measured boundaries and acceptance criteria are unchanged. Final measurements use only the amended checker; preliminary measurements are not pooled with them.
