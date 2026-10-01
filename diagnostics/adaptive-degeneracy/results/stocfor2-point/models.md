# Paired whole-model validation

Base: `a7f1fac`. Production SHA-256: `90207a20d1dfa07cf548706f456191f31401f4dd98907342db138a2a9149e8a0`.

All 30 configurations reach verified original optima, versus 29 optima and one
numerical error on the base. Only JuMP stocfor2 changes. The other 29 cases retain
status, iterations, refactorizations, phase sequence and objective exactly.
Timings include diagnostic work and compilation; this is not a speed benchmark.

| Model | Reader | Algorithm | Manager | Seed | Before | After | Changed fields |
| --- | --- | --- | --- | --- | --- | --- | --- |
| miplib/mod010 | permuted | primal | pfi | 1 | OPTIMAL / 598 | OPTIMAL / 598 | unchanged |
| miplib/mod010 | permuted | primal | forrest_tomlin | 1 | OPTIMAL / 590 | OPTIMAL / 590 | unchanged |
| miplib/mod010 | permuted | primal | suhl_suhl | 1 | OPTIMAL / 576 | OPTIMAL / 576 | unchanged |
| miplib/mod010 | permuted | primal | bartels_golub | 1 | OPTIMAL / 615 | OPTIMAL / 615 | unchanged |
| miplib/mod010 | permuted | primal | pfi | 17 | OPTIMAL / 679 | OPTIMAL / 679 | unchanged |
| miplib/mod010 | permuted | primal | pfi | 2 | OPTIMAL / 619 | OPTIMAL / 619 | unchanged |
| miplib/mod010 | permuted | primal | pfi | 29 | OPTIMAL / 586 | OPTIMAL / 586 | unchanged |
| miplib/mod010 | native | primal | pfi | 20261001 | OPTIMAL / 532 | OPTIMAL / 532 | unchanged |
| miplib/mod010 | jump | primal | pfi | 20261001 | OPTIMAL / 595 | OPTIMAL / 595 | unchanged |
| netlib/degen2 | native | primal | pfi | 20261001 | OPTIMAL / 1034 | OPTIMAL / 1034 | unchanged |
| netlib/degen2 | jump | primal | pfi | 20261001 | OPTIMAL / 1031 | OPTIMAL / 1031 | unchanged |
| netlib/boeing1 | native | primal | pfi | 20261001 | OPTIMAL / 558 | OPTIMAL / 558 | unchanged |
| netlib/boeing1 | jump | primal | pfi | 20261001 | OPTIMAL / 559 | OPTIMAL / 559 | unchanged |
| miplib/p0201 | native | primal | pfi | 20261001 | OPTIMAL / 244 | OPTIMAL / 244 | unchanged |
| miplib/p0201 | jump | primal | pfi | 20261001 | OPTIMAL / 244 | OPTIMAL / 244 | unchanged |
| miplib/misc07 | native | primal | pfi | 20261001 | OPTIMAL / 263 | OPTIMAL / 263 | unchanged |
| miplib/misc07 | jump | primal | pfi | 20261001 | OPTIMAL / 284 | OPTIMAL / 284 | unchanged |
| netlib/scsd6 | native | primal | pfi | 20261001 | OPTIMAL / 340 | OPTIMAL / 340 | unchanged |
| netlib/scsd6 | native | primal | forrest_tomlin | 20261001 | OPTIMAL / 326 | OPTIMAL / 326 | unchanged |
| netlib/scsd6 | native | primal | suhl_suhl | 20261001 | OPTIMAL / 329 | OPTIMAL / 329 | unchanged |
| netlib/scsd6 | native | primal | bartels_golub | 20261001 | OPTIMAL / 337 | OPTIMAL / 337 | unchanged |
| netlib/scsd6 | jump | primal | pfi | 20261001 | OPTIMAL / 340 | OPTIMAL / 340 | unchanged |
| netlib/cycle | native | primal | pfi | 20261001 | OPTIMAL / 963 | OPTIMAL / 963 | unchanged |
| netlib/cycle | jump | primal | pfi | 20261001 | OPTIMAL / 1291 | OPTIMAL / 1291 | unchanged |
| netlib/stocfor2 | native | primal | pfi | 20261001 | OPTIMAL / 1970 | OPTIMAL / 1970 | unchanged |
| netlib/stocfor2 | jump | primal | pfi | 20261001 | NUMERICAL_ERROR / 1957 | OPTIMAL / 2322 | status, iterations, refactorizations, objective |
| miplib/mod010 | native | dual | pfi | 20261001 | OPTIMAL / 679 | OPTIMAL / 679 | unchanged |
| miplib/mod010 | jump | dual | pfi | 20261001 | OPTIMAL / 712 | OPTIMAL / 712 | unchanged |
| netlib/degen3 | native | primal | pfi | 20261001 | OPTIMAL / 3613 | OPTIMAL / 3613 | unchanged |
| netlib/degen3 | jump | primal | pfi | 20261001 | OPTIMAL / 4089 | OPTIMAL / 4089 | unchanged |
