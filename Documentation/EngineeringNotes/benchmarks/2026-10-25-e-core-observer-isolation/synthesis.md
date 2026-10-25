# Observer profile synthesis

Use the ordinary controller with background-only workers. Independent review by gpt-5.6-sol selected the same base against the six recorded criteria.

The profile is named `e-core-workers-observer-v2`. It preserves the old `e-core-application-v1` entry point and receipt rules. Workers remain subject to zero P-core user ticks. Controller and observation costs remain charged and reported separately.

Take absolute monotonic sampling deadlines and per-scan process start identities from the dedicated-process design. Keep scan start/end anchors and the fixed 50 ms coverage gate from the controller design. Add raw controller QoS evidence so an inherited background clamp cannot silently masquerade as ordinary scheduling.

Reject a second observer process for now. Its protocol and cleanup costs are unjustified until the smaller design demonstrates a remaining controller or GIL bottleneck. Neither scheduling profile establishes affinity. Actual worker P/E counters decide placement acceptance.

Physical footprint is additional evidence. RSS retains its existing definition and twin gate. Reusable memory is unavailable through this unprivileged cross-process probe and is omitted.

Pure coverage checks pass after correcting two fixture errors: the queue-clipped hole is 79 ms, and a slow scan needs a later final bracket to distinguish slow coverage from malformed boundaries. Real workload coverage remains unverified.
