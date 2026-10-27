# Independent publication audit

Reviewed by gpt-6-astra. Completed 2026-10-27T18:44:24.917044+00:00.

No publication blocker remains in the revised frozen `records/` candidate. I did not modify the package/source, run builds/tests or make remote writes. The incomplete and intermediate candidates remain as `records-before-nested-failure-log-inclusion` and `records-before-failure-inventory-guard`. Both are superseded by this review.

The candidate has 158 total files, 157 manifest-listed files, 72 compressed payloads, 2,559 benchmark archive members and 7,873,026 bytes. The packaged standalone verifier actually passed. I independently checked the complete manifest, duplicate-free file/member inventories, every gzip payload, every archive member and all original-to-published mappings. Archive members are regular files with safe relative paths.

All 153 source-derived payloads equal the originals after only the declared hostname and native-device replacements. Compression metadata matches original hashes, published decoded hashes and byte lengths. All nine changed payloads have complete transformation bindings. Every benchmark archive member matches its original, published hash, byte length and redaction flag. The manifest remains `c9264fdb7826238b22cbf5b15b90ee0668ee41e0d17cc6cc7fe7ffc6c44bedc1`.

I scanned 2,789 stored, decompressed and archive-member byte streams, including the manifest. Original local hostname/native identifiers were derived from raw local evidence without reproducing their values here. There were zero matches for those originals or the native hardware identifier pattern. Private-key, GitHub-token, AWS-key, credential-bearing URL and populated bearer-authorization patterns also had zero matches. Authorized filesystem paths remain. This is not an anonymity claim. Raw task transcripts, build caches, probe/native binaries, xcresult bundles, full CodeQL databases and TRAP files are excluded.

The selected PR94 provenance matches its original metadata hash, exact head/base, head repository and read-only permissions. The unrelated Dependabot release-note body is excluded. The hosted failure log, baseline and final process outputs, golden fixtures, real red/green XCTest logs, preliminary setup attempts, all five full-job access failures, actual native exported trees and security source hashes remain available.

## Review correction

The first candidate omitted the 276-byte nested failed-extractor log referenced by `setup-failures.json`. The primary failed database log was present, so the omission did not conceal the failure, but it left an inventory entry unresolved. The revised package recipe includes nested extractor logs from both successful and failed security attempts. The formerly missing log now has a gzip mapping bound to its actual original bytes. Every setup-failure inventory reference now resolves in the package. The previous package remains available for comparison.

The final revision also adds a standalone verification guard for every declared failed-attempt payload. It requires the original digest through the compressed mapping or declared redaction mapping, and requires the file to exist in the manifest. I ran this final packaged verifier against the first incomplete snapshot: it exited 1 on the exact missing extractor log. The same verifier exits 0 on the final candidate. The retained `publication-guard-red.log` records the same missing-entry assertion. This is a read-only negative control, not a build or test-suite rerun.

Compared with the immediately prior reviewed ea58 candidate, only `verify-publication.py`, `decisions.tsv` and the regenerated manifest differ. All diagnostic evidence, mappings, compressed/archive bytes, source and qualification are unchanged. Both changed payloads equal their current local originals, and all final bytes passed another privacy scan. The final packaged decision log contains seven rows through the package correction and matches the live trail at review time. The earlier substantive audit binds its five-row historical snapshot.

## Claims and delivery boundary

README and the current draft PR preserve the necessary user-facing limits: regenerate old stored vectors/indexes, no trained semantic-quality guarantee, explicit precommit versus final-head evidence, source-only PR94 merge proof and retained full-check setup failures. The original eight passing workflow steps remain distinct from the failed extra coverage guard and separate local eight-line coverage export. Existing strict comparator, MD5 and MLX limitations remain visible.

The packaged source-publication receipt binds the exact reviewed qualification and actual publication controller. Its successful scoped execution at 18:39:55Z and remote readback record source `3012a6e52d70306a9437fb8cd8af4343a41560dd` on the fork's stable-local-embedding-hash branch through normal non-force Git. Earlier audit statements that publication was pending describe their earlier snapshots. This receipt does not establish a notes publication, new PR or changed hosted outcome.

PR94's branch remains outside the selected account's write permissions. Upstream application and branch update are still required before its failed CI can be considered resolved. Replace the draft's `EVIDENCE_LINK` only with the verified pinned notes URL, then perform the subsequent delivery checks.

## Bound package

| Artifact | SHA-256 |
| --- | --- |
| `records/FILES.sha256` | `c9264fdb7826238b22cbf5b15b90ee0668ee41e0d17cc6cc7fe7ffc6c44bedc1` |
| `records/package-records.py` | `ec2f1f3082e2e6aa9ab66ba5e6daf1ce54bda39ce2e711c846c011c892db21e9` |
| `records/verify-publication.py` | `775839cdb1173526e68929191c21b75094efd6ab296ea2528c9a03fdf19a6624` |
| `records/source-publication.json` | `c741f9b1ab55d575a9c7095ebb28c75067f79c0539098695e674386c0ed1b5e1` |
| `records/decisions.tsv` | `b8da37a5ecbecd729eae4b30f07478d4811216b88a3a9a96788a7413d9ed7a77` |
| Current draft `pr-body.md` | `d33bc9fb9dd341f9f92f66385c38080e59b6436fc62f83e1dcb7af9e35464d5a` |

## Attention

Reviewed by gpt-6-astra.

The missing inventory log was corrected and rechecked, and the final verifier rejects its omission. No new privacy/integrity flag remains. Stored-vector migration, semantic limits, upstream application and the existing qualification limitations remain unchanged. Notes/PR delivery and the pinned evidence link are still pending.
