# Stable sorting experiments

This directory contains the experiments used to select the Double sorting path in SwiftSci. Production changes are in `TypedColumn.swift`; the unconditional radix implementation remains here for comparison.

The first experiment showed that radix improves disordered input but loses on sorted and reversed input. The selected production path keeps comparison sorting for small, very sparse, or mostly ordered input. It abandons partial comparison preparation as soon as the run limit is exceeded, then creates a stable radix permutation. NaNs retain the existing fallback.

The driver compares full DataFrame operations and isolated permutation creation. It checks source-row identities, every payload column, null counts and exact Double bit patterns. Coverage includes signed zeros, infinities, subnormals, ordered runs, displaced rows, duplicates and high null densities.

## Commands

```sh
./build.sh
./run.py --binary "$HOME/Library/Caches/SwiftSci/sort-prototype/Build/Products/Release/SortPrototype" \
  --algorithms comparison,baseline --sizes 1000,10000,1000000
```

The historical command label `baseline` calls the current production `sortBy` or `sortedIndices`. `comparison` reproduces the original cached-tuple comparison algorithm. `radix` uses the unconditional experiment. Treat `baseline` as the candidate when reading later result files.

Each measured process performs two warmups and five timed repetitions by default. Runs rotate algorithm order and execute serially. Reference validation happens after capturing peak memory. Full-operation timing includes gathering output columns; kernel timing does not. RSS includes source construction and allocator reuse, so it is not an exact scratch-allocation count.

Results are under timestamped `results` directories. Final runs preserve the driver sources, production diff and executable hash. Earlier exploratory results retain measurements and metadata, with the original executable saved in `../baseline/SortPrototype-original`. See the parent report for accepted results and full-suite validation.
