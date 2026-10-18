# Design rubric

Score each candidate from 1 to 5 for actual API compatibility, synchronous disjoint-write ownership, honest scratch accounting, a small removable private implementation, and independent falsification through public operations. A correctness or lifetime failure disqualifies performance claims.

The configured model list includes unavailable models. The two independent runners and cross-judge use the available configured gpt-5.6-sol model. This is independent-agent review, not independent-model-family evidence.

Caller usage must be real SwiftSci code:

```swift
let rows = column.sortedIndices(ascending: true)
let result = try frame.sortBy("key", ascending: false)
```

No new strategy enum, public options, generic scheduler or storage interface is needed. Separate frozen branches and executable hashes isolate alternatives. Do not introduce a new option only to control the benchmark.
