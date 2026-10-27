# Core ML export records publication audit

reviewed by gpt-6-astra

No publication blocker found for the assembled records of `bdf2b57a66330c331bb870a4d762bb94f7dae0a9`. This verdict binds `records/FILES.sha256` SHA-256 `a57fd24378ebf461f68d466d07fe7ce4a071c3787dc18ff818563e78371ecd84`. I did not mutate source or records, publish, run builds, or make remote changes.

The packaged standalone verifier passes with 90 manifest-listed files, 91 total files including the manifest, 50 compressed payloads, and 2,559 comparison archive members. Total size is 4,980,021 bytes. I independently checked unique manifest paths and archive members, complete membership, stored/decompressed hashes and sizes, and every original-to-published transformation.

All 86 source-derived payloads and all archive members equal the retained originals after exactly the declared hostname and native hardware identifier replacements. Thirteen individual payloads required redaction, covering worker metadata and native build/test receipts and logs. Original hashes match raw retained files; published and decompressed hashes match actual package bytes. The compression maps correctly distinguish original raw content from sanitized decompressed content.

A scan of all stored files, decompressed content, and archive members found zero occurrences of the raw machine hostname or native hardware identifier. Additional scans found no private-key blocks, GitHub/AWS/Slack credential patterns, bearer values, credentials embedded in URLs, or apparent password/API-key/client-secret/access-token assignments. No unnecessary host/device identifier was identified. Authorized local filesystem paths remain; this is not an anonymity claim.

The package preserves the failed relocated-cache compatibility attempt, recovery record, red and green evidence, complete native/workflow summaries and logs, actual older-compiler focused tests, security results, and independent audit. The original failure remains a failure and is separate from the successful compatibility rerun. Raw chat transcripts, generated build caches, xcresult bundles, and the full CodeQL database are excluded as documented. The published qualification, README, and audit distinguish retained-byte verification from fresh execution.

## Draft PR review

Reviewed `pr-body.md` SHA-256: `0eaa6d4e1563400c35db2c691f78daef6d5d15b2617bda4c3c34be2252920e9e`.

Its invalid-activation failure description, four-file scope, numerical regression coverage, native counts, main/benchmark results, actual Swift 6.3.3 runtime tests, and changed-source CodeQL extraction claims match the audited evidence. It explicitly retains the four strict comparator failures and unchanged MD5 finding, discloses hosted SwiftML/Codecov exclusions, limits runtime qualification to one host, and makes no performance or Neural Engine placement claim. It does not assert a hosted outcome or upstream approval.

The remaining `RECORDS_URL` is an intentional prepublication placeholder. Replace it with the pinned published records URL and verify that URL before creating the PR. No other unsupported claim was found.

## Attention

reviewed by gpt-6-astra

No new package or substantive PR-body flags. Preserve existing hosted-coverage, single-host/runtime, numerical-policy, and MD5 limits. The published-link replacement and later PR/hosted outcomes remain delivery actions, not completed results certified by this audit.
