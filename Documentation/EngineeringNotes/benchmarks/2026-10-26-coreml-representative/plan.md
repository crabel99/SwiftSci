# Representative Core ML workflow

- [x] Trace existing production adapter, trained-model controllers and historical evidence.
- [x] Reproduce the public multiclass export obstacle with Core ML itself.
- [x] Correct shared softmax serialization with a failing-before runtime regression and independent probability checks.
- [ ] Reuse frozen real-data models and existing inference tools; record existing train-only scaling controls and complete adapter inference with explicit phase boundaries. Full raw-input-to-pool composition is already covered by the prior fused workflow; do not duplicate it.
- [ ] Inspect actual Core ML device events, keeping planned placement and instrumented timing separate.
- [ ] Run applicable local checks, compiler compatibility, review and published qualification records.

The library already supplies the execution interfaces. Do not add another model runtime, matrix protocol, memory manager or task scheduler. Existing numerical tolerances, admission contracts, dependency pins and device routing remain. New source contributions must have a concrete consumer need. Preserve primary checkout and unrelated notes; retain Xcode 27 and verify older compiler compatibility per process.
