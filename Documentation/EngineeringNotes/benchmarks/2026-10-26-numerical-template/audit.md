# Numerical template audit

reviewed by gpt-6-astra

No blocking source, numerical-evidence, or qualification finding remains in the reviewed local template unit. Final source is `0e1635199654ac6a20b32ea53eea0ffdfa39e747`; `final-run-qualified` is the authoritative positive result. The reviewed qualification JSON has SHA-256 `02f696a103c61fe209f09c619caac1d6d236c034c85a99d3bb8000389da66d52`. Publication bytes and a remote dependency fetch were not yet available for this audit.

I inspected the public-import example, legacy comparison, scalar verifier, runner, source/build bindings, standards/spec reviews, package manifest substitution, retained failures, and relevant scoped transcript and decision rows. I independently checked all qualification artifact hashes and the final probe bindings. I did not build or launch Swift, change source, or publish.

The runner now rejects a probe whose build-log path or digest differs from the selected build. It also verifies the recorded object paths under that build's products and their hashes, binary and consumer hashes, and public compile flags. Both final probes pass these checks. The old c4de probes fail before launch under the final selected build; the negative-control output directory is empty. The original runner and review finding remain available.

The public workflow splits training and query rows before fitting imputation, scaling, PCA, or classification. Labels stay separate. Query rows preserve the selection `[10, 8, 10, 9, 11]`, including the duplicate. The fixture covers both invalid numeric storage and a valid NaN. Public legacy output provides a second implementation path. The independent scalar oracle derives preprocessing statistics from training rows, computes the small eigensystem, aligns eigenvector signs, and performs the declared logistic updates.

I recomputed verification from copies of the retained outputs in a temporary directory. The new result equals the saved authoritative verification, including maximum absolute error `4.440892098500626e-16`, tolerance `1e-12 + 1e-12 * abs(reference)`, and predictions `[1, 0, 1, 1, 0]`. Legacy output differences are zero for the checked fields. Both authoritative probe attempts exited zero. The public example and package source bytes match; the package's local dependency substitution is the only manifest change, its build succeeded, and its saved result equals the authoritative prepared result.

The earlier invalid rowValues compile attempt, its missing-executable launch, and the later no-Metal sandbox attempt remain failures. `final-run-bound` contains a diagnostic rather than numerical JSON and has no passing verdict. The final qualified run is separate. The added template README sentence accurately warns that existing MLX initialization needs accessible Metal even when the example selects CPU algorithms.

## Attention

reviewed by gpt-6-astra

- Low, external reproducibility. The package was built with a verified local dependency substitution. At this review cutoff the exact remote revision had not been fetched and built through the published manifest. Keep `remote_fetch` unverified until there is an actual receipt. A local build does not establish remote availability.
- Low, execution environment. CPU selection does not remove the existing MLX Metal startup requirement. Headless or sandboxed execution can fail before the numerical workflow starts. The retained failed run and template README disclose this.
- Low, inference scope. This toy fixture proves the joined public workflow, selected-row identities, and numerical agreement for this example. It does not qualify statistical quality, memory use, speed, arbitrary datasets, or all PCA eigenspaces.
- Publication gate, pending. Include this audit in the package's declared artifact set, regenerate qualification, verify the assembled manifest/compressed payloads and their original/published mappings, and scan published content for private host/device identifiers. The standalone publication verifier establishes retained-byte integrity; the original qualification still depends on the local build/probes and is not a fresh execution on a reader's machine.

## Addendum, 2026-10-26: remote package verified

reviewed by gpt-6-astra

The earlier external-reproducibility flag is superseded by an actual successful resolve, build, and execution through the remote package manifest. All other limits and the pending publication gate remain unchanged.

I reviewed `check-remote-package.py` and independently verified its digest against `remote-package/receipt.json`, whose SHA-256 is `bdb96d799f8f902496936dc6e01bbbc5acf5b67d6b036362d0981317e9eb6bee`. The exact executed controller has SHA-256 `05764c97eaa3e3ebb4cb0a99cd7a289a930b055c1078343b98f47565fa8deb7d`. All three step exit codes are zero and their log hashes match. The build log ends with BUILD SUCCEEDED. The built binary's hash matches the receipt, and the saved run result equals the independently verified prepared result exactly.

`template/Package.resolved` identifies `https://github.com/crabel99/SwiftSci.git` as remote source control at exact revision `0e1635199654ac6a20b32ea53eea0ffdfa39e747`. The resolver log records fetching that URL, creating its working copy, and checking out that revision. The checkout's origin points to SwiftPM's local repository mirror; that mirror's origin is the same GitHub URL. A local mirror here is part of the remote resolver path, not the earlier local dependency substitution. The checkout is clean at the exact revision. All 383 tracked files under Sources plus Package.swift match both receipt hashes and the frozen qualified source bytes. Consumer and manifest bytes also match the executed receipt.

This establishes successful remote resolution and execution in the recorded environment. Some transitive dependencies used caches, as the resolver log says. It does not establish an empty-cache build for every dependency or remove the disclosed MLX Metal startup requirement. No new failure or unsupported remote-success claim was found.
