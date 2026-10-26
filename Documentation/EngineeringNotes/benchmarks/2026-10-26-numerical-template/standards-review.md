## Standards

No open findings after re-review. Reviewed CONTRIBUTING.md, subtract-before-you-add and the code-review smell baseline. No hard documented-standard violation or meaningful code-smell finding was identified in the workflow, controls, manifest or README.

Resolved P2: bind supplied probes to the selected library build before stamping its commit. The original `run-template.py:12-16` verified each probe against its own proof and independently verified the selected build, allowing old c4de probes to receive a final0e source stamp. The revised runner compares the resolved input-build-log path and its actual SHA against the selected build log, requires linked objects inside that build's products, and retains object/binary/source hash checks. It now records process exit attempts.

Evidence reviewed:

- `mismatched-build-rejection-final.json` records exit1 before probe execution when old c4de probes are paired with the final0e library root.
- `final-run-qualified/provenance.json` binds source `0e1635199654ac6a20b32ea53eea0ffdfa39e747` and runner SHA `0134ebcf6747674d13f11d0099a7d070d8dd85f0e668cf8039b2bf0930faae7a`. Its runner, build-log, object and result hashes match current files.
- `final-run-qualified/attempts.json` records both probes exiting0; `verification.json` records passing scalar and legacy controls under `abs(error) <= 1e-12 + 1e-12 * abs(reference)`. The verifier and result hashes match current files.

The core template selects features and targets together, fits every learned stage on eight training rows, and associates prediction arrays with score provenance. Explicit CPU/full-SVD choices and optimizer settings make the example reproducible. Independent scalar preprocessing, a closed-form eigensystem and scalar logistic updates complement legacy API parity. The recorded local manifest substitution remains clear.

The preserved sandbox failure in `final-run-bound` is distinct from the successful qualified run with device access. This re-review inspected source and recorded artifacts and checked their hashes. It performed no builds, numerical reruns or network access.
