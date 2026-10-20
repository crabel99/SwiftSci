# Narrowed String/Bool follow-up

This follow-up compares baseline `d23bf7cac92fe9f9c10bd98046ca8ade354b5a3c` with `546510bb7d` on the preserved serial-specialization branch. The new commit removes only the explicit Date dispatch. The String/Bool helper and generic fallback remain.

All fourteen cases pass, including two Date shapes added after the original regression was found. See [results](RESULTS.md), [plan](PLAN.md), [raw evidence](evidence.tar.gz), and [the audit](audit.json). The parent [report](../README.md) states the decision and scope limits.

Run the same prepare, build, run, summarize and audit sequence described in the parent report. `run-regressions.py` compiles the existing three tests with Swift Testing and links the exact Release dataframe object measured here. Its test source is copied without modification from the candidate branch. The testing launcher is diagnostic tooling only.
