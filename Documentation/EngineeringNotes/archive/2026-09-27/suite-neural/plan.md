# Fixed neural inference suite increment

1. Read the working principles and inspect existing neural APIs.
2. Define bounded fixed-weight Float32 inference cases with independent scalar answers. Review weight loading, causal masks, positional encoding, cache reset, device selection and execution completion.
3. Add reproducible fixtures, strict boundary validation and runtime adapters without changing production algorithms.
4. Verify controller tests, the actual Release worker on explicitly requested devices, negative controls and existing smoke coverage. Preserve production failures.
5. Obtain independent review, commit only suite files locally, and archive engineering decisions and evidence only on engineering-notes.

Done means all declared cases are runnable, validate complete outputs and record failures honestly. A passing bounded case does not establish trained-model quality, all neural APIs, or a performance baseline.
