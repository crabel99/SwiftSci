# Focused upstream delivery queue

Live main at selection: e19db7dda4567c425b7eb002da82e234e6c7980f. PR89 remains a separate open prepared-PCA contribution. The qualified combined fork is a convergence/consumer test revision, not the intended single upstream diff.

1. **GPU BCE gradient correction, current unit.** Isolate Losses.swift and BinaryCrossEntropyTests.swift from `53063789b1` directly on main. No dependency on PCA or prepared classification. Frozen delivery head `506204920a5a073b1e7bc316476875860bacfda0`; fresh local qualification passed.
2. **CoreML multiclass export correction.** The serialization change and public regressions in a1e234d256 are independent of prepared classification. Isolate the four files on current main, then run fresh source-bound checks. Prior model-study results remain historical evidence.
3. **Truthful documentation-check reporting.** Isolate c4de6cc866's checker, reporting tests and workflow label from the integration merge. It changes no numerical algorithm or coverage threshold.
4. **Prepared classification.** Deliver the feature from8926829bf2 with the GPU correction present. Keep the exact PCA stack intact if PR89 merges first. Reconcile the actual shared PreparedNumericBatch accessor and verify final source; do not use the combined integration merge as a catch-all PR.
5. **Agent completion reporting and cooperative cancellation.** SwiftAgent/SwiftLLM production files are byte-identical between upstream base and c4de parent, so6ef1a4b35b and0e16351996 can be isolated without the scientific feature stack. Preserve the two logical commits and existing compatibility/cancellation limits, then qualify the actual new head.
6. **Numerical example upstream.** The public template is already published and remotely verified on the fork. An upstream example needs the prepared PCA and classifier APIs delivered first. No new generic preprocessing API is needed.

No upstream merge or maintainer comment is authorized by this delivery task. New PRs should be focused and draft until their actual hosted status is known. Check for existing PRs before creating duplicates. Every new source head gets appropriate local checks; prior source-qualified receipts cannot be relabeled.
