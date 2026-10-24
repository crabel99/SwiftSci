# CSV PR publication

Both validated source branches are pushed to `crabel99/SwiftSci`. Both draft PRs target upstream `main`. The actual remote heads and published bodies match the reviewed source and prepared text.

| PR | Scope | Published head | Current upstream diff |
|---|---|---|---|
| [#85](https://github.com/Nodibell/SwiftSci/pull/85) | CSV ingestion and matched comparison contracts | `428891dfd1777be592cb04c85eea1a5b433cb32c` | 45 commits, 80 files |
| [#86](https://github.com/Nodibell/SwiftSci/pull/86) | Selectable compact Double storage and numeric consumers, dependent on #85 | `224c6a2a2cddb40904ce4ad140829a4b63030884` | 59 commits, 97 files, including ingestion |

The user authorized publishing both PRs. This replaces the earlier plan to hold the second upstream draft until ingestion merged. GitHub's cross-fork stack restriction still applies. The descriptions explicitly identify #86 as blocked on #85 and link its [focused comparison](https://github.com/crabel99/SwiftSci/compare/codex/csv-ingestion-review...codex/csv-compact-review), which contains 14 commits across 22 files.

Merge order is #85, then #86. After #85 merges, refresh #86 onto the resulting upstream base, inspect the remaining diff, and validate its refreshed head before review readiness or merge. Neither PR is marked ready and nothing was merged.

Hosted Debug and Release builds, Swift and Python CodeQL, and benchmark verification have begun or are queued in the initial snapshot. Some #85 MLX CPU checks already pass. Full hosted CI and Codecov have not completed. The disabled performance check is not a performance result. No workflow was rerun or cancelled, and no maintainer comment was sent.

The [independent local validation report](../2026-10-23-csv-review-stack/README.md) and [reference performance study](../2026-10-23-csv-sort-closeout/README.md) retain their original source fingerprints. No source change or new performance measurement was made during publication. Both PR artifacts are attached to this chat. Engineering notes remain on `codex/engineering-notes`, outside both source diffs and were not pushed by this operation.

The JSON snapshots record the initial PR metadata and checks. They are point-in-time evidence, not a live CI monitor.
