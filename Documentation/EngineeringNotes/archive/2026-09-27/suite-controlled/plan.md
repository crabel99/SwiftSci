# Suite-first implementation

The user clarified the order on September 27, 2026. Complete the testing and certification branch before repairing production algorithms. Then use a separate repair branch with one commit per error. Establish the formal performance baseline after those repairs pass the completed suite.

This run continues stage 3. It adds independently checkable fixtures for existing APIs without changing production behavior. Existing numerical failures remain failed. No measured timings from this phase are a formal performance baseline.

- [x] Read the workflow principles and current dataset plan.
- [x] Frame scope and record the user-required order.
- [x] Review existing inference, clustering, forecast, search and explanation APIs for controllable inputs.
- [x] Implement the supported exact fixtures and explicit capability boundaries.
- [x] Verify generation, malformed-input rejection and both real workers.
- [x] Review evidence with a separate model, commit suite changes, and archive notes separately.

Done for this run means every selected fixture has immutable inputs, independent expected outputs, declared tolerances and complete worker validation. Unsupported controls must be recorded as blockers rather than patched on this branch. Completion of stage 3 does not complete the full suite.

Verified contribution commit: `279c01433dfd76e6768c72c7af7d2950fa5d3944`. The ten supported stage-3 fixtures are implemented. Shared multi-cluster initialization and broader sampled explanation/forecast contracts remain outside this profile. Stages 4 through 7 of the full strategy are still pending.
