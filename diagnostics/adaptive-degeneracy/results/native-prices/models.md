# Paired whole-model results

Only the new native price-recovery helper is disabled in the control. All other diagnostic policies and instrumentation are identical. Timings include compilation and are not a benchmark.

| Model | Reader / seed | Algorithm / manager | Control status / iterations | Corrected status / iterations | Price corrections |
| --- | --- | --- | --- | --- | --- |
| miplib/mod010 | permuted / 1 | primal / pfi | NUMERICAL_ERROR / 272 | NUMERICAL_ERROR / 272 | 1 |
| miplib/mod010 | permuted / 1 | primal / forrest_tomlin | NUMERICAL_ERROR / 266 | NUMERICAL_ERROR / 266 | 0 |
| miplib/mod010 | permuted / 1 | primal / suhl_suhl | NUMERICAL_ERROR / 265 | NUMERICAL_ERROR / 265 | 0 |
| miplib/mod010 | permuted / 1 | primal / bartels_golub | OPTIMAL / 615 | OPTIMAL / 615 | 0 |
| miplib/mod010 | permuted / 17 | primal / pfi | OPTIMAL / 679 | OPTIMAL / 679 | 0 |
| miplib/mod010 | permuted / 2 | primal / pfi | OPTIMAL / 619 | OPTIMAL / 619 | 0 |
| miplib/mod010 | permuted / 29 | primal / pfi | OPTIMAL / 586 | OPTIMAL / 586 | 0 |
| miplib/mod010 | native | primal / pfi | OPTIMAL / 532 | OPTIMAL / 532 | 0 |
| miplib/mod010 | jump | primal / pfi | OPTIMAL / 595 | OPTIMAL / 595 | 0 |
| netlib/degen2 | native | primal / pfi | NUMERICAL_ERROR / 2160 | NUMERICAL_ERROR / 660 | 1 |
| netlib/degen2 | jump | primal / pfi | TIME_LIMIT / 868714 | NUMERICAL_ERROR / 733 | 1 |
| netlib/boeing1 | native | primal / pfi | NUMERICAL_ERROR / 202 | NUMERICAL_ERROR / 202 | 0 |
| netlib/boeing1 | jump | primal / pfi | OPTIMAL / 559 | OPTIMAL / 559 | 0 |
| miplib/p0201 | native | primal / pfi | NUMERICAL_ERROR / 110 | NUMERICAL_ERROR / 110 | 0 |
| miplib/p0201 | jump | primal / pfi | NUMERICAL_ERROR / 110 | NUMERICAL_ERROR / 110 | 0 |
| miplib/misc07 | native | primal / pfi | NUMERICAL_ERROR / 198 | NUMERICAL_ERROR / 197 | 1 |
| miplib/misc07 | jump | primal / pfi | OPTIMAL / 284 | OPTIMAL / 284 | 0 |
| netlib/scsd6 | native | primal / pfi | OPTIMAL / 340 | OPTIMAL / 340 | 0 |
| netlib/scsd6 | native | primal / forrest_tomlin | OPTIMAL / 326 | OPTIMAL / 326 | 0 |
| netlib/scsd6 | native | primal / suhl_suhl | OPTIMAL / 329 | OPTIMAL / 329 | 0 |
| netlib/scsd6 | native | primal / bartels_golub | OPTIMAL / 337 | OPTIMAL / 337 | 0 |
| netlib/scsd6 | jump | primal / pfi | OPTIMAL / 340 | OPTIMAL / 340 | 0 |
| netlib/cycle | native | primal / pfi | NUMERICAL_ERROR / 868 | NUMERICAL_ERROR / 868 | 0 |
| netlib/cycle | jump | primal / pfi | OPTIMAL / 1291 | OPTIMAL / 1291 | 0 |
| netlib/stocfor2 | native | primal / pfi | OPTIMAL / 1970 | OPTIMAL / 1970 | 0 |
| netlib/stocfor2 | jump | primal / pfi | NUMERICAL_ERROR / 1957 | NUMERICAL_ERROR / 1957 | 0 |
| miplib/mod010 | native | dual / pfi | OPTIMAL / 679 | OPTIMAL / 679 | 0 |
| miplib/mod010 | jump | dual / pfi | OPTIMAL / 712 | OPTIMAL / 712 | 0 |
| netlib/degen3 | native | primal / pfi | TIME_LIMIT / 109743 | NUMERICAL_ERROR / 2345 | 1 |
| netlib/degen3 | jump | primal / pfi | TIME_LIMIT / 112654 | NUMERICAL_ERROR / 2891 | 1 |

24 unaffected configurations retain status, iteration/refactorization counts, phase sequence and objective exactly. Both arms have 17 verified optima. The control has ten numerical errors and three time limits; corrected pricing has 13 numerical errors, including six later artificial-removal failures.

Production SHA-256: `e2e5be10660627f80fe4c146758d116c847b1d5530e5861c79816dc74e66da16`.

See the raw TOML reports for failure messages, original feasibility, objective agreement, policy flags and instrumentation hashes.
