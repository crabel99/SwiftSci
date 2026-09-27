# Supervised source review

Use the WDBC files in `vendorable/` for classification and preprocessing. Use the existing wine-quality-red fixture for regression. Keep the diabetes downloads outside the repository until an original-data redistribution grant is established.

## WDBC source

The [official UCI record](https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic) identifies dataset 17, DOI [10.24432/C5DW2B](https://doi.org/10.24432/C5DW2B), and explicitly grants CC BY 4.0. Its original source files declare November 1995. UCI does not offer a release revision for these files, so `provenance.json` pins the downloaded bytes by SHA-256. `vendorable/ATTRIBUTION.md` supplies the creator credit, source link, license link, and modifications notice. Original source documentation and diagnoses are preserved.

The 569 records contain 357 benign and 212 malignant diagnoses, 30 numeric predictors, and an ID. All source IDs are unique. All numeric features are finite. All complete predictor rows are distinct. Every numeric feature row matches scikit-learn 1.7.2 in the same row order. Original diagnoses map to scikit-learn target 0 for malignant and 1 for benign. The suite should declare its own mapping as malignant 1 and benign 0, then test this mapping directly.

`wdbc-schema-v1.json` maps each one-based original column. Columns 3 through 12 hold means, 13 through 22 hold standard errors, and 23 through 32 hold worst measurements in the same feature order. Worst means the average of the three largest values. UCI does not supply physical units in its metadata. Preserve raw published values and describe their measurement rather than inventing units such as millimeters. Source IDs and diagnoses must never enter the predictor matrix.

The bytes to vendor are:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| wdbc.data | 124103 | d606af411f3e5be8a317a5a8b652b425aaf0ff38ca683d5327ffff94c3695f4a |
| wdbc.names | 4708 | 840e04e3f20f8a5b326892f3b9cbc01c4cd6f7e6c597630b701ef6c0ac79f5ef |

The [CC BY 4.0 deed](https://creativecommons.org/licenses/by/4.0/) permits redistribution and adaptation with attribution, a license link, and an indication of changes. A direct download of the plain-text legal code returned HTTP 403. The attribution file links to the legal code instead.

## Split contract

The parent task selected a versioned SHA-256 partition of canonical predictor content into 60/20/20 training, validation, and test buckets. Identical predictor rows must share a partition even when their targets differ. Neither labels nor target values affect the hash. Freeze the exact canonical numeric serialization, domain separator, hash-to-bucket rule, and source-ID lists in the suite manifest. Preserve source IDs and source line numbers for traceability. This source bundle deliberately contains no competing split definition.

Fit imputation, scaling, feature selection, and other learned preprocessing only on training data. Select parameters on validation data and leave test data for final scoring. A label-only split stratifier would be defensible if declared, but the chosen contract uses no labels at all.

## Diabetes research findings

The [scikit-learn API](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_diabetes.html) says `scaled=False` returns raw feature variables. The default centers and scales across all samples, which would leak holdout information if used before partitioning. The source was pinned to release 1.7.2, Git commit `25dee604bae18205b01548348388baf7a1cdfe0e`. `downloads.json` records immutable URLs and hashes for the source data, target data, package license, loader, and description.

The [original data host](https://www4.stat.ncsu.edu/~boos/var.select/diabetes.html) attributes the data to Efron, Hastie, Johnstone, and Tibshirani, Least Angle Regression, 2004. There are 442 rows, ten predictors, and the original one-year disease-progression response. The original target has no stated measurement unit. Retain sex codes 1 and 2 without inventing their meanings. The original serum column S5 already appears transformed. The scikit-learn description calls its interpretation uncertain.

The downloaded scikit-learn raw file and original tab-delimited file have the same 442 records and targets. Eleven S5 values differ by floating-point representation at roughly 1e-15, so they are not strictly bitwise or numerically identical. `provenance.json` records each difference. No rows or targets were synthesized.

The scikit-learn repository has a BSD-3-Clause package notice. Neither its dataset description nor the original data host gives an explicit separate redistribution license for the original diabetes dataset. This review does not treat the package license as a grant from the data creators. Diabetes stays research-only.

The requested local `Benchmarks/.venv-standardized` environment contains no importable scikit-learn installation or bundled scikit-learn dataset files. No environment changes were made.

## Existing regression alternative

The [official wine-quality record](https://archive.ics.uci.edu/dataset/186/wine+quality) explicitly grants CC BY 4.0 and permits classification or regression using the original quality score. The existing `Benchmarks/Specs/datasets/wine-quality-red.json` pins 1599 records, original source SHA-256 `4a402cf041b025d4566d954c3b9ba8635a3a8a01e039005d97d6a710278cf05e`, and normalized fixture SHA-256 `f54f1488ea72487f6604930ccb5c1d1b5e75e2aa540ffe720c1d1a4de26abc94`. Retain Cortez, Cerdeira, Almeida, Matos, and Reis, 2009, DOI `10.24432/C56S3T`, as its attribution. Group identical predictor rows before partitioning to keep duplicates out of different partitions.

All work in this review is confined to the temporary source directory. No repository files, production code, or Git state were changed.
