# Source-informed integration decisions

## CSV

Pandas uses flat token arrays and row boundaries. Kiraa uses a flat field grid. SwiftSci needs ragged row boundaries to preserve its existing file-reader behavior, so the selected representation combines a flat field array with row starts. The public nested-array parser remains a wrapper over the same scanner. Both file and chunked-output readers consume the flat representation inside the mapped-byte lifetime.

CPU samples showed String null matching dominated conversion. The selected matcher compares normalized ASCII bytes and keeps the existing String path for escaped fields, non-ASCII data and non-ASCII configured tokens. That fallback matters because Swift String equality recognizes canonical Unicode equivalents. Tests include Kelvin-sign equivalence, composed/decomposed accents and malformed UTF-8.

This remains whole-file indexing. Pandas chunk conversion and Kiraa guarded parallel scanning suggest later work, but neither is needed for the accepted allocation and conversion improvements. The separate compact design can reduce retained buffers across whole queries.

## Grouping

Pandas checks products of factorized cardinalities and compresses before overflow. Kiraa uses mixed-radix IDs, but its unchecked products and raw-byte Unicode hashing are unsuitable to copy into SwiftSci unchanged.

The selected grouping path reuses SwiftSci's integer domain lookup for the first component and adds checked prefix refinement. Tables must fit both the input row count and a 512 KiB byte limit. A null gets a separate slot. Sparse or extreme domains keep typed dictionary lookup. Group IDs still follow first appearance, and numeric reductions retain their existing order and compensation.

The broader Release tests caught a trap in the missing-column fallback after the refactor. Restoring reserved capacity did not fix it. Direct construction of the known single group did. The existing regression now passes in both modes. No compiler root cause has been established.

## Sorting

Kiraa's DataFrame sort uses indirect Swift comparison sorting over compact values. Its Accelerate value-sort function is not on the measured path. Installed NumPy uses indirect Timsort for the Float64 pandas workload.

Pure radix won on disordered data and lost on ordered data. The selected Double path retains comparison sorting below 1,024 valid values, below five percent valid density, and when monotone runs average at least 64 values, with a minimum allowance of eight runs. These are measured dispatch choices for this Apple Silicon implementation, not universal algorithmic optima.

The first adaptive prototype copied the entire input into tuples before selecting radix. It preserved correctness but lost on the 100,000-row production fixture. The revised detector stops and discards partial preparation as soon as the run limit is exceeded, then scans the original input directly into radix keys. The early decision equals the eventual decision because the run count can only increase.

Normalized keys preserve signed-zero tie order, infinities and subnormals. Stable scatter returns original row positions, and missing rows append in original order. NaNs found before or after the switch retain the old comparison fallback. That preserves compatibility; it does not define a new mathematical total order for NaNs. Other numeric types keep their existing exact sorting paths.

The 99%-missing case used about 7 MiB more process memory for a roughly three-percent speed gain. The conservative five-percent density gate retains comparison sorting there; the measured 90%-missing case retains radix and its substantial speed benefit. The gate is a policy between measured cases, not a proven optimal crossover.

Radix scratch can increase memory for some distributions even when it reduces runtime. Report complete-operation RSS, not a blanket memory-saving claim. Reusable compact buffers and selections remain a separate architecture experiment.

## Evidence and remaining scope

[CSV source notes](csv-grounding.md), [grouping source notes](group-grounding.md), [sorting source notes](sort-grounding.md), [competing design](candidate-b.md), and [design review](design-review.md) retain source links and research papers.

The benchmark adapter was corrected after reading Kiraa's actual composite output code. Kiraa preserves key columns; its ordinal index labels do not replace them. The corrected adapter compares actual keys and values. Historical raw measurements remain unchanged, with a correction in their report.

Inherited CSV EOF handling, integer-parser overflow and sampled inference limitations are recorded in the CSV grounding note. This performance change does not alter those policies. No upstream PR or push is part of this work.
