# Foundation standards review

Reviewed `git diff da03a63015...5cc699a7ef` against `CONTRIBUTING.md`, the proposed `Documentation/FoundationContract.md`, and the Fowler smell baseline. Also inspected the final join specialization delta against `edece095de`. Read-only review. Source validation remains pending.

No actionable documented-standard violations or design-smell findings.

- The final join dispatch retains the established optional-array inputs for noncompact typed columns. Four explicit Double cases send compact collections or optional arrays into one shared hashing kernel. This avoids duplicated join algorithms and permits concrete collection specialization without a storage switch on every optional-array access. The cases represent existing combinations rather than speculative extensibility.
- Making the existing `CompactColumnValues` adapter internal permits reuse across dataframe files and adds no public API. The collection constraints preserve matching optional element types and integer indices. The private kernel assumes zero-based input indices and matching supplied counts. Every current caller provides a full array or the zero-based compact adapter, so that assumption is satisfied. Passing array slices in a future internal change would need review.
- The hashing body, FIFO match order, null behavior, and equality comparisons are unchanged by specialization. This source inspection identifies no behavioral difference for optional, compact, or mixed Double inputs. It does not establish performance parity.
- Grouped aggregation retains its numerical loop, compensation, missing-value handling, and reduction order. The private value-access closure serves existing storage variants.
- Empty join assembly reuses column gathering rather than returning a schema-free frame. Tests cover compact grouping, special join keys, empty schema, validation precedence, and retained provenance admission. Their numeric expressions remain small and explicitly typed.
- The contract distinguishes intentional compatibility copies, memory estimates from RSS, numerical policy from full conformance, and device permissions from placement guarantees. Its claims match the inspected preparation and ownership code.

No tooling-enforced checks were treated as findings. Compiler compatibility, test success, optional-path performance parity, and measured allocation improvement require the parent's pending validation. Unqualified diagnostic timing differences are not proof of regression or its absence.
