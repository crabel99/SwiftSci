# Five-hour SwiftSci continuation

Deadline: 2026-10-27 01:27:23 UTC. Start: 2026-10-26 20:27:23 UTC.

## Workflow

- [x] Read the Principles section of poteto-mode in full and apply subtract-before-you-add.
- [x] Phase A: Frame. Resume verified source a1e234d25677d91ce5914062603c41233fe13c09 in an isolated checkout. Preserve PR 89 and primary worktrees. Five hours permit several verified units; unfinished work remains explicitly open.
- [x] Phase B: Design the workflow. Ground existing public pool and model controllers, distinguish historical completed trials from missing representative coverage, and select the smallest experiment before adding code. See how-synthesis.md. Reuse the generic native stress worker and task-local preparation/full-output probes; production APIs need no initial change.
- [ ] Phase C: Run the loop. For each unit, state the hypothesis, capture current behavior with an existing tool or minimal probe, measure complete outputs and ownership, and keep only demonstrated corrections.
- [x] Unit 1: Qualify representative weighted ML Programs with typed Float16/Float32 I/O using frozen real-data models and independent references. Completed24 reduced-precision cases and12 full-Float32 controls. Reduced precision exceeds the strict reference; full-Float32 controls meet it. Application suitability remains unassessed.
- [x] Unit 2: Qualify public concurrent pool and fused/prepared preprocessing on those artifacts. Completed864 reduced-precision and432 full-precision workflow predictions plus52 concurrency/sustained cases and13,621,364 requests. Row provenance, retained outputs, error recovery and reservations pass.
- [x] Unit 3: Inspect actual Core ML execution events for representative artifacts and allowed-device policies. Eight recordings show215,448 positive CPU dispatches and no other target device dispatch. No Neural Engine acceleration is established. One saved recording recovered after a driver timeout; full events and target success validated, failure retained.
- [ ] Unit 4: Correct only reproduced defects; add meaningful regressions, run applicable full local CI and Swift 6.3.3 compatibility before source publication. No source mutation during worker build or qualification.
- [ ] Unit 4a: Converge the complete prepared PCA PR89 stack with the later classification/GPU/CoreML source on a separate integration branch. Verify both siblings' behavior together; leave the PR89 branch unchanged.
- [ ] Unit 4b: Correct the documented false100% success line in the documentation checker, retaining placeholder policy and describing the declaration scan honestly. Prove with tiny CLI fixtures and actual source output.
- [ ] Unit 5: Reconcile the current engineering-record index and handoff. If time remains, evaluate the evidenced generic LLM completion-information gap from llm-completion-grounding.md as a separate bounded library unit, without company/server/runtime work.
- [ ] Phase D: Keep the audit trail. Append decisions and completed-unit evidence to decisions.tsv throughout the run.
- [ ] Phase E: Verify and hand back. Independent standards/spec and audit reviews, truthful completion inventory, separate engineering records, and updated handoff. Stop starting work at the deadline.

## Falsifiable completion criteria

Each qualified artifact has frozen source, binary, model, input and reference identities. Complete finite outputs are compared with the existing independent Double requirement, abs(error) <= 1e-5 + 1e-5 * abs(reference), without changing it to fit precision. Public direct/prepared/pool paths agree as required by their existing transport contract. Pool and input reservations drain and invalid-input recovery succeeds. Application task scores and precision differences are separately reported; no suitability threshold is invented after observing held-out results. Every claimed device dispatch has inspected runtime-event evidence. Source changes have passing appropriate local checks before publication, with unsupported tools disclosed.

Reuse prepare_models.py, existing model/pool/concurrency workers, StandardPreprocessingPlan and existing phase measurements. No new runtime, scheduler, memory manager or general measurement framework. Rigor is high for numerical claims and concurrent ownership; exploratory timings remain observations, not a performance baseline.

## Throughput checkpoint

Grounding is split across two independent read-only slices: production adapter/data ownership and existing controllers/history. The main agent prepares the smallest real artifact probe. Builds may run alongside read-only work, but numerical timing and tracing run without concurrent builds. If existing mechanisms cover the unit, reuse them and publish new qualification evidence rather than add code. Reserve the last 45 minutes for checks, review, publication and handoff; advance another unit only when it ends in a verifiable state before that window.
