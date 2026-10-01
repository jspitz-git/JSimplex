# Reliable-price refinement: paired model outcomes

Baseline: `c0db99f`. Identical 30-job manifest, policy isolation, reader equivalence and original-model checks. Timings include compilation and are not benchmarks.

| Model | Reader / seed | Algorithm / manager | Before: status / iterations | After: status / iterations |
| --- | --- | --- | --- | --- |
| miplib/mod010 | permuted / 1 | primal / pfi | OPTIMAL / 598 | OPTIMAL / 598 |
| miplib/mod010 | permuted / 1 | primal / forrest_tomlin | NUMERICAL_ERROR / 266 | OPTIMAL / 590 |
| miplib/mod010 | permuted / 1 | primal / suhl_suhl | NUMERICAL_ERROR / 265 | OPTIMAL / 576 |
| miplib/mod010 | permuted / 1 | primal / bartels_golub | OPTIMAL / 615 | OPTIMAL / 615 |
| miplib/mod010 | permuted / 17 | primal / pfi | OPTIMAL / 679 | OPTIMAL / 679 |
| miplib/mod010 | permuted / 2 | primal / pfi | OPTIMAL / 619 | OPTIMAL / 619 |
| miplib/mod010 | permuted / 29 | primal / pfi | OPTIMAL / 586 | OPTIMAL / 586 |
| miplib/mod010 | native | primal / pfi | OPTIMAL / 532 | OPTIMAL / 532 |
| miplib/mod010 | jump | primal / pfi | OPTIMAL / 595 | OPTIMAL / 595 |
| netlib/degen2 | native | primal / pfi | OPTIMAL / 1034 | OPTIMAL / 1034 |
| netlib/degen2 | jump | primal / pfi | OPTIMAL / 1031 | OPTIMAL / 1031 |
| netlib/boeing1 | native | primal / pfi | NUMERICAL_ERROR / 202 | OPTIMAL / 558 |
| netlib/boeing1 | jump | primal / pfi | OPTIMAL / 559 | OPTIMAL / 559 |
| miplib/p0201 | native | primal / pfi | NUMERICAL_ERROR / 110 | OPTIMAL / 244 |
| miplib/p0201 | jump | primal / pfi | NUMERICAL_ERROR / 110 | OPTIMAL / 244 |
| miplib/misc07 | native | primal / pfi | OPTIMAL / 263 | OPTIMAL / 263 |
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
| netlib/degen3 | native | primal / pfi | OPTIMAL / 3613 | OPTIMAL / 3613 |
| netlib/degen3 | jump | primal / pfi | OPTIMAL / 4089 | OPTIMAL / 4089 |

Five previous price-disagreement failures now reach verified optima. The other 25 configurations retain status, iterations, refactorizations, phase sequence and objective exactly. Native cycle and JuMP stocfor2 remain numerical errors at their previous endpoints.

Production SHA-256: `70f3310f964ddd296d56375a0f19cecc4051c466780bb6836c6540d10de31cad`.
