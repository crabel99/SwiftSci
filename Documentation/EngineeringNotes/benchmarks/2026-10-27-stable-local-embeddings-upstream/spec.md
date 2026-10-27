# PR94 safe-test failure correction

Observed failing head a9732e04f5c5ca16fc6aadf39d0707fe85721246, base 01d48cbcd940c886546b2bb8d6b177d9b7a0e277. Hosted safe tests failed only at ZeroShotTextClassifierTests.testZeroShotWithLocalEmbeddingEngine: food versus technology. Python dependencies and all benchmark/security/build jobs passed. The only PR94 changes are two Python requirements files; NLP source/test bytes equal base.

Requirements:
- Replace LocalEmbeddingEngine's process-randomized String.hashValue coordinates/signs with the existing deterministic fnv1aTokenHash. Reuse each computed hash; use magnitude to avoid abs(Int.min) overflow. Keep dimensions, normalization, batch APIs and public signatures unchanged.
- Add independent ASCII/UTF-8 golden coordinates that fail against old actual production code and remain identical across fresh processes.
- Correct the local zero-shot integration fixture to exercise explicit text overlap with its label hypothesis. A hash projection without learned weights cannot establish semantic category accuracy. Keep classification/ranking and calibrated-score checks.
- Document coordinate change and rebuilding stored embeddings/indexes. Do not claim compatibility with earlier randomized vectors or learned semantic quality.
- Leave PR94 requirements updates, all unrelated source, workflow/Codecov policy and numerical tolerances unchanged. Deliver a focused fix on actual main from our fork because upstream permissions are read-only. No comments, reviews, direct upstream writes or merge are authorized.
- Run full applicable local native, workflow, benchmark, compatibility and security checks on the final head before submission; retain known comparison/security/cold-start limitations and the separate coverage-export follow-up.
