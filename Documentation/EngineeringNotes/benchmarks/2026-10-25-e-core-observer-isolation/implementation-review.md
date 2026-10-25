# Implementation review

Reviewed the implementation commit `84778af52a` and its follow-up working-tree fixes against `controller-design.md` and `design-judgment.md`. The fixed point was `af4e2cd45b`.

## Verdict

No blocking correctness finding remains after the review fixes. The v1 profile remains strict and keeps its whole-tree clamp. The v2 profile clamps every worker, requires zero worker P-user time, charges controller and observation CPU, reports controller P/E and QoS evidence separately, and rejects poor raw sampling coverage. Jobs, data, engine membership, native pools, caller count, and twin limits remain unchanged.

Do not treat this review as performance qualification. The native checks and measured panel still decide whether this host satisfies worker placement, controller QoS, and the 50 ms coverage gate.

## Standards

Two findings were fixed during review.

1. **Resolved P1, direct launcher import.** `run.py` introduced package imports that failed under the documented `python3 Benchmarks/CPUThroughput/run.py` entry point. `run.py:20-25` now adds the repository root before importing `Benchmarks.CPUThroughput`, and `test_cpu_observation_lifecycle.py:49-61` exercises the direct-script import with no `PYTHONPATH`.
2. **Resolved P2, absolute cadence drift.** The sampler reset an overdue deadline to `now + interval`, which moved the sampling phase after every overrun. `observation.py:6-7` now advances the prior deadline by whole periods, and `run.py:146-154` skips missed slots without catch-up bursts or phase drift. `test_cpu_observation_coverage.py:27-30` covers on-time and overdue cases.

No documented-standard breach or remaining code-smell finding warrants a source change.

## Specification

Two correctness findings were fixed during review.

1. **Resolved P1, incomplete controller CPU charge.** The first implementation ended `process_time_ns` charging before coverage recomputation and core receipt validation. `run.py:283-296` now performs both validations before the final CPU snapshot, then replaces the provisional controller delta in the raw observation and charged summary. Final serialization and disk writes remain outside the interval and the report states that boundary.
2. **Resolved P1, rejected receipt lost evidence.** Coverage or identity validation used to fail before any complete result receipt was retained. `run.py:273-302` now assembles the raw observation and core receipt first. On rejection, `failure.json` keeps that record plus the samples and scans. `test_cpu_observation_lifecycle.py:81-90` checks the retained anchors, jobs, runtime identities, core evidence, and worker cleanup.

The remaining contract checks pass static review:

- `core_usage.py:157-158` applies the strict interval audit to every worker under both profiles and relaxes only the v2 controller. E-user time subtracts P-user time before reporting.
- `run.py:51-65` derives the worker prefix from the closed profile set and rejects a launch whose ready PID differs from `Popen.pid`. The parent task's native and Python live checks passed PID, process-group cleanup, and zero P-user checks.
- `core_usage.py:161-169` requires positive controller QoS evidence and rejects background, maintenance, or utility controller CPU in v2.
- `observation.py:10-60` recomputes coverage from raw scan intervals. It checks frozen policy values, queue and charge anchors, non-overlap, worker PID order, stable process-start identities, exact legacy RSS projection, leading and trailing brackets, scan duration, and every clipped interior gap.
- `compare.py:200-207` appends every coverage failure to the unchanged twin-control flags, so a hole blocks qualification without hiding the completed queue.
- The v1 parser still accepts receipts without the new policy field. The default launcher still selects `e-core-application-v1`; v2 requires an explicit flag and persists its named policy.

The CLI uses `--observer-isolation` and the persisted name `e-core-workers-observer-v2`, rather than the sketch's `--core-profile e-core-compute-observed-v2`. This is a naming difference, not a policy relaxation. Rename it only if the exact draft spelling is part of the external interface contract.

One host-specific risk remains by design. `taskpolicy` is a scheduling policy, not affinity. The runtime PID check, per-queue worker counters, controller QoS counters, and coverage audit turn a host mismatch into a failed run instead of an accepted result.

Summary: Standards has zero open findings after two fixes. Specification has zero open correctness findings after two fixes, with one nonblocking interface-name difference and one explicitly audited host risk.
