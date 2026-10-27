## Standards

No actionable findings in `git diff e19db7dda4567c425b7eb002da82e234e6c7980f...bdf2b57a66330c331bb870a4d762bb94f7dae0a9`.

Reviewed CONTRIBUTING.md in full, the required subtract-before-you-add skill, and the code-review smell baseline. The correction replaces the unused legacy softmax field constant with the required SoftmaxND field and adds only its axis-field definition. Encoding remains in the existing protobuf builder. Existing activation cases keep their current representation, with the selected outer field made explicit. No additional public abstraction, validation layer or dependency is introduced.

The two regression definitions live under the correct test target and use existing compiled-model fixtures. One compares real exported-model inference with independently computed stable softmax across ordinary, zero and extreme finite logits, including reordered/repeated source rows and different batching. The other exercises fitted public classifier export against native probabilities. Both check release of the existing memory budget. Fixtures remain small and explicitly typed where numeric construction needs it.

Public documentation now describes probability outputs and the existing class-label compatibility argument. Public signatures and defaults are unchanged. The small field-selection switch does not warrant a repeated-switch or duplication finding; moving it into another abstraction would add complexity without a second consumer.

No hard documented-standard breach or meaningful heuristic smell was identified. Tool-enforced concerns were excluded. This read-only review performed no builds, numerical checks, security analysis or remote actions. It does not establish that separately running native, benchmark, compatibility or security qualification has passed.
