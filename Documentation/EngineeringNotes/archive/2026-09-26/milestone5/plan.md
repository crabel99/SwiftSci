# Milestone 5 plan

- [x] Read Principles and recover the original milestone contract.
- [x] Frame: retain 27 NIST univariate checks; add H2O-derived grouping and one pinned real-data pipeline. Kiraa stays research-only.
- [x] Verify primary sources and fixture redistribution terms.
- [x] Add explicit input identities, independent output references and compatibility checks.
- [x] Add Swift and Python implementations, small CI cases and representative performance cases.
- [x] Validate all new cases on real workers; rerun existing correctness profiles and contract tests.
- [x] Review evidence independently, commit contribution code locally and archive private records on engineering-notes.

Done means both engines pass every new workload against independent full-output references, corrupt inputs and mismatched dataset/workload pairs fail, the unchanged NIST and migration smoke profiles still pass, and the contribution history contains no private notes. No claim of full H2O reproduction or general numerical certification.

Changes use the existing contract and worker lifecycle. No production API changes are planned. Existing native library tests need repeating only if production code changes; build the actual uninstrumented Release worker and run the affected operations regardless.
