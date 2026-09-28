# Compact storage and model-batch integration

Keep compact storage as the integration direction. The prototype shows a substantial reduction in retained data and process memory. Adapting the model input layout also recovers throughput: the compact column-major path matches or beats the fused path over existing storage in the tested workloads.

This is an external experiment. No production SwiftSci storage API was changed. The repository remains at cd7409227b. The preserved source, executable, fixture hashes, toolchain metadata, raw samples and correctness checks are in this result directory.

## What was measured

Eight numeric features loaded from identical warm-cache binary Double fixtures, a filter on the first feature, fixed normalization parameters, zero imputation for missing normalized features, Float32 batch construction, and a linear prediction through Accelerate CBLAS. The model weights are fixed. This is native CPU inference, not Qwen, MLX, GPU or Neural Engine inference. The experiment does not measure CSV parsing or model quality.

The current path uses SwiftSci DataFrame filtering. The fused paths avoid materializing a filtered DataFrame. Compact paths use contiguous Double values and one validity bit per value, omitting the bitmap for all-valid columns. The successful adapter writes a column-major Float32 batch that Accelerate consumes directly. It still allocates that batch; it is not zero-copy.

Each repeated pipeline measurement has two warmups followed by seven samples in each of three processes, for 21 samples. Mode order rotates between batches. Loading is timed separately once per process. Accelerate thread limits are set to one; SwiftSci may still perform its existing parallel column gather. Absolute times vary with other work on this Mac.

## Memory and throughput together

Rows below use one missing value every 101 rows per feature, with feature-specific offsets. Memory units are decimal MB. Column payload counts exclude allocator overhead. Peak RSS includes input mapping, allocations, retained buffers and allocator caches, so it is a process measure rather than column size.

| Rows | Path | Column payload MB | Peak RSS MB | Live heap MB after pipeline | Load and construct ms | Repeated pipeline ms |
|---:|---|---:|---:|---:|---:|---:|
| 1,000,000 | Current DataFrame | 128.0 | 222.7 | 209.2 | 178.54 | 9.46 |
| 1,000,000 | Existing storage, fused | 128.0 | 198.8 | 150.0 | 175.32 | 8.39 |
| 1,000,000 | Compact, row-major batch | 65.0 | 135.6 | 87.0 | 22.73 | 9.83 |
| 1,000,000 | Compact, column-major batch | 65.0 | 135.6 | 87.0 | 22.97 | 8.43 |
| 4,000,000 | Current DataFrame | 512.0 | 859.8 | 836.5 | 696.21 | 37.00 |
| 4,000,000 | Existing storage, fused | 512.0 | 774.8 | 599.4 | 694.40 | 34.70 |
| 4,000,000 | Compact, row-major batch | 260.0 | 522.6 | 347.4 | 91.78 | 39.57 |
| 4,000,000 | Compact, column-major batch | 260.0 | 522.6 | 347.4 | 90.45 | 31.29 |

Heap snapshots report live allocations, not the number of allocation calls. The full source uses the same masks and values in every mode. Input construction differs because optional elements must be constructed while packed Double values can be bulk-copied. These loading figures cannot be attributed solely to fewer bytes or generalized to other readers.

An additional loader control compared indexed optional construction with the original map-based construction. At one million rows, the original optional loader took about 173 ms, indexed optional loading took 163 ms, and compact loading took 23 ms. At four million rows the corresponding figures were 676, 659 and 91 ms. That check retained the construction advantage, but it remains specific to this native binary ingestion path. Its independent snapshots are in the earlier 20260926T015624Z/loader-control directory.

## All repeated-pipeline results

| Rows | Missing pattern | Path | Select ms | Normalize and pack ms | Inference ms | Total ms |
|---:|---|---|---:|---:|---:|---:|
| 100,000 | none | Current DataFrame | 0.310 | 0.589 | 0.093 | 1.000 |
| 100,000 | none | Existing storage, fused | 0.208 | 0.567 | 0.091 | 0.882 |
| 100,000 | none | Compact, row-major batch | 0.179 | 0.713 | 0.092 | 0.993 |
| 100,000 | none | Compact, extra vDSP passes | 0.179 | 0.959 | 0.095 | 1.234 |
| 100,000 | none | Existing, row traversal | 0.207 | 0.745 | 0.091 | 1.044 |
| 100,000 | none | Compact, row traversal | 0.171 | 0.904 | 0.091 | 1.147 |
| 100,000 | none | Existing, tiled | 0.207 | 0.584 | 0.092 | 0.880 |
| 100,000 | none | Compact, tiled | 0.174 | 0.663 | 0.089 | 0.933 |
| 100,000 | none | Compact, column-major batch | 0.178 | 0.633 | 0.006 | 0.816 |
| 100,000 | every 101 rows | Current DataFrame | 0.289 | 0.559 | 0.092 | 0.982 |
| 100,000 | every 101 rows | Existing storage, fused | 0.182 | 0.577 | 0.090 | 0.849 |
| 100,000 | every 101 rows | Compact, row-major batch | 0.111 | 0.769 | 0.090 | 0.969 |
| 100,000 | every 101 rows | Compact, extra vDSP passes | 0.110 | 0.985 | 0.092 | 1.188 |
| 100,000 | every 101 rows | Existing, row traversal | 0.182 | 0.740 | 0.089 | 1.009 |
| 100,000 | every 101 rows | Compact, row traversal | 0.110 | 1.037 | 0.090 | 1.238 |
| 100,000 | every 101 rows | Existing, tiled | 0.183 | 0.599 | 0.089 | 0.871 |
| 100,000 | every 101 rows | Compact, tiled | 0.112 | 0.764 | 0.088 | 0.966 |
| 100,000 | every 101 rows | Compact, column-major batch | 0.114 | 0.648 | 0.006 | 0.767 |
| 100,000 | every 2 rows | Current DataFrame | 0.143 | 0.168 | 0.047 | 0.374 |
| 100,000 | every 2 rows | Existing storage, fused | 0.050 | 0.204 | 0.046 | 0.301 |
| 100,000 | every 2 rows | Compact, row-major batch | 0.077 | 0.239 | 0.045 | 0.361 |
| 100,000 | every 2 rows | Compact, extra vDSP passes | 0.075 | 0.527 | 0.045 | 0.647 |
| 100,000 | every 2 rows | Existing, row traversal | 0.050 | 0.264 | 0.046 | 0.360 |
| 100,000 | every 2 rows | Compact, row traversal | 0.074 | 0.327 | 0.046 | 0.447 |
| 100,000 | every 2 rows | Existing, tiled | 0.050 | 0.213 | 0.045 | 0.309 |
| 100,000 | every 2 rows | Compact, tiled | 0.074 | 0.255 | 0.046 | 0.376 |
| 100,000 | every 2 rows | Compact, column-major batch | 0.079 | 0.215 | 0.003 | 0.301 |
| 1,000,000 | none | Current DataFrame | 3.210 | 5.496 | 0.848 | 9.600 |
| 1,000,000 | none | Existing storage, fused | 2.037 | 5.509 | 0.866 | 8.406 |
| 1,000,000 | none | Compact, row-major batch | 1.826 | 6.786 | 0.852 | 9.466 |
| 1,000,000 | none | Compact, extra vDSP passes | 1.836 | 9.441 | 0.859 | 12.154 |
| 1,000,000 | none | Existing, row traversal | 2.048 | 7.296 | 0.907 | 10.250 |
| 1,000,000 | none | Compact, row traversal | 1.854 | 8.542 | 0.896 | 11.282 |
| 1,000,000 | none | Existing, tiled | 2.058 | 6.166 | 0.908 | 9.123 |
| 1,000,000 | none | Compact, tiled | 1.831 | 6.612 | 0.894 | 9.320 |
| 1,000,000 | none | Compact, column-major batch | 1.853 | 6.226 | 0.119 | 8.191 |
| 1,000,000 | every 101 rows | Current DataFrame | 2.956 | 5.476 | 0.838 | 9.461 |
| 1,000,000 | every 101 rows | Existing storage, fused | 1.806 | 5.721 | 0.846 | 8.386 |
| 1,000,000 | every 101 rows | Compact, row-major batch | 1.104 | 7.873 | 0.841 | 9.828 |
| 1,000,000 | every 101 rows | Compact, extra vDSP passes | 1.109 | 9.821 | 0.843 | 11.764 |
| 1,000,000 | every 101 rows | Existing, row traversal | 1.813 | 7.181 | 0.890 | 9.876 |
| 1,000,000 | every 101 rows | Compact, row traversal | 1.114 | 14.307 | 0.893 | 16.337 |
| 1,000,000 | every 101 rows | Existing, tiled | 1.806 | 5.843 | 0.881 | 8.517 |
| 1,000,000 | every 101 rows | Compact, tiled | 1.110 | 8.298 | 0.885 | 10.295 |
| 1,000,000 | every 101 rows | Compact, column-major batch | 1.114 | 7.155 | 0.118 | 8.427 |
| 1,000,000 | every 2 rows | Current DataFrame | 1.509 | 1.653 | 0.425 | 3.665 |
| 1,000,000 | every 2 rows | Existing storage, fused | 0.535 | 2.273 | 0.453 | 3.288 |
| 1,000,000 | every 2 rows | Compact, row-major batch | 0.791 | 2.462 | 0.425 | 3.649 |
| 1,000,000 | every 2 rows | Compact, extra vDSP passes | 0.754 | 5.508 | 0.424 | 6.700 |
| 1,000,000 | every 2 rows | Existing, row traversal | 0.510 | 2.635 | 0.440 | 3.582 |
| 1,000,000 | every 2 rows | Compact, row traversal | 0.822 | 4.524 | 0.431 | 5.777 |
| 1,000,000 | every 2 rows | Existing, tiled | 0.514 | 2.346 | 0.438 | 3.291 |
| 1,000,000 | every 2 rows | Compact, tiled | 0.745 | 2.803 | 0.427 | 3.976 |
| 1,000,000 | every 2 rows | Compact, column-major batch | 0.748 | 2.155 | 0.044 | 2.945 |
| 4,000,000 | none | Current DataFrame | 12.860 | 20.904 | 3.636 | 37.554 |
| 4,000,000 | none | Existing storage, fused | 8.206 | 22.295 | 3.685 | 34.253 |
| 4,000,000 | none | Compact, row-major batch | 7.320 | 27.215 | 3.630 | 38.192 |
| 4,000,000 | none | Compact, extra vDSP passes | 7.380 | 37.571 | 3.625 | 48.662 |
| 4,000,000 | none | Existing, row traversal | 8.134 | 29.007 | 3.627 | 40.831 |
| 4,000,000 | none | Compact, row traversal | 7.309 | 34.576 | 3.627 | 45.508 |
| 4,000,000 | none | Existing, tiled | 8.173 | 23.902 | 3.623 | 36.090 |
| 4,000,000 | none | Compact, tiled | 7.336 | 26.242 | 3.629 | 37.134 |
| 4,000,000 | none | Compact, column-major batch | 7.366 | 25.060 | 0.534 | 32.971 |
| 4,000,000 | every 101 rows | Current DataFrame | 12.018 | 21.297 | 3.583 | 37.002 |
| 4,000,000 | every 101 rows | Existing storage, fused | 7.283 | 23.763 | 3.666 | 34.696 |
| 4,000,000 | every 101 rows | Compact, row-major batch | 4.540 | 31.243 | 3.653 | 39.571 |
| 4,000,000 | every 101 rows | Compact, extra vDSP passes | 4.836 | 39.756 | 3.660 | 48.331 |
| 4,000,000 | every 101 rows | Existing, row traversal | 7.247 | 28.955 | 3.581 | 39.809 |
| 4,000,000 | every 101 rows | Compact, row traversal | 4.757 | 56.301 | 3.612 | 64.840 |
| 4,000,000 | every 101 rows | Existing, tiled | 7.240 | 25.261 | 3.591 | 36.043 |
| 4,000,000 | every 101 rows | Compact, tiled | 4.744 | 33.259 | 3.612 | 41.779 |
| 4,000,000 | every 101 rows | Compact, column-major batch | 4.531 | 26.113 | 0.550 | 31.294 |

Per-stage medians need not add to the median total. Extra vector passes, full row traversal and tiling were not general improvements. A column-major consumer adapter was the useful integration change. This demonstrates why memory layout and the consuming operation must be designed together.

## Correctness

All 252 edge runs passed across nine paths, including empty inputs, all missing values, 63/64/65-row bitmap boundaries and partial final words. All larger workloads checked every selected feature and every prediction against a scalar reference. Feature batches matched exactly and the largest observed prediction error was zero for this fixture.

The fixture deliberately uses exactly representable binary fractions so traversal order does not hide correctness failures. It does not establish identical rounding for arbitrary floating inputs, nor full production support for NaN, infinity, variable-width data, mutation or shared-buffer ownership. No full package test rerun was needed because production source did not change.

## Integration decisions

1. Preserve compact numeric buffers and validity bitmaps as the intended storage direction. Evaluate memory capacity and peak process memory alongside latency. More free unified memory can support larger datasets, model working sets or context caches; no increase in actual LLM context capacity was measured here.
2. Add a batch adapter that accepts the consumer's dtype and strides. The prototype validates a column-major Accelerate adapter. MLX needs its own adapter and measurements; do not assume an ordinary Swift array can be shared without copying.
3. Keep filters as selection indices through normalization and batch conversion when a full filtered table is unnecessary. Use bounded batches for workloads that value peak memory over maximum single-batch throughput.
4. Make optional-array materialization explicit at compatibility boundaries. Repeatedly reconstructing `[Double?]` from compact columns would lose the memory benefit. The current public `TypedColumn.values` property is the main compatibility decision before integration.
5. Use immutable buffer ownership for slices and views, and carry the validity bitmap and offset with every view. Evaluate Arrow interoperation once ownership and lifetime checks are implemented.
6. Keep Double storage and exact integer policies for engineering calculations. Float32 or lower precision should be chosen at the model boundary, with separate accuracy tests.

The next production step should be a tested compact numeric buffer and a consumer-aware batch adapter, with compatibility decisions documented before replacing TypedColumn storage.

## Reproduce

Run `../run.sh` from this result directory, or `/Users/LOCAL_USER/local-ai/spl/swiftsci/filter-profiling/compact-pipeline/run.sh` from anywhere. The script builds the experiment and writes a new timestamped result directory. It leaves production repositories unchanged.
