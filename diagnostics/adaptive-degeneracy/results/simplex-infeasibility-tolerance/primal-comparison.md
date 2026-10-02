# Paired primal corpus results

Status, iteration count, refactorizations, phase sequence and objective are compared exactly.
An optimum is verified only if both primal certificates and the independent objective match pass.
Times include compilation and diagnostics; this is not a speed benchmark.

| Model | Reader | Manager | Seed | Before | After | Verified before / after | Changed fields |
| --- | --- | --- | --- | --- | --- | --- | --- |
| miplib/mod010 | permuted | pfi | 1 | OPTIMAL / 598 | OPTIMAL / 598 | True / True | unchanged |
| miplib/mod010 | permuted | forrest_tomlin | 1 | OPTIMAL / 590 | OPTIMAL / 590 | True / True | unchanged |
| miplib/mod010 | permuted | suhl_suhl | 1 | OPTIMAL / 576 | OPTIMAL / 576 | True / True | unchanged |
| miplib/mod010 | permuted | bartels_golub | 1 | OPTIMAL / 615 | OPTIMAL / 615 | True / True | unchanged |
| miplib/mod010 | permuted | pfi | 17 | OPTIMAL / 679 | OPTIMAL / 679 | True / True | unchanged |
| miplib/mod010 | permuted | pfi | 2 | OPTIMAL / 619 | OPTIMAL / 619 | True / True | unchanged |
| miplib/mod010 | permuted | pfi | 29 | OPTIMAL / 586 | OPTIMAL / 586 | True / True | unchanged |
| miplib/mod010 | native | pfi | 20261001 | OPTIMAL / 532 | OPTIMAL / 532 | True / True | unchanged |
| miplib/mod010 | jump | pfi | 20261001 | OPTIMAL / 595 | OPTIMAL / 595 | True / True | unchanged |
| netlib/degen2 | native | pfi | 20261001 | OPTIMAL / 1034 | OPTIMAL / 1034 | True / True | unchanged |
| netlib/degen2 | jump | pfi | 20261001 | OPTIMAL / 1031 | OPTIMAL / 1031 | True / True | unchanged |
| netlib/boeing1 | native | pfi | 20261001 | OPTIMAL / 558 | OPTIMAL / 558 | True / True | unchanged |
| netlib/boeing1 | jump | pfi | 20261001 | OPTIMAL / 559 | OPTIMAL / 559 | True / True | unchanged |
| miplib/p0201 | native | pfi | 20261001 | OPTIMAL / 244 | OPTIMAL / 244 | True / True | unchanged |
| miplib/p0201 | jump | pfi | 20261001 | OPTIMAL / 244 | OPTIMAL / 244 | True / True | unchanged |
| miplib/misc07 | native | pfi | 20261001 | OPTIMAL / 263 | OPTIMAL / 263 | True / True | unchanged |
| miplib/misc07 | jump | pfi | 20261001 | OPTIMAL / 284 | OPTIMAL / 284 | True / True | unchanged |
| netlib/scsd6 | native | pfi | 20261001 | OPTIMAL / 340 | OPTIMAL / 340 | True / True | unchanged |
| netlib/scsd6 | native | forrest_tomlin | 20261001 | OPTIMAL / 326 | OPTIMAL / 326 | True / True | unchanged |
| netlib/scsd6 | native | suhl_suhl | 20261001 | OPTIMAL / 329 | OPTIMAL / 329 | True / True | unchanged |
| netlib/scsd6 | native | bartels_golub | 20261001 | OPTIMAL / 337 | OPTIMAL / 337 | True / True | unchanged |
| netlib/scsd6 | jump | pfi | 20261001 | OPTIMAL / 340 | OPTIMAL / 340 | True / True | unchanged |
| netlib/cycle | native | pfi | 20261001 | OPTIMAL / 963 | OPTIMAL / 963 | True / True | unchanged |
| netlib/cycle | jump | pfi | 20261001 | OPTIMAL / 1291 | OPTIMAL / 1291 | True / True | unchanged |
| netlib/stocfor2 | native | pfi | 20261001 | OPTIMAL / 1970 | OPTIMAL / 1970 | True / True | unchanged |
| netlib/stocfor2 | jump | pfi | 20261001 | OPTIMAL / 2322 | OPTIMAL / 2322 | True / True | unchanged |
| netlib/degen3 | native | pfi | 20261001 | OPTIMAL / 3613 | OPTIMAL / 3613 | True / True | unchanged |
| netlib/degen3 | jump | pfi | 20261001 | OPTIMAL / 4089 | OPTIMAL / 4089 | True / True | unchanged |
