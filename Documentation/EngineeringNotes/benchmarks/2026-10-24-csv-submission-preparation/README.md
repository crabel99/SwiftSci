# CSV submission preparation

The two descriptions are ready for local review. No source branch was pushed, no PR was opened, and no maintainer message was sent. Upstream `main` remains `e005efcc1dd55bb40f9e1ad63ac29e2d29de5178`, so no source refresh or repeat test run is needed for the existing local heads.

## Reviewable descriptions

1. [CSV ingestion and matched comparison contracts](ingestion-pr.md), proposed title `perf(csv): bound ingestion metadata and align comparison contracts`.
2. [Selectable compact Double storage and numeric consumers](compact-pr.md), proposed title `perf(dataframe): add selectable compact Double storage and reuse numeric buffers`.

The [submission metadata](submission.json) records exact heads, intended repository, titles, and the dependency. The [independent validation report](../2026-10-23-csv-review-stack/README.md) owns the build and correctness receipts. The [reference study](../2026-10-23-csv-sort-closeout/README.md) owns the performance results and their original measurement fingerprints.

## Submission sequence

Push the two source branches to the verified GitHub fork, then open the ingestion PR against upstream `main`. Hold the compact upstream PR until ingestion merges. Its current local comparison base is the ingestion branch, which is absent from the upstream repository. [GitHub requires every branch in a PR stack to belong to the same repository](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/creating-stacked-pull-requests). That fork-local base cannot provide a focused upstream PR target without maintainer action. Do not create an upstream branch or duplicate the ingestion diff merely to simulate a stack.

After ingestion merges, fetch the resulting upstream head. Refresh only the compact branch's 14 commits onto it, preserving the current review head as a recovery point. Verify that the resulting diff contains only the compact work, inspect any upstream changes, and rerun validation on the actual refreshed head before submitting. Update the compact description's validation fingerprint and dependency language at that point. Preserve all historical benchmark fingerprints.

The temporary source repository's `origin` is a local cache, not GitHub. A later push must use the verified fork URL or a clearly named GitHub remote. Neither source diff contains engineering reports or local machine paths. Publish only the two descriptions as PR text; keep this planning record, metadata, and evidence on `codex/engineering-notes`.

## Claims and limitations

The ingestion description makes no unmeasured speedup claim against upstream. It distinguishes bounded transient row metadata from whole-file mapping and final output storage. The compact description includes read CPU regressions, default optional storage, `.values` materialization, generic fallbacks, resource use, elapsed time, and runtime-baseline limits. It preserves the known numerical failures and the distinction between a passing regression policy and failed strict conformance.

The GitHub searches found no open PR and no issue with CSV in its title. This is not an exhaustive issue-body search. No issue was auto-closed or linked by guesswork. Hosted CI remains pending. Local test size and compiler checks do not establish CodeQL or Codecov success.
