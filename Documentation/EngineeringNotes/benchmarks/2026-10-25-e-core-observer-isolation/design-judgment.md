# Design judgment

## Verdict

Use `controller-design.md` as the base for the new named experimental profile, `e-core-compute-observed-v2`.

It meets the approved policy: every application worker must record zero P-core user time, kernel P/E time stays separate, and the observer may run outside the worker clamp. It also leaves `e-core-application-v1` intact and reproducible. The process design preserves more of v1 inside v2 than the requirement asks for, then pays for that choice with a socket protocol, a second process, split cleanup ownership, and another accounting interval.

Do not use the isolated observer process unless the controller design later fails its frozen coverage gate and evidence points to GIL or controller-path delay. The present evidence shows scheduler starvation under the inherited background clamp. It does not justify the second process yet.

## Criterion score

| Criterion | Controller base | Isolated process |
| --- | --- | --- |
| Strict worker E-user time | Pass. Every preflight, timed, and postflight worker gets the fixed background launch policy, and each worker receipt still rejects P-user ticks. | Pass. Worker and controller retain the old strict audit. Strict controller placement is extra policy, not an approved requirement. |
| Declared observer scheduling | Pass with a launch condition. The v2 profile declares an ordinary controller and sampler by omitting the benchmark's background clamp. The receipt must identify that profile and retain scheduling evidence. | Pass in intent. The observer launches before the controller clamp, but its claimed default scheduling still depends on the wrapper's inherited state. |
| Observation CPU and P/E cost charged | Stronger base. One widened controller CPU interval can contain queue setup, boundary scans, sampler work, dispatch lanes, worker stats, and core reads. Raw worker and controller P/E counters remain separate. | Incomplete. The per-session observer delta does not yet assign observer startup, inter-session work, receipt encoding, shutdown, or wrapper protocol CPU. Self-snapshots also leave boundary work outside their own P/E interval. |
| Poor sampling coverage blocks qualification | Pass. It persists queue and scan start/end anchors, rejects missing brackets, backward time, empty samples, scan duration over 50 ms, and every effective gap over 50 ms. | Revise before use. A single timestamp per sample cannot expose a scan that itself took too long, and `max_sample_gap_ns` alone cannot prove boundary coverage. |
| Jobs, data, native pools, and twin limits stay fixed | Pass. The new profile changes controller and worker launch policy only. It retains four callers, the full engine panel, identical twins, native pool defaults, and the existing CPU, wall, and RSS limits. | Pass on paper. It retains the old compute launch tree and limits, but adds observer competition and lifecycle behavior that must remain identical across every condition and twin. |
| Smallest maintainable interface | Win. One named profile and a fixed worker launch rule fit the existing worker, batch, and audit owners. | Loss. `ObservationClient.measure` is a tidy facade, but it hides a substantial protocol and creates competing ownership of worker termination, PID identity, session state, and CPU receipts. |

## Grafts into the base

Take three ideas from the process design without taking its process boundary.

1. Use absolute monotonic sampling deadlines. Skip missed deadlines instead of issuing catch-up bursts that could make a bad interval look dense.
2. Record each worker's start identity when sampling begins and recheck it during scans. A failed read, exit, or identity change invalidates the batch and uses the existing `Worker` cleanup path.
3. Make the profile contract explicit about observer scheduling and role accounting. Report worker compute separately from `controller/observation`; the controller number includes dispatch lanes and bookkeeping, so labeling all of it `observer` would be false. If QoS CPU buckets are available from the same supported counters, retain them as evidence, not as a substitute for P/E placement checks.

Keep the base design's scan start/end anchors, exact legacy-sample projection, coverage audit, separate raw role counters, and rejected-run receipt. Do not graft the socket protocol, observer-owned `killpg`, or the requirement that the v2 controller also have zero P-user time.

## Implementation conditions and risks

- A free-form `launch_prefix` leaks scheduler representation through `compare.py`, `preflight`, and `run.py`. Pass a validated named profile or a closed profile-derived worker launch value. Callers must not supply arbitrary scheduling commands.
- Verify that `taskpolicy -c background` replaces itself with the worker. If it keeps a wrapper process, the recorded PID, core counters, stats target, process group, and cleanup target will be wrong. This check must cover native and Python workers before a panel run.
- Removing the explicit background clamp does not reset a clamp inherited by the wrapper. This host does not accept `taskpolicy -c default`. The v2 launcher must either establish an ordinary launch context by another supported mechanism or record enough evidence to reject a controller that still ran under the background policy.
- Move `time.process_time_ns()` start before the first v2 batch observation action and its end after the final scan, worker stats, and core reads. Keep queue wall anchors separate. The P/E counter interval will not equal charged CPU because the boundary reads cannot include all of their own execution; report it as a role-split cross-check, as the design proposes.
- Change `user_e` to `user_ticks - p_user_ticks` before allowing controller P-user ticks. Otherwise the report double-counts controller P-user time. Worker validation must still reject any nonzero `p_user_ticks`.
- Define coverage from raw intervals, not sample count or a saved maximum. Audit the leading edge, every blind interval between scans, the trailing edge, and each scan duration. Recompute the legacy RSS pairs exactly from v2 scan records. A 200 ms hole must fail even if samples cluster elsewhere.
- Preserve the old parser, wrapper behavior, receipt rules, and report meaning for v1. Never reinterpret old records under v2. Cross-profile performance comparisons are invalid because v2 moves controller dispatch and collection to ordinary scheduling and widens its CPU charge interval.
- Physical-footprint reads can add enough work to change cadence. Charge that work and fail the v2 batch if the required read or coverage check fails. Do not relax the 50 ms gate, native pools, panel, or twin limits to rescue a run.

The base is ready for implementation only after profile and worker-launch fixtures establish these contracts. A real panel may qualify only when every engine and twin passes the same persisted coverage audit.
