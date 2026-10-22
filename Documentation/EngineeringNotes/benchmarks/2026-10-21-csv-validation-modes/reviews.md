# Validation-mode review

## Standards

No actionable standards findings. No documented violations or judgment calls worth raising. The two loops implement different validation contracts. The Date specialization is small and supports the measured performance goal. Standard benchmark execution still needs its own validation evidence.

## Specification

No actionable specification defects. The protocol default maps missing and invalid to nil for explicit schemas. The Date specialization uses the same null matcher and parser as its classified decoder. Validating conversions visit original fields and reject the first invalid token. Eligibility, fallback ordering, offsets, chunk-local inference, APIs, optional storage, deployment, framing, limits, and cancellation are unchanged. CPU and memory acceptance require measurements of the exact head.

The fixed point is 297ebd36ef979cf1a5dfafa3f419c052165f2d1e. The reviewed head is a5856aa40f8de2bbcc3653976419202a41222190. Neither reviewer changed code or ran builds.
