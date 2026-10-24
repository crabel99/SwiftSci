# CSV review stack validation

Two local review branches now separate the reader and comparison contracts from selectable compact Double storage. Each branch passes its own full package tests and formal CPU regression policy. No branch was pushed and no PR was created.

## Review order and scope

| Order | Branch | Head | Commits in this review | Changed files |
|---|---|---|---:|---:|
| 1 | `codex/csv-ingestion-review` | `428891dfd1777be592cb04c85eea1a5b433cb32c` | 45 | 80 |
| 2 | `codex/csv-compact-review` | `224c6a2a2cddb40904ce4ad140829a4b63030884` | 14 | 22 |

The first branch starts from upstream `main` at `e005efcc1dd55bb40f9e1ad63ac29e2d29de5178`. It contains the 43 reader and comparison-contract commits through `5d1f89a961`, then the acceptance-request and reviewed coverage-fingerprint fixes. Record discovery, eager and streaming reads, inference validation, explicit date formats, and selectable conversion concurrency stay together with the matched-schema benchmark contracts. This cut also contains the earlier borrowed radix buffers and scalar column-gather changes used by the reader-to-sort path.

The second branch starts at the first branch's head. It adds the 13 compact-storage and consumer commits through `a74f5c3b5e`, then the test type-inference cleanup. Gathering, joining, filtering, numeric preparation, and stable sorting retain compact Double storage when the caller selects it. Optional storage remains the default.

Review the second branch against the first until the first lands. Then refresh it onto upstream `main` and validate the refreshed head. Do not submit both as independent diffs against the old upstream base.

## Independent validation results

| Check | Ingestion cut | Compact cut |
|---|---:|---:|
| Release native tests | 1594 passed | 1631 passed |
| Debug native tests | 1594 passed | 1631 passed |
| Native failures and skips | 0 | 0 |
| Declared test targets included | 15 of 15 | 15 of 15 |
| Benchmark controllers with Metal enabled | 226 passed, no skips | 226 passed, no skips |
| Formal CPU regression policy | Passed | Passed |
| SwiftSci strict CPU cases | 202 of 202 passed | 202 of 202 passed |
| pandas strict CPU cases | 198 of 202 passed | 198 of 202 passed |
| New or blocking policy failures | 0 | 0 |
| Long type-check warnings in changed Swift files | 0 | 0 |
| Largest changed Swift test file | 197 lines | 147 lines |

Each branch has a separately built, uninstrumented benchmark worker with a verified source and binary receipt. Each CPU run covers 16 profiles and 404 engine executions. Both runs retain the four reviewed pandas Wampler accuracy failures as failed strict conformance. A passing regression policy does not mean full numerical conformance.

Native tests use the pinned MLX dependency, a hash-verified tokenizer, and strict ONNX prerequisites. Controller runs enable the four optional Metal checks. Their single-worker Polars correctness setting is not a performance comparison. ASan was not rerun for these review cuts.

Actual documentation coverage is 2429 of 2462 declarations for ingestion and 2431 of 2464 for compact storage. Both round to 98.66%. The existing script's incorrect 100% success sentence remains a tooling limitation. Hosted CodeQL and Codecov have not run. Local compile diagnostics and test size checks do not replace those checks.

## Preserve the measured checkpoints

The compact review tree is byte-for-byte identical to the validated integration tree at `bc87628ce1fe8722a716a612d4d3db3d0149b7c8`. The original integration branch and experiment checkpoints remain unchanged. The new history moves the two acceptance fixes before the compact work, without changing the final source tree.

The [reference performance report](../2026-10-23-csv-sort-closeout/README.md) still identifies `a74f5c3b5e0e511bf5bb69886a40cbae48b28d99` as its measured compact head and `5d1f89a961106104757f2d8d0b8faba79487d100` as its pre-compact baseline. Those fingerprints are unchanged. No performance timings were remeasured or relabeled for the review branches.

For the representative household dataset, compact storage reduced peak memory by 25.6% for reading and 31.8% for the complete read, stable sort, and matrix path. Read CPU time increased by 4.9%, while complete-path CPU time decreased by 4.4%. These are observations from the recorded comparison, not an upstream-main speedup claim. Compact storage remains a caller choice.

## Evidence and recovery

The [audit](audit.json) records the actual heads, scopes, tests, and failure inventories. Each branch has its own [ingestion acceptance evidence](ingestion/acceptance.json) or [compact acceptance evidence](compact/acceptance.json), with matching regression-policy records. The [experiment archive](experiments.tar.gz) preserves validation drivers, build logs, requests, outputs, certificates, and receipts. It excludes xcresult bundles, compiled binaries, environments, and model weights.

The [source bundle](review-source.bundle) preserves both review branches relative to upstream. The [artifact hashes](artifact-sha256.json) identify the retained files. All reports and raw evidence remain on `codex/engineering-notes` and are absent from both source diffs.
