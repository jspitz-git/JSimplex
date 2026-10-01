# Paired dual corpus results

Status, iteration count, refactorizations, phase sequence and objective are compared exactly.
An optimum is verified only if both primal certificates and the independent objective match pass.
Times include compilation and diagnostics; this is not a speed benchmark.

| Model | Reader | Manager | Seed | Before | After | Verified before / after | Changed fields |
| --- | --- | --- | --- | --- | --- | --- | --- |
| miplib/mod010 | permuted | pfi | 1 | OPTIMAL / 664 | OPTIMAL / 664 | True / True | unchanged |
| miplib/mod010 | permuted | forrest_tomlin | 1 | OPTIMAL / 726 | OPTIMAL / 726 | True / True | unchanged |
| miplib/mod010 | permuted | suhl_suhl | 1 | OPTIMAL / 687 | OPTIMAL / 687 | True / True | unchanged |
| miplib/mod010 | permuted | bartels_golub | 1 | OPTIMAL / 708 | OPTIMAL / 708 | True / True | unchanged |
| miplib/mod010 | permuted | pfi | 17 | OPTIMAL / 765 | OPTIMAL / 765 | True / True | unchanged |
| miplib/mod010 | permuted | pfi | 2 | OPTIMAL / 668 | OPTIMAL / 668 | True / True | unchanged |
| miplib/mod010 | permuted | pfi | 29 | OPTIMAL / 778 | OPTIMAL / 778 | True / True | unchanged |
| miplib/mod010 | native | pfi | 20261001 | OPTIMAL / 679 | OPTIMAL / 679 | True / True | unchanged |
| miplib/mod010 | jump | pfi | 20261001 | OPTIMAL / 712 | OPTIMAL / 712 | True / True | unchanged |
| netlib/degen2 | native | pfi | 20261001 | OPTIMAL / 534 | OPTIMAL / 534 | True / True | unchanged |
| netlib/degen2 | jump | pfi | 20261001 | OPTIMAL / 548 | OPTIMAL / 548 | True / True | unchanged |
| netlib/boeing1 | native | pfi | 20261001 | OPTIMAL / 377 | OPTIMAL / 377 | True / True | unchanged |
| netlib/boeing1 | jump | pfi | 20261001 | OPTIMAL / 388 | OPTIMAL / 388 | True / True | unchanged |
| miplib/p0201 | native | pfi | 20261001 | OPTIMAL / 85 | OPTIMAL / 85 | True / True | unchanged |
| miplib/p0201 | jump | pfi | 20261001 | OPTIMAL / 85 | OPTIMAL / 85 | True / True | unchanged |
| miplib/misc07 | native | pfi | 20261001 | OPTIMAL / 143 | OPTIMAL / 143 | True / True | unchanged |
| miplib/misc07 | jump | pfi | 20261001 | OPTIMAL / 144 | OPTIMAL / 144 | True / True | unchanged |
| netlib/scsd6 | native | pfi | 20261001 | OPTIMAL / 288 | OPTIMAL / 288 | True / True | unchanged |
| netlib/scsd6 | native | forrest_tomlin | 20261001 | OPTIMAL / 302 | OPTIMAL / 302 | True / True | unchanged |
| netlib/scsd6 | native | suhl_suhl | 20261001 | OPTIMAL / 305 | OPTIMAL / 305 | True / True | unchanged |
| netlib/scsd6 | native | bartels_golub | 20261001 | OPTIMAL / 281 | OPTIMAL / 281 | True / True | unchanged |
| netlib/scsd6 | jump | pfi | 20261001 | OPTIMAL / 288 | OPTIMAL / 288 | True / True | unchanged |
| netlib/cycle | native | pfi | 20261001 | OPTIMAL / 571 | OPTIMAL / 571 | True / True | unchanged |
| netlib/cycle | jump | pfi | 20261001 | OPTIMAL / 634 | OPTIMAL / 634 | True / True | unchanged |
| netlib/stocfor2 | native | pfi | 20261001 | OPTIMAL / 1627 | OPTIMAL / 1627 | True / True | unchanged |
| netlib/stocfor2 | jump | pfi | 20261001 | OPTIMAL / 1626 | OPTIMAL / 1626 | True / True | unchanged |
| netlib/degen3 | native | pfi | 20261001 | OPTIMAL / 2075 | OPTIMAL / 2075 | True / True | unchanged |
| netlib/degen3 | jump | pfi | 20261001 | OPTIMAL / 2036 | OPTIMAL / 2036 | True / True | unchanged |
| netlib/stocfor1 | native | pfi | 20261001 | OPTIMAL / 100 | OPTIMAL / 100 | True / True | unchanged |
| netlib/stocfor1 | jump | pfi | 20261001 | OPTIMAL / 93 | OPTIMAL / 93 | True / True | unchanged |
| netlib/scsd1 | native | pfi | 20261001 | OPTIMAL / 104 | OPTIMAL / 104 | True / True | unchanged |
| netlib/scsd1 | jump | pfi | 20261001 | OPTIMAL / 104 | OPTIMAL / 104 | True / True | unchanged |
| netlib/scsd8 | native | pfi | 20261001 | OPTIMAL / 1095 | OPTIMAL / 1095 | True / True | unchanged |
| netlib/scsd8 | jump | pfi | 20261001 | OPTIMAL / 1095 | OPTIMAL / 1095 | True / True | unchanged |
| netlib/ship04s | native | pfi | 20261001 | OPTIMAL / 333 | OPTIMAL / 333 | True / True | unchanged |
| netlib/ship04s | jump | pfi | 20261001 | OPTIMAL / 333 | OPTIMAL / 333 | True / True | unchanged |
| netlib/ship08s | native | pfi | 20261001 | OPTIMAL / 466 | OPTIMAL / 466 | True / True | unchanged |
| netlib/ship08s | jump | pfi | 20261001 | OPTIMAL / 466 | OPTIMAL / 466 | True / True | unchanged |
| netlib/ship12s | native | pfi | 20261001 | OPTIMAL / 643 | OPTIMAL / 643 | True / True | unchanged |
| netlib/ship12s | jump | pfi | 20261001 | OPTIMAL / 643 | OPTIMAL / 643 | True / True | unchanged |
| netlib/pilot4 | native | pfi | 20261001 | OPTIMAL / 1067 | OPTIMAL / 1067 | True / True | unchanged |
| netlib/pilot4 | jump | pfi | 20261001 | OPTIMAL / 971 | OPTIMAL / 971 | True / True | unchanged |
| netlib/pilotnov | native | pfi | 20261001 | INFEASIBLE / 0 | INFEASIBLE / 0 | False / False | unchanged |
| netlib/pilotnov | jump | pfi | 20261001 | INFEASIBLE / 0 | INFEASIBLE / 0 | False / False | unchanged |
| netlib/25fv47 | native | pfi | 20261001 | OPTIMAL / 3087 | OPTIMAL / 3087 | True / True | unchanged |
| netlib/25fv47 | jump | pfi | 20261001 | OPTIMAL / 2523 | OPTIMAL / 2523 | True / True | unchanged |
| netlib/80bau3b | native | pfi | 20261001 | OPTIMAL / 3333 | OPTIMAL / 3333 | True / True | unchanged |
| netlib/80bau3b | jump | pfi | 20261001 | OPTIMAL / 3331 | OPTIMAL / 3331 | True / True | unchanged |
| netlib/wood1p | native | pfi | 20261001 | OPTIMAL / 165 | OPTIMAL / 165 | True / True | unchanged |
| netlib/wood1p | jump | pfi | 20261001 | OPTIMAL / 165 | OPTIMAL / 165 | True / True | unchanged |
| netlib/woodw | native | pfi | 20261001 | OPTIMAL / 1039 | OPTIMAL / 1039 | True / True | unchanged |
| netlib/woodw | jump | pfi | 20261001 | OPTIMAL / 1010 | OPTIMAL / 1010 | True / True | unchanged |
| netlib/bandm | native | pfi | 20261001 | OPTIMAL / 328 | OPTIMAL / 328 | True / True | unchanged |
| netlib/bandm | jump | pfi | 20261001 | OPTIMAL / 328 | OPTIMAL / 328 | True / True | unchanged |
| netlib/capri | native | pfi | 20261001 | OPTIMAL / 262 | OPTIMAL / 262 | True / True | unchanged |
| netlib/capri | jump | pfi | 20261001 | OPTIMAL / 251 | OPTIMAL / 251 | True / True | unchanged |
| netlib/recipe | native | pfi | 20261001 | OPTIMAL / 28 | OPTIMAL / 28 | True / True | unchanged |
| netlib/recipe | jump | pfi | 20261001 | OPTIMAL / 28 | OPTIMAL / 28 | True / True | unchanged |
| netlib/scorpion | native | pfi | 20261001 | OPTIMAL / 205 | OPTIMAL / 205 | True / True | unchanged |
| netlib/scorpion | jump | pfi | 20261001 | OPTIMAL / 206 | OPTIMAL / 206 | True / True | unchanged |
| miplib/air03 | native | pfi | 20261001 | OPTIMAL / 396 | OPTIMAL / 396 | True / True | unchanged |
| miplib/air03 | jump | pfi | 20261001 | OPTIMAL / 396 | OPTIMAL / 396 | True / True | unchanged |
| miplib/air04 | native | pfi | 20261001 | OPTIMAL / 4483 | OPTIMAL / 4483 | True / True | unchanged |
| miplib/air04 | jump | pfi | 20261001 | OPTIMAL / 4483 | OPTIMAL / 4483 | True / True | unchanged |
| miplib/air05 | native | pfi | 20261001 | OPTIMAL / 1469 | OPTIMAL / 1469 | True / True | unchanged |
| miplib/air05 | jump | pfi | 20261001 | OPTIMAL / 1469 | OPTIMAL / 1469 | True / True | unchanged |
| miplib/blend2 | native | pfi | 20261001 | OPTIMAL / 651 | OPTIMAL / 651 | True / True | unchanged |
| miplib/blend2 | jump | pfi | 20261001 | OPTIMAL / 650 | OPTIMAL / 650 | True / True | unchanged |
| miplib/markshare1 | native | pfi | 20261001 | OPTIMAL / 13 | OPTIMAL / 13 | True / True | unchanged |
| miplib/markshare1 | jump | pfi | 20261001 | OPTIMAL / 13 | OPTIMAL / 13 | True / True | unchanged |
| miplib/markshare2 | native | pfi | 20261001 | OPTIMAL / 20 | OPTIMAL / 20 | True / True | unchanged |
| miplib/markshare2 | jump | pfi | 20261001 | OPTIMAL / 20 | OPTIMAL / 20 | True / True | unchanged |
| miplib/nw04 | native | pfi | 20261001 | OPTIMAL / 191 | OPTIMAL / 191 | True / True | unchanged |
| miplib/nw04 | jump | pfi | 20261001 | OPTIMAL / 191 | OPTIMAL / 191 | True / True | unchanged |
| miplib/10teams | native | pfi | 20261001 | OPTIMAL / 1505 | OPTIMAL / 1505 | True / True | unchanged |
| miplib/10teams | jump | pfi | 20261001 | OPTIMAL / 1505 | OPTIMAL / 1505 | True / True | unchanged |
