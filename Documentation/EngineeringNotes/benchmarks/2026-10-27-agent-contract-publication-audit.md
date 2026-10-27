# Independent publication audit

Reviewed by gpt-6-astra. Completed 2026-10-27T16:31:51.196446+00:00.

No publication blocker found in the frozen `records/` candidate. This review did not modify the package or source, rerun builds/tests, or make remote writes. The superseded pre-audit package was not used as the candidate.

The candidate contains 118 files, including 117 manifest-listed files, 54 compressed payloads and 2,559 benchmark archive members. Its total size is 7,575,389 bytes. The packaged standalone verifier completed successfully. I independently checked the manifest against the complete file set, rejected duplicate entries, decompressed every declared payload and inspected every archive member. Archive member names are relative and contain no traversal paths; every member is a regular file.

All 113 source-derived payloads match their local originals after only the declared hostname/native-hardware-ID substitutions. Every compression-map original digest, published uncompressed digest and size matches. All nine transformed payloads have exact original and published digest bindings, with no missing or unnecessary transform entry. Every archive member matches its original bytes under those same substitutions and its original/published hashes, length and redaction flag.

The packaged `decisions.tsv` is the exact five-row snapshot bound in the substantive audit, SHA-256 `3017ff9c1427c155225e34c1c4a2ea65a8f96026127f0c0b2cecd04a55ac176c`. The live trail preserves that prefix and adds the later publication checkpoint. This expected snapshot boundary is not an unexplained payload mismatch.

I scanned 2,730 stored, decompressed and archive-member byte streams. The original hostname and native identifiers were derived from local receipts without copying their values into this report. There were zero matches for those originals or the native hardware ID pattern. Scans for private keys, GitHub tokens, AWS access keys, credential-bearing URLs and populated authorization bearer values found no matches. Authorized filesystem paths remain visible. This package makes no anonymity claim. Raw task transcripts, caches, executable binaries, xcresult bundles, CodeQL databases and TRAP files are absent.

The original failed ninth coverage guard is retained in the actual main receipt alongside eight successful workflow steps. Original and supplemental LCOV, supplemental profile/object bindings, red overlays and failures, native exported trees, security extraction hashes, the verifier count correction and its pending-prerequisite failure remain present. The current README and draft PR accurately distinguish local supplemental 80/80 line evidence from the unfixed hosted export. They preserve cooperative cancellation, four strict comparator failures, the MD5 finding and the separate MLX cold-start hazard.

`source-publication.json` binds the reviewed qualification and exact publication controller. The scoped transcript records its successful execution at 16:29:20Z. The controller uses a normal non-force Git push and verifies the remote branch before and after. The receipt records exact source `3a9482122cd91a3d18467a9d7005416242b1c203`. The earlier substantive audit's publication-pending statement is its historical snapshot; the later publication receipt supplies the subsequent fact. I did not infer a notes publication, PR creation or hosted CI result.

The draft PR retains `EVIDENCE_LINK`. Replace it with the verified pinned records URL before submission. Remaining delivery checks belong after notes publication and PR creation; they do not require changing this reviewed package.

## Bound package

| Artifact | SHA-256 |
| --- | --- |
| `records/FILES.sha256` | `b589e5749e0337e4683552f7873d2d69cfef00ca60ba611211249c65f687004b` |
| `records/package-records.py` | `e9dd74816319e8c15e47cf221e0e6bb91c40135c352a74dad2c0126ae5f0b615` |
| `records/verify-publication.py` | `2338998dbc74a5ecc0ea438a905fc694ce08d0515ac6a255bfab91bc55f8ec03` |
| `records/source-publication.json` | `25a419b8ad668587fc42fdec849f75ae1a98970e324d5d033e468a8862f75f8b` |
| Current draft `pr-body.md` | `26a119f77ae5dbdb7710953488641b3111281c0d5d5e4865a1999f370d65bab9` |

## Attention

Reviewed by gpt-6-astra.

No new privacy or integrity flags. The substantive limitations remain unchanged. Complete the pinned evidence link and subsequent delivery checks before claiming the PR and records are published.
