# Initial stable radix experiment

Pure radix is faster on random and duplicate-heavy input, but slower on sorted and reversed input. It is not accepted as a universal replacement. All 224 verification cases and six NaN rejection cases passed.

Times below are full two-column DataFrame operations, descending order, median of 15 measured repetitions. Peak RSS is the median whole-process high water mark before reference validation.

| Rows | Distribution | Comparison ms | Radix ms | Comparison MiB | Radix MiB |
|---:|---|---:|---:|---:|---:|
|1000|random|0.047|0.019|6.5|6.5|
|1000|sorted|0.009|0.013|6.5|6.5|
|1000|reverse|0.009|0.013|6.5|6.5|
|1000|duplicates|0.047|0.037|6.5|6.5|
|1000|nulls|0.028|0.024|6.6|6.5|
|10000|random|0.683|0.199|7.2|7.2|
|10000|sorted|0.069|0.149|7.2|7.2|
|10000|reverse|0.066|0.150|7.2|7.2|
|10000|duplicates|0.438|0.338|7.2|7.2|
|10000|nulls|0.440|0.206|7.3|7.3|
|100000|random|9.407|2.314|19.5|18.7|
|100000|sorted|0.666|1.436|14.1|14.1|
|100000|reverse|0.637|1.579|18.8|14.1|
|100000|duplicates|5.390|3.545|19.5|18.7|
|100000|nulls|5.778|2.186|21.9|20.0|
|1000000|random|125.484|31.887|82.9|90.5|
|1000000|sorted|7.267|16.311|82.9|90.5|
|1000000|reverse|6.528|15.731|82.9|90.5|
|1000000|duplicates|63.380|33.047|82.9|90.5|
|1000000|nulls|69.862|24.586|103.3|96.6|

Raw kernel timings, both directions and eight-column measurements remain in samples.jsonl. The source tree was at the first CSV/group optimization slice; no adaptive sorter had been installed.
