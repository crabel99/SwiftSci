# Shared key preparation synthesis

## Caller contract

Keep column.sortedIndices and DataFrame.sortBy unchanged. No public model, storage policy, precision, or worker setting changes.

## Base decision

Choose candidate-shared. Parent scoring on the six contract criteria is shared 5/4/4/5/4/3 and delayed 4/2/3/5/2/2, on a five-point scale. The independent judge also selects shared keys. These are design judgments, not performance acceptance.

The shared-key design keeps Swift Array ownership and makes one existing IEEE encoder authoritative for comparison and radix. It avoids a disposable full tuple cache if radix is selected late. Admit this representation when physical-row UInt64 keys cost no more than the valid native tuples they replace, expressed as nullCount <= validCount on this 64-bit target. The existing small/sparse policies remain unchanged. This is a conservative bound on the key buffer alone, not proof of an optimal whole-sort density crossover. The shared representation also removes missing-row storage, so whole-operation peak memory can favor it below that bound; sparse comparison locality still needs a separate experiment.

## Grafts and rejections

Retain the delayed candidate's requirement to finish NaN validation after radix intent and to measure transient peak memory during late selection. Shared preparation already satisfies both structurally; the broader adversarial controls make them verifiable. Reject its raw storage owner, rebinding, grow/realloc lifecycle and extra valid-ordinal buffer. They add ownership and memory costs without an established need.

Keep the shared candidate's null sentinel, valid-prefix/null-suffix output and one radix kernel. This deliberately accepts a key-array scan and possible valid-prefix copy-back. Test their CPU and memory costs rather than treating reduced source reads as sufficient proof.

## Implementation sketch

The production entry keeps the scalar monotonic detector. At the first direction change with an eligible key layout, prepare the already-read prefix without recounting runs and continue the suffix with saved scalar state. Preparation returns nil for a valid NaN. Otherwise it returns physical-row keys, differing bits and the run decision. Partition one result array from those keys, stable-sort its valid prefix by UInt64 keys or use the current radix passes. Leave missing indices in source order at the end.

For ineligible sparse columns, finish the existing scalar classifier and use existing tuple comparison. If it selects radix, feed full key preparation to the same kernel. Monotonic inputs retain their existing direct permutations.

## Verification

Three new small test functions pass against e1f5f8c305 before implementation. Measure early/middle/late first disorder, late radix selection, both sides of the byte crossover, missing values, existing ordered/random controls and real observation workflows. Preserve rejected direct-index trial def5a57c59 and its unqualified screening evidence. No source implementation has performance acceptance yet.
