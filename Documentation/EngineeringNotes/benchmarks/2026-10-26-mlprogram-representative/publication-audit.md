# Publication audit of representative ML Program records

reviewed by gpt-6-astra

This review covers the publication package under `/private/tmp/swiftsci-mlprogram-20261026/records`, its README, packaging and verification scripts, transformation maps, and scoped failure receipt. It does not qualify later source integration or other work in the five-hour run. The earlier substantive review remains in `audit-interim.md`.

No blocking evidence, recovery, or privacy finding remains in the revised package. One low-severity wording correction is still needed in the reviewed README: the verifier checks published decompressed digests after hostname redaction, not every original decompressed digest. The original digests remain provenance entries. Replace "every compressed original digest" with "every published compressed payload and its decompressed digest" or equivalent before publication.

## Checks completed

- Ran the standalone published verifier. It passed 428 manifest entries, 69 compressed payloads, eight replayed trace cases, and 215,448 positive CPU dispatches. These are retained-data checks; no inference, stress test, or profiler was rerun.
- Compared all 14 transformations with local original evidence. Six files remove the exact hostname, including three compressed nested provenance files. Eight TOCs remove device name and UUID. Original, published, and applicable decompressed hashes match the maps. Each transformed payload differs only by the declared replacement or XML attribute removal.
- Scanned every published file and every decompressed payload for the original hostname, TOC device name, and device UUID. There were zero matches. Authorized `/Users/crabel` paths remain, as the README explicitly states. This is selective redaction, not a claim of anonymity.
- Matched `traces/initial-driver-failure.json` to the exact `CommandExecution` at scoped transcript line 584. Timestamp, command, status, output, exit code 1, and duration match. Its session-event hash matches the original JSONL line. It retains both the 92-second timeout and cleanup `PermissionError`, while the successful target log remains separately intact. The full unrelated transcript is not published.
- Confirmed `traces/recordings.json` is byte-identical to the captured ledger. The verifier updates TOC digests only in its temporary replay copy, after checking the original-to-published mapping. The original inspector changes only at the export block, replacing fresh trace export with existence checks for retained exports. Replay reproduces event counts, device counts, model names, examples, measurement intervals, target PIDs, result hashes, and event-export hashes.
- Checked the README's substantive limits. It distinguishes Float16 computation from Float32 transport, full-Float32 controls from reduced-precision artifacts, successful integration from strict accuracy and application suitability, and allowed devices from observed dispatch. It discloses the weak wine model, bounded stress duration, zero persistent-cancellation checks, cache and performance limits, local raw trace retention, and historical CI reuse. It does not claim qualification of the later integration source.

## Supplemental comparison of saved output variants

For each process, I selected its direct normal output and permuted that vector using the recorded reverse or duplicate-selection map. I compared every saved non-normal sample against that permuted baseline. The counts include repeated routes, callers, and processes; they are not counts of independent observations.

| Artifact group | Compared values | Maximum absolute difference | Exceedances of `1e-5 + 1e-5 * abs(permuted normal)` | Processes with exceedances |
|---|---:|---:|---:|---:|
| Reduced precision | 129,168 | 0.015625 | 1,485 | 18 of 24 |
| Full Float32 | 64,584 | 9.5367431640625e-7 | 0 | 0 of 12 |

The largest reduced-precision difference occurs in a reversed WDBC program16 CPU batch. One example is `workflows/wdbc-program16-cpu-1.json`, direct variant 1, output position 0 corresponding to normal position 125: 31.3125 versus 31.328125. The full-Float32 maximum occurs in the wine CPU controls. Their reversed batches differ at four positions and duplicate-selected batches at six positions, while every comparison remains within the unchanged bound.

These observations establish the size and scope of batch-order dependence in the saved results. They do not establish its cause. Neither the read-only audit nor the control experiment isolates arithmetic rounding, parameter quantization, native kernel choice, or other artifact-specific effects. The revised README correctly limits its claim to the tested artifacts and precision and does not assert that reduced precision explains every discrepancy.

## Portability and remaining scope

The standalone verifier resolves its own directory and uses retained payloads, so it does not need the original absolute paths or compiled binaries. Reexecuting inference is a different operation and requires the exact source, recorded environment, worker, and restored path mappings. The README says so. The relative link to the preceding study depends on publication into the intended sibling study directory; it does not resolve within this isolated staging folder.

The packaged decision log is a qualification snapshot. Later source-integration decisions appended to the live log are outside this package's scope. The README and copied audit preserve both earlier cautions. A later end-of-run audit is still required for the remaining work and any publication claims added after this review.

## Attention

reviewed by gpt-6-astra

- Low severity: correct the stale original-digest wording described above. The transformed payloads and their provenance are valid; the sentence overstates what an offline reader can verify about unavailable original redacted bytes.
- Retain the earlier persistent-cancellation and batch-order cautions. They are now stated in the README and append-only qualification log.
- No blocking findings in the revised evidence package.
