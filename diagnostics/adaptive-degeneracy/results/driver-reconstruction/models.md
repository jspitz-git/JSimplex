# Paired whole-model validation

Base: `8d9b83e`. Production source SHA-256: `6f5d7c7d0d1e721a29464509a65681eecffcec681e81ae9a1850c0fd9ad9ebf7`.

29 verified optima and one numerical error, versus 28 and two before.
Only native cycle changed; the other 29 configurations retain status, iterations,
refactorizations, phase sequence and objective exactly.
All optimal results pass original unscaled primal feasibility and independent
HiGHS objective comparison. Timings include diagnostic work and compilation;
this is not a speed benchmark.

| Model | Reader | Algorithm | Manager | Seed | Before status / iterations | After status / iterations | Verified | Changed fields |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| miplib/mod010 | permuted | primal | pfi | 1 | OPTIMAL / 598 | OPTIMAL / 598 | True | unchanged |
| miplib/mod010 | permuted | primal | forrest_tomlin | 1 | OPTIMAL / 590 | OPTIMAL / 590 | True | unchanged |
| miplib/mod010 | permuted | primal | suhl_suhl | 1 | OPTIMAL / 576 | OPTIMAL / 576 | True | unchanged |
| miplib/mod010 | permuted | primal | bartels_golub | 1 | OPTIMAL / 615 | OPTIMAL / 615 | True | unchanged |
| miplib/mod010 | permuted | primal | pfi | 17 | OPTIMAL / 679 | OPTIMAL / 679 | True | unchanged |
| miplib/mod010 | permuted | primal | pfi | 2 | OPTIMAL / 619 | OPTIMAL / 619 | True | unchanged |
| miplib/mod010 | permuted | primal | pfi | 29 | OPTIMAL / 586 | OPTIMAL / 586 | True | unchanged |
| miplib/mod010 | native | primal | pfi | 20261001 | OPTIMAL / 532 | OPTIMAL / 532 | True | unchanged |
| miplib/mod010 | jump | primal | pfi | 20261001 | OPTIMAL / 595 | OPTIMAL / 595 | True | unchanged |
| netlib/degen2 | native | primal | pfi | 20261001 | OPTIMAL / 1034 | OPTIMAL / 1034 | True | unchanged |
| netlib/degen2 | jump | primal | pfi | 20261001 | OPTIMAL / 1031 | OPTIMAL / 1031 | True | unchanged |
| netlib/boeing1 | native | primal | pfi | 20261001 | OPTIMAL / 558 | OPTIMAL / 558 | True | unchanged |
| netlib/boeing1 | jump | primal | pfi | 20261001 | OPTIMAL / 559 | OPTIMAL / 559 | True | unchanged |
| miplib/p0201 | native | primal | pfi | 20261001 | OPTIMAL / 244 | OPTIMAL / 244 | True | unchanged |
| miplib/p0201 | jump | primal | pfi | 20261001 | OPTIMAL / 244 | OPTIMAL / 244 | True | unchanged |
| miplib/misc07 | native | primal | pfi | 20261001 | OPTIMAL / 263 | OPTIMAL / 263 | True | unchanged |
| miplib/misc07 | jump | primal | pfi | 20261001 | OPTIMAL / 284 | OPTIMAL / 284 | True | unchanged |
| netlib/scsd6 | native | primal | pfi | 20261001 | OPTIMAL / 340 | OPTIMAL / 340 | True | unchanged |
| netlib/scsd6 | native | primal | forrest_tomlin | 20261001 | OPTIMAL / 326 | OPTIMAL / 326 | True | unchanged |
| netlib/scsd6 | native | primal | suhl_suhl | 20261001 | OPTIMAL / 329 | OPTIMAL / 329 | True | unchanged |
| netlib/scsd6 | native | primal | bartels_golub | 20261001 | OPTIMAL / 337 | OPTIMAL / 337 | True | unchanged |
| netlib/scsd6 | jump | primal | pfi | 20261001 | OPTIMAL / 340 | OPTIMAL / 340 | True | unchanged |
| netlib/cycle | native | primal | pfi | 20261001 | NUMERICAL_ERROR / 868 | OPTIMAL / 963 | True | status, iterations, refactorizations, phases, objective |
| netlib/cycle | jump | primal | pfi | 20261001 | OPTIMAL / 1291 | OPTIMAL / 1291 | True | unchanged |
| netlib/stocfor2 | native | primal | pfi | 20261001 | OPTIMAL / 1970 | OPTIMAL / 1970 | True | unchanged |
| netlib/stocfor2 | jump | primal | pfi | 20261001 | NUMERICAL_ERROR / 1957 | NUMERICAL_ERROR / 1957 | False | unchanged |
| miplib/mod010 | native | dual | pfi | 20261001 | OPTIMAL / 679 | OPTIMAL / 679 | True | unchanged |
| miplib/mod010 | jump | dual | pfi | 20261001 | OPTIMAL / 712 | OPTIMAL / 712 | True | unchanged |
| netlib/degen3 | native | primal | pfi | 20261001 | OPTIMAL / 3613 | OPTIMAL / 3613 | True | unchanged |
| netlib/degen3 | jump | primal | pfi | 20261001 | OPTIMAL / 4089 | OPTIMAL / 4089 | True | unchanged |
