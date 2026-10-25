# Review disposition

The saved review remains unchanged. These corrections address its findings.

- Corrected the JSON timing caveat. The end-of-window model is used; the start model is rejected under the strict constraints. Four selected Mach offsets are evaluated at the telemetry-origin midpoint. No continuous uncertainty sweep is claimed.
- Preserved the 100 raw bridge pairs and added their arithmetic checks to replay. The original bridge-producing command was not saved as a file. The reconstructed producer documents the described procedure and is explicitly not proof of that original command's identity.
- Bound the test commands, interpreter, scripts, raw inputs, and results in `verification.json`. The raw replay checks all four numeric output files byte for byte in a fresh output directory, the selected bridge, the four sensitivity cases, the rejected timestamp model, and the partial first interval. The three small overlap and timestamp tests still pass.
- Changed the plot's causal wording to "covaries with." The report retains the limitations on shared-cluster averages, overlapping runs, thermal pressure, endpoint SFI, energy attribution, and older benchmark qualification.

The remaining clock-model provenance and timestamp-call-site uncertainty is explicit. The recorded offset checks support the narrow correlation result, not every possible reconstruction or an exact macOS clock-selection rule.

The final review preceded archive packaging. Its preservation-scope flag is addressed by `manifest.json`, which covers all 63 archived evidence files, including the runner, reviews, figures, and original capture. `archive-replay.json` records successful hash verification of those files after extraction and a passing replay from that extracted archive. `verification.json` remains the narrower numeric-input and test receipt.
