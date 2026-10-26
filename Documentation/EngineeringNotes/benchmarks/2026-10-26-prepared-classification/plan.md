# Prepared classification

- [x] Ground existing classifier, pipeline, prepared storage, and test workflow.
- [x] Sketch two distinct designs and cross-judge them.
- [x] Agree by synthesis, no user checkpoint requested.
- [x] Implement the selected design and complete compatibility/numerical checks.
- [ ] Scrap and re-ground only if repeated structural friction invalidates the sketch.

Arena phases: frame, fan out, cross-judge, pick, graft, verify.

Scope: prepared logistic classification fitting and probability/label prediction, with existing iterative CPU/GPU solvers and routing. No new algorithm or agent infrastructure. Preserve legacy callers, named feature ordering, input snapshots and numerical policies. Full local checks on Xcode27 and separate older compiler compatibility before future PR submission. Swift CodeQL is currently unsupported on Xcode27/Swift6.4 per GitHub release notes; never treat that as a passed local scan.

The selected architecture held after adding synchronized pipeline lifecycle state in response to review. No repeated structural failure required replacing the design.
