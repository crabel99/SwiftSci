# Review disposition

- The resource overview now shows primary and twin throughput, charged CPU per job, wall time per job, sampled RSS, and resident MiB-seconds. It links the original comparison report.
- The collection wrapper writes its method before launch and checks the method against the measured plan. Retrospective reports remain labeled retrospective.
- Worker P values are explicitly permitted kernel work. Near-zero P ratios are described as unstable.
- Final validation supersedes the intermediate receipts. The clean head passed 275 controller tests with no skips, including the six focused tests. A new real collection completed 24 queues and retained five timing failures. Saved and replayed diagnostics agree, original capture bytes remain unchanged, and all 109 recorded worker/controller PIDs were absent after completion.
- The archive retains the exact raw acquisition and replay evidence. Its hash verification does not claim a portable full audit without the original external dependencies and capture location.

The new counter report does not independently measure hardware frequency, establish an energy result, or qualify a library ranking. The source and evidence remain local.

The final review preceded packaging. The promised source snapshot has now been copied, and every method-hashed file matches its declared fingerprint in `source-snapshot-verification.json`. This resolves the missing-source flag. External executable, calibration-library, input-path, and capture-location requirements remain explicit in the replay instructions.
