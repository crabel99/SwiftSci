# Publication review, September 28, 2026

This review prepares the current engineering-notes revision for sharing with upstream reviewers. It removes unnecessary personal background, an unpublished personal reply, local home-directory identities, hostnames, and device identifiers. The public contributor handle, technical references, numerical results, failed checks, source commits, and limitations remain.

## Scope

The content scan covered 22,411 files and archive members, including nested archives and the split suite-completion archive. It found no matches for the checked common GitHub, GitLab, OpenAI, AWS access-key, private-key, or authorization-header patterns. Pattern scanning is a bounded check, not proof that every possible secret format is absent.

The prose review retained technical uses of terms such as malignant in the breast-cancer dataset and invalid-output test names. They describe test semantics and are not commentary about people or projects.

## Evidence provenance

The working archive was retained locally before publication edits. Sanitized copies replace identifying values with `LOCAL_USER`, `AppleSiliconHost`, or `LOCAL_DEVICE_ID`. Embedded `PUBLICATION_SANITIZATION.json` records identify changed archive members and their original and published hashes. The [publication manifest](PUBLICATION-MANIFEST.json) records original and published hashes for changed files in this branch revision.

Existing run, certificate, source, and capture hashes describe original artifacts. Sanitized copies must not be presented as byte-identical original evidence or used to claim that an unchanged certificate authenticates edited metadata. The sanitation operation does not rerun or revalidate experiments. Numerical data and recorded outcomes were not edited.

This is a normal cleanup commit, not a history rewrite. Earlier commits retain the original non-secret machine metadata and wording. The current revision is the reviewed publication entry point. This review does not claim deletion of previously published copies.

## Future entries

Record the tested revision, configuration, result, and limitations. Review both prose and embedded archives before publishing. Keep credentials and unnecessary personal or device information out of new records. Label transformed evidence copies, and preserve their original provenance separately. Implementation PRs should summarize relevant verified findings without merging this branch.
