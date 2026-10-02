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
