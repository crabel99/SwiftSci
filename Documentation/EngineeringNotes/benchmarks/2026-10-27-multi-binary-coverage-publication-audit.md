# Frozen publication package audit

reviewed by gpt-6-astra

No privacy or integrity blocker found in the frozen records package. Publication of these exact records is cleared by this audit. I made no changes inside records/.

This approval binds to FILES.sha256 with SHA-256 `110f2c1b4003b6fecf4a28a1db945e5591b783c08993ed3ab9cf032469d79c8f`. The package contains 116 files including the manifest, 115 manifest payloads, 63 separately compressed text files, and 2,559 benchmark archive members.

I independently verified every payload digest and decoded compressed stream. Each retained file equals its local original after only the declared hostname and native-device substitutions. Every compression entry agrees with its original hash, decoded hash and size. All nine transformed payloads agree with their original and published hashes. Every benchmark archive member agrees with its original, transformed bytes, declared size and recorded hashes. No duplicate, absolute or traversing archive path was accepted. The explicit packaging recipe produces exactly the observed payload and archive-member sets.

The privacy scan covered 2,673 decoded text streams and 78,780,366 bytes, including every archive member. No retained stream contains the known hostname or native device identifier. No private-key headers, GitHub token forms, AWS access-key forms, populated bearer credentials, URL user/password credentials, account-usage telemetry fields or quoted credential assignments matched the scan. Every scanned payload decoded as UTF-8 without binary NUL bytes. The inventory excludes the raw transcript, process inventory, account telemetry records, caches, native result bundles, executable binaries and full security databases. Authorized filesystem paths remain as documented. Mentions of excluded artifacts in review prose and controller paths are descriptions, not retained copies of those artifacts.

All five setup-failure inventory entries are present and match their original hashes. The separately retained initial red and failed-green controls also match their originals. The frozen thirteen-row decisions.tsv is an exact prefix of the current append-only trail, ending before later publication and delivery actions. The frozen plan correctly leaves publication and handoff open.

The frozen source patch, source reconciliation, qualification and source-publication receipt exactly match the audited originals. The source receipt binds its qualification hash and reports a normal non-force push of `08486058190836df0a3b1916aa2cb633450a35fc` to `refs/heads/codex/fix-multi-binary-coverage`. Scoped transcript line 730 records that publisher exiting zero and returning the matching remote ref. Lines 747, 748 and 756 record package creation and both original and copied standalone publication verifiers exiting zero. I did not perform another remote operation for this audit.

README.md and the frozen audit distinguish local qualification from hosted CI and Codecov acceptance. They retain the four known strict pandas failures, one unchanged unsuppressed MD5 finding, MLX cold-start limitation and old-vector regeneration requirement. I found no unsupported claim that hosted checks or Codecov acceptance had passed.

Two initial attempts to derive the recipe inventory in my read-only audit script failed while selecting AST loop lists. I corrected that script selection and completed the full inventory check successfully. Neither attempt wrote to the package or changed its files.

## Attention

reviewed by gpt-6-astra

- No package publication blocker remains for the exact manifest identified above. Recheck integrity if any frozen byte changes.
- Verify the published records branch against these frozen bytes after upload. This audit approves the local package; remote records delivery has not happened yet.
- Hosted CI and Codecov acceptance remain separate from the completed local qualification. Existing benchmark, MD5 and MLX limitations remain as documented.
