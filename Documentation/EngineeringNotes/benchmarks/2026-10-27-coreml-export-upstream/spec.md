# Independent multiclass Core ML export correction

Fixed base: upstream main e19db7dda4567c425b7eb002da82e234e6c7980f. Independent of PR89 and PR90. Isolate the existing correction from a1e234d25677d91ce5914062603c41233fe13c09.

Encode a multiclass MLP output as Core ML SoftmaxND with axis -1, matching the last output dimension. Exported probabilities must be finite, normalized, and agree with independent stable softmax, including extreme finite logits. The public fitted classifier export must compile and agree with its native probabilities through prepared inference. Preserve row provenance and budget release. Binary sigmoid and hidden activations must keep their behavior. Public signatures, default output name, class-label compatibility argument, device routing, inference precision and numerical tolerances are unchanged. Clarify existing probability output documentation. No performance, NPU placement or predictive-quality claim.

Copy the existing two regression definitions onto actual upstream and prove baseline failure before applying production files. Fresh full local CI on final exact head is required before submission, including native Debug/Release, main and benchmark workflows, older-compiler compatibility, Python and matching Swift CodeQL. Keep Xcode27 selected and preserve four strict comparator failures and legacy database security finding.
