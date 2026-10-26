# Complete public numerical workflow template

- [x] Ground existing public APIs and check for an existing runnable example. None combines prepared PCA and prepared logistic classification.
- [x] Use existing public Imputer and StandardScaler. StandardPreprocessingPlan has no public general transform method; add no library API or package-access workaround.
- [x] Implement a small external template: split supervised rows before fitting, training-only imputation/scaling/PCA, prepared classifier training, then held-out predictions associated with original rows. Include missing and valid-NaN features, a constant feature and reordered/duplicate held-out rows.
- [x] Compile and run prepared and separate legacy consumers on qualified integration c4de6cc866. Ordinary public imports only. Frozen object/build/source identities verified.
- [x] Independently verify scalar preprocessing, closed-form two-feature PCA and scalar64-step logistic updates with declared1e-12 absolute/relative tolerance. Maximum observed error4.45e-16; legacy/prepared outputs match exactly. This toy fixture is integration evidence, not statistical-quality/performance qualification.
- [ ] After final agent benchmark completes, repeat both consumers against final0e163519 library objects and stamp that source, without changing source or competing with benchmark timing.
- [ ] Verify the executable package build separately if practical, preserve any limitation, review template/oracle, publish evidence and deliver a copyable template.

Initial compile attempt incorrectly called rowValues on a matrix. The actual public method is on PreparedNumericBatch. Removed that unnecessary matrix conversion. Initial compile log and source retained; the corrected file compiled and ran successfully. No production source changed.
