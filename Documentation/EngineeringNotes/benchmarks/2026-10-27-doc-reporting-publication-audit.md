# Independent publication audit

Reviewed by gpt-6-astra on 2026-10-27. No publication blocker found in the frozen package for source `84aa7c59e80d8282c7daf0ce8e9dfc4871308b60`.

The actual package contains 92 manifest-listed files, 93 files including the manifest, 51 compressed payloads and 2,559 comparison archive members, totaling 4,676,837 bytes. I ran its retained standalone verifier successfully and independently checked manifest membership, unique paths, stored hashes, gzip contents and unique archive members.

All 88 source-derived payloads match the original local artifacts after exactly the packager's declared replacements. Every compressed payload's original digest, published uncompressed digest and uncompressed size agree. All seven transformed payloads have correct original and published digests, and the transformation map contains exactly those changed payloads. All 2,559 archive members match their original bytes after the same replacements, with correct original/published hashes, sizes and redaction flags.

I derived the original hostname from the worker receipt and the native hardware identifier from the original native logs without reproducing either in this report. Across 2,740 stored/decoded/member byte streams, neither original identifier remains. Scans found no matches for private keys, GitHub/Slack tokens, AWS access-key identifiers, credential-bearing URLs or long bearer credentials. A further scan for password, API-key, access-token, secret-key and authorization assignments found no unresolved candidate. These checks support the observed package review; they are not an anonymity guarantee. Authorized local filesystem paths remain intentionally present.

The package excludes the raw task transcript, build caches, native result bundles and full CodeQL database. Its retained controller paths and historical artifact paths describe the original execution environment. The standalone publication verifier accepts a downloaded package path and validates retained bytes; the qualification/build controllers require their original artifacts and dependencies and are not claimed to provide a portable rerun.

The preserved failed verifier is byte-identical to its original and matches the digest in `qualification-verifier-failure.json`. The corrected verifier, failure metadata, substantive audit and qualification record are retained. The actual correction requires all 348 extracted files: 288 library files, 59 benchmark files and the manifest. The published README preserves both the failed evidence check and its resolution, along with the four strict numerical failures and one unchanged security finding.

The prepared PR body accurately describes the three-file reporting change, the five regression outcomes, actual 98.66% heuristic ratio, local native/workflow checks and retained failures. It makes no hosted-result claim and does not equate this scan with DocC or Codecov coverage. `RECORDS_URL` is the only remaining delivery placeholder and must be replaced with the verified pinned publication URL before posting.

No source or package content was changed during this audit. This report is deliberately outside the immutable package. No remote writes, builds or heavy tests were performed.

## Attention

No new blocker. Preserve the package bytes and stated qualification limits; replace and verify the pending records link during delivery. Remote publication and PR creation are later actions, not outcomes of this audit.

## Reviewed snapshot

- `records/FILES.sha256` SHA-256 `ba286509417655733f4c9f181f62b7683ccef7ac78a24bc5a0ec114ec976489f`
- `package-records.py` SHA-256 `c01b84fe310cfb7768d73f040151d298f1cec8a750341ca7e63b29a6362ca008`
- `records/audit.md` SHA-256 `100adbf0435b5371b83add6327e76a3c9179dae220c1c3e2bee0fca68ce1828b`
- `records/qualification.json` SHA-256 `0d0639bc06707d61ff5dd4e46e7f6ff157c2bf2d528bebe87a5c250624738087`
- `pr-body.md` SHA-256 `7f26efea80ffef74e14540660d458494cb0d304799a54e184d142175befbefec`
