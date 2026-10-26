# Standards review

Reviewed the three modified serialization files and the untracked `Tests/SwiftMLTests/CoreMLMulticlassExportTests.swift` against baseline `53063789b1893b28250ea239d5fdca4fed84c4c9`.

**Documented rules:** No actionable violation found. The implementation remains within SwiftML serialization, preserves public signatures, and documents the changed probability-output behavior (`CoreMLExportable.swift:304–310`, `CoreMLExporter.swift:512–520`), consistent with CONTRIBUTING.md's module-boundary and public-API documentation requirements. The new tests reside in SwiftMLTests, reuse the existing compilation helper, use small explicitly typed fixtures where needed, and exercise both supplied weights and a fitted public classifier (`CoreMLMulticlassExportTests.swift:10–70`). This matches the contribution requirements for target-local regression tests and manageable Swift numeric fixtures.

The required subtract-before-you-add principle is satisfied: the unused legacy softmax field constant is replaced rather than retained, and the correction adds no public abstraction or speculative validation (`CoreMLProtobuf.swift:62`, `:85–87`, `:692–711`).

**Heuristic judgment:** No change warranted under the supplied smells. Repeating the activation-field assignment in the existing single dispatch is small and explicit; extracting it would introduce navigation for little benefit. Test setup overlap is modest, while the two tests establish different contracts. The serializer remains the proper owner of protobuf field selection. Existing string-based activation dispatch and unknown-activation behavior predate this diff and are not findings against this patch.

**Correctness observation:** The softmax branch emits its own layer variant and explicitly encodes the last axis, while existing ReLU/sigmoid/tanh branches retain their prior encoding (`CoreMLProtobuf.swift:695–711`). The independent reference includes extreme logits and repeated/reordered rows (`CoreMLMulticlassExportTests.swift:15–41`), providing meaningful coverage beyond compilation.

This is a static review. Full tests, numerical qualification, and older-compiler validation remain the parent task's responsibility before submission; their completion was not inferred here.
