# Architecture judgment

Use shared ordered keys as the implementation base. It reuses preparation across comparison and radix without a raw allocation owner. This is a design recommendation, not acceptance of a performance claim. Neither candidate supplies runnable code or measurements.

Scores are zero to five for the six contract criteria. Five means the design addresses the criterion convincingly; zero means no evidence supplied.

| Contract criterion | Shared keys | Delayed tuples |
| --- | ---: | ---: |
| 1. Exact ordering and fallback | 4 | 4 |
| 2. CPU, reads, memory, sparse costs | 3 | 2 |
| 3. Monotonic and radix gains across disorder positions | 4 | 3 |
| 4. Public API and policy constraints | 5 | 5 |
| 5. Small private implementation and shared kernel | 4 | 2 |
| 6. Rerunnable measurements and full checks | 0 | 0 |

Both preserve scalar monotonic detection, native integer dispatch, signed-zero equality, stable null suffixes, and the exact original comparator on any valid NaN. Shared keys must test the sentinel proof in both directions, including infinities and subnormals. The excluded IEEE NaN ranges leave UInt64.max unavailable to valid transformed keys. Neither proposal should assign NaNs an invented order.

Shared keys derive their density condition from 8N physical-row keys versus 16V native tuples. Retaining tuple preparation below that crossover avoids charging sparse comparison inputs for a physical-row key array. Keep the existing minimum-size and sparse bypass. Test the crossover on either side, with nulls distributed throughout the prefix and suffix. The calculation bounds preparation storage; allocator capacity and sorting workspace still need measurement.

The shared candidate removes the discarded-cache problem even when radix selection occurs late. First disorder at position k still costs approximately N+k source reads, plus a key scan, so late disorder may save little CPU. Indirect comparison reads may lose to tuple locality. Its radix kernel may also copy V indices back from scratch where the existing implementation swaps buffers. Measure this copy explicitly before claiming retention of radix gains.

Delayed tuples correctly identify that backward scatter avoids overwriting unread native values because row >= ordinal. However, its raw Double-to-UInt64 transition needs a legal binding and lifetime implementation. Rebinding the entire region before all Double reads finish is unsafe. Growing V values to N keys may temporarily retain both allocations, especially near the sparse boundary. That peak contradicts any unconditional memory-neutral promotion claim.

The delayed comparison path also introduces a valid-ordinal permutation alongside native values and source rows, followed by a mapped result. Unless those lifetimes are redesigned, it retains roughly another 8V bytes over the original tuple preparation during mapping, before sort workspace. This omitted cost weakens its stated memory case.

Graft the delayed candidate's explicit early/middle/late NaN and disorder validation cases into the shared plan. Reject the raw owner and ordinal comparison representation. Require buffer borrowing that avoids ArraySlice copy-on-write, scopes rejected preparation out before fallback allocation, and preserves the null suffix during radix completion.

Before acceptance, run same-input exact-permutation checks and CPU/peak-memory measurements for early, middle, late, and long-run disorder, both density crossover sides, both directions, and both storage forms. Run the full module checks. Keep resulting notes only on engineering-notes.
