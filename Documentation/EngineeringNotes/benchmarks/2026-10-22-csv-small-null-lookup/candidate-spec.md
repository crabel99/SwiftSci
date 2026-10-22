# Bounded String null lookup

Reduce process CPU work for complete CSV reads. Retain empty-set lookup and hashed lookup for more than two null tokens, including the ten-token default. Use no more than two direct Swift String equality comparisons for one- and two-token sets. Preserve canonical Unicode equality, exact null membership, quoting, malformed UTF-8 decoding, native output values, row order, eager and streamed reads, inferred and explicit columns, and both existing column conversion policies.

Do not change parsing grammar, numeric conversion, CSV batch size, concurrency, caches, or public APIs. Review CPU and peak RSS against the matching frozen parent policy. Keep engineering notes and experimental evidence off the implementation branch.
