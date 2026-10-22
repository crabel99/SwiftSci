# Compiler-boundary screening

These 72 source-path observations compare the same native output under three identical launcher names for both executables. See the [study methods](README.md).

| Scope | Case | Policy | Implementation | CPU ms | Elapsed ms | Peak RSS MiB |
|---|---|---|---|---:|---:|---:|
| stream | energy | parallel | parent-short | 273.363 | 117.327 | 139.19 |
| stream | energy | parallel | parent-production-name | 272.791 | 117.124 | 139.12 |
| stream | energy | parallel | parent-screen-name | 275.246 | 117.430 | 139.10 |
| stream | energy | parallel | candidate-short | 258.925 | 111.568 | 139.30 |
| stream | energy | parallel | candidate-production-name | 259.288 | 112.578 | 139.34 |
| stream | energy | parallel | candidate-screen-name | 259.126 | 112.706 | 139.12 |
