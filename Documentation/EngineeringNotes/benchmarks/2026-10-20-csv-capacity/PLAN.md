# Quoted CSV allocation diagnosis

October 20, 2026. Historical and current readers reproduce oversized output arrays. Pointer instrumentation shows that a column reserving 250000 elements receives the same address previously used by a 401406-element parser field buffer. A standalone Swift Array program reproduces the reuse without SwiftSci.

Compare the current source at 546510bb7d with a throwaway exact-count prepass. The prepass scans the actual input using the same quote and escape rules; it does not receive fixture sizes or a supplied schema. Both readers perform normal schema inference and the same output validation. The extra scan is inside every measured call. Do not use instrumented builds for timing.

Five alternating timing pairs, two warmups and five measured samples per process. Three separate memory pairs, one operation without warmup. Measure CPU user+system and elapsed time including call and output release; check all values outside timing. Capture live heap and RSS before validation. Cases: 100000, 250000 and 1000000 quoted rows at width four; 1000000 quoted rows at width two; 1000000 unquoted rows at width four.

This experiment asks whether avoiding growing parser arrays improves overall resources. A retained-memory win alone does not justify a more expensive default. Preserve failures and any CPU tradeoff. Do not alter production code, push a branch, or claim energy savings.
