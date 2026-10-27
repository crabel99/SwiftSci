# Deliver the independent GPU BCE correction

Base is live upstream main e19db7dda4567c425b7eb002da82e234e6c7980f. Keep PR89 unchanged. Reuse the already reviewed smooth BCE correction and three analytical regression definitions from `53063789b1`, excluding prepared-classification files that do not belong in this independent fix.

- [x] Read live upstream/PR status and isolate the smallest independent unit.
- [x] Reproduce failure using the existing analytical tests on the actual upstream base.
- [x] Apply only Losses.swift correction, freeze exact source, and pass focused tests.
- [x] Run full native Debug/Release, actual local main/benchmark workflows, Python and matching-compiler Swift CodeQL, and Swift6.3.3 compatibility on that exact source. Preserve all failures and existing numerical policies. Keep Xcode27 selected.
- [ ] Independent standards/spec review against fixed upstream base and final trail audit.
- [ ] Publish fork source, qualification evidence and one focused draft upstream PR. Attach it to this task, verify actual diff/CI status, and update tracker/handoff.

No new public APIs, classifier feature work, dependencies, upstream merge or maintainer messages. GPU training trajectories intentionally change at previously incorrect zero-logit derivatives; CPU fitting remains unchanged. Prior broader qualification remains historical, not fresh evidence for this new source.

This package captures qualification before publication. Final trail audit and remote delivery are recorded separately after their checks finish.
