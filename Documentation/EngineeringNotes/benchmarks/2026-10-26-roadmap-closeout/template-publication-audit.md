# Numerical template publication audit

reviewed by gpt-6-astra

No publication blocker found. This closes the assembled-package gate in the substantive audit for `records/FILES.sha256` SHA-256 `69900bd76ad39b46ccce6042184325dc69d1f7c91d06c52e842766ac039a5788`.

The packaged standalone verifier passes for source `0e1635199654ac6a20b32ea53eea0ffdfa39e747`, with 47 manifest-listed files, 48 files including the manifest, and two compressed build logs. Total package size is 418,201 bytes. Manifest paths are unique, confined to the package, complete, and hash-correct.

I independently compared all 46 source-derived payloads against their retained originals. Every original hash matches `publication-records.json`; every published payload equals exactly the documented hostname and UUID/native-hardware-identifier redactions, with gzip decompression applied to the two logs. Only `package-build.log`, `remote-package/build.log`, and `final-run-qualified/provenance.json` changed through redaction. All original/published digest, size, and transformation-state mappings agree. A scan of all published and decompressed content found zero occurrences of the original hostname or identifiers matching the redacted device formats. Authorized filesystem paths remain; this is not an anonymity claim.

The package contains the 45 qualification artifacts plus qualification itself, including the dated independent remote audit addendum, actual remote controller/receipt/result, resolver and build logs, and exact resolved dependency pins. It preserves the earlier failures and local dependency substitution. The current README and qualification distinguish successful remote consumption from the historical local-only proof. The publication verifier claims retained-byte integrity rather than a fresh numerical execution or repeated remote fetch, which matches what it does.

This was a read-only publication review. I did not mutate records, rebuild, run the example, or publish. The independent substantive numerical and remote evidence reviews remain in `audit.md`.

## Attention

reviewed by gpt-6-astra

No new publication flags. The example's limited numerical scope, existing MLX Metal startup dependency, and disclosed use of cached transitive dependencies remain. This verdict binds the manifest above; the package is ready for publication with those limits preserved.
