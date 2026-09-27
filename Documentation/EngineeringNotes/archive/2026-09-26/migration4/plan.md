# Milestone 4 work plan

- [x] Read the migration skill and its principles.
- [x] Inventory every tracked legacy benchmark case and caller.
- [x] Map each case to a versioned contract or a concrete unresolved validation requirement.
- [x] Migrate independently verifiable dataframe and numerical cases in tested units.
- [x] Enforce Kiraa's optional experimental status in the supported-case records.
- [x] Reconcile inventory against executable profiles; do not retire unconverted coverage.
- [x] Run protocol tests, native tests and production-size validation for added workloads.
- [x] Record evidence and remaining boundaries only on codex/engineering-notes.

Completion requires every legacy case to have a reviewed disposition, executable replacements for migrated cases, no unsupported case silently dropped, independent output verification, and honest preservation of cases that cannot yet be compared. Inventory reconciliation alone does not establish full migration.

The v4 runs passed output validation but contained Swift coverage instrumentation. Their timings are diagnostic only. The uninstrumented v5 runs and all four evidence audits passed; the measurement step is closed.
