# Narrowed String/Bool specialization

October 19, 2026. The original candidate regressed both Date cases despite winning on String/Bool. Remove only the explicit Date specialization and retain the generic fallback. Compare this local candidate against the same d23bf7 baseline with identical typed checking and measured boundaries.

Repeat all twelve original cases and add two Date shapes, 131071 rows by three columns in descending order and 512003 rows by eight columns with missing keys. Five timing pairs and three separate memory pairs per case. No thresholds or input-specific algorithm decisions change. The Date regression must disappear without sacrificing the mixed-column CPU savings or adding live output storage. Retain all original results separately.
