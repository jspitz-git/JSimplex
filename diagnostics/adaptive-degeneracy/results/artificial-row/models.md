# Artificial-row recovery: paired model outcomes

Baseline: `0ee115e`, with the native price recovery already enabled. Identical inputs, readers, manager settings and isolated policies are used in both runs. Timings include compilation and are not benchmarks.

| Model | Reader / seed | Algorithm / manager | Before: status / iterations | After: status / iterations |
| --- | --- | --- | --- | --- |
| miplib/mod010 | permuted / 1 | primal / pfi | NUMERICAL_ERROR / 272 | OPTIMAL / 598 |
| miplib/mod010 | permuted / 1 | primal / forrest_tomlin | NUMERICAL_ERROR / 266 | NUMERICAL_ERROR / 266 |
| miplib/mod010 | permuted / 1 | primal / suhl_suhl | NUMERICAL_ERROR / 265 | NUMERICAL_ERROR / 265 |
| miplib/mod010 | permuted / 1 | primal / bartels_golub | OPTIMAL / 615 | OPTIMAL / 615 |
| miplib/mod010 | permuted / 17 | primal / pfi | OPTIMAL / 679 | OPTIMAL / 679 |
| miplib/mod010 | permuted / 2 | primal / pfi | OPTIMAL / 619 | OPTIMAL / 619 |
| miplib/mod010 | permuted / 29 | primal / pfi | OPTIMAL / 586 | OPTIMAL / 586 |
| miplib/mod010 | native | primal / pfi | OPTIMAL / 532 | OPTIMAL / 532 |
| miplib/mod010 | jump | primal / pfi | OPTIMAL / 595 | OPTIMAL / 595 |
| netlib/degen2 | native | primal / pfi | NUMERICAL_ERROR / 660 | OPTIMAL / 1034 |
| netlib/degen2 | jump | primal / pfi | NUMERICAL_ERROR / 733 | OPTIMAL / 1031 |
| netlib/boeing1 | native | primal / pfi | NUMERICAL_ERROR / 202 | NUMERICAL_ERROR / 202 |
| netlib/boeing1 | jump | primal / pfi | OPTIMAL / 559 | OPTIMAL / 559 |
| miplib/p0201 | native | primal / pfi | NUMERICAL_ERROR / 110 | NUMERICAL_ERROR / 110 |
| miplib/p0201 | jump | primal / pfi | NUMERICAL_ERROR / 110 | NUMERICAL_ERROR / 110 |
| miplib/misc07 | native | primal / pfi | NUMERICAL_ERROR / 197 | OPTIMAL / 263 |
| miplib/misc07 | jump | primal / pfi | OPTIMAL / 284 | OPTIMAL / 284 |
| netlib/scsd6 | native | primal / pfi | OPTIMAL / 340 | OPTIMAL / 340 |
| netlib/scsd6 | native | primal / forrest_tomlin | OPTIMAL / 326 | OPTIMAL / 326 |
| netlib/scsd6 | native | primal / suhl_suhl | OPTIMAL / 329 | OPTIMAL / 329 |
| netlib/scsd6 | native | primal / bartels_golub | OPTIMAL / 337 | OPTIMAL / 337 |
| netlib/scsd6 | jump | primal / pfi | OPTIMAL / 340 | OPTIMAL / 340 |
| netlib/cycle | native | primal / pfi | NUMERICAL_ERROR / 868 | NUMERICAL_ERROR / 868 |
| netlib/cycle | jump | primal / pfi | OPTIMAL / 1291 | OPTIMAL / 1291 |
| netlib/stocfor2 | native | primal / pfi | OPTIMAL / 1970 | OPTIMAL / 1970 |
| netlib/stocfor2 | jump | primal / pfi | NUMERICAL_ERROR / 1957 | NUMERICAL_ERROR / 1957 |
| miplib/mod010 | native | dual / pfi | OPTIMAL / 679 | OPTIMAL / 679 |
| miplib/mod010 | jump | dual / pfi | OPTIMAL / 712 | OPTIMAL / 712 |
| netlib/degen3 | native | primal / pfi | NUMERICAL_ERROR / 2345 | NUMERICAL_ERROR / 2367 |
| netlib/degen3 | jump | primal / pfi | NUMERICAL_ERROR / 2891 | NUMERICAL_ERROR / 2894 |

24 configurations retain status, iteration/refactorization counts, phase sequence and objective exactly. Four previous failures now reach verified optima; both degen3 readers progress through artificial exchanges but still fail removal. The other seven numerical failures retain their earlier endpoints.

Final production SHA-256: `6500645441568dfbee1cc3d20e2cc952fb3b223fc5a62948a92e8a6c006de9af`.
