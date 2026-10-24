# Review draft: stable identity for fully missing sort keys

This is prepared text for the isolated `a74f5c3` change against `940353d`. It is not a submitted PR or a claim that the full source stack is ready for production.

## Proposed title

Avoid sort preparation when every key is missing

## Proposed description

A stable sort of an entirely missing key must preserve source row order in both directions. `TypedColumn.sortedIndices` now returns that identity permutation from its existing immutable null count, avoiding key scans and temporary sort storage. The change applies to every supported native key type and compact Double. Valid NaNs remain distinct from missing values and retain their comparison path.

Two test functions cover empty inputs, validity boundaries, both directions, public dataframe sorting, native Int64 identities above 2^53, and compact inputs containing valid NaNs. Both tests pass before the optimization because this is a resource improvement, not a correctness repair. The test type is 60 lines.

All 431 dataframe test functions pass in Release, Debug, and Address Sanitizer with no failures or skips. Those receipts match the exact retained source and test files. The complete MLX-dependent package and hosted required checks remain separate prerequisites.

The original exceptional-case panel has 14 qualified cases out of 18. Qualified CPU reductions range from 67.5% to 99.0%. Eight-million-row compact Double uses 18.867 to 6.076 ms CPU and 191.828 to 130.797 MiB peak RSS. Four original native timings and one original common-shape timing remain unqualified. A separate 32-replicate confirmation passes unchanged quality controls on the four selected native cases without replacing their original records.

The shortcut has a small measured common-input cost. The higher-replication distributed 32,768-row compact control uses about 4.4% more paired CPU, a few microseconds. The earlier 10% million-row observation does not repeat consistently. A refactor that moved the shortcut into type-specific algorithms was rejected after it added about 7.5 MiB peak memory to million-row compact sorts.

The engineering evidence and readable comparison remain on the fork's `codex/engineering-notes` branch. The separate complete-schema reference panel evaluates the accumulated compact-storage and sorting stack, so its gains must not be attributed to this one-line shortcut. Its primary scope completes the DuckDB Arrow bridge pandas import before timing. The original first-use panel remains separate. Engineering notes, fixture archives, profiles, and rejected experiments are excluded from the source patch.

## Before submission

Confirm the intended parent after upstream synchronization. Rerun required package checks on the combined branch and obtain passing hosted checks. Link a published, sanitized engineering-note revision if benchmark evidence is requested. The current report is local and no push is authorized here.
