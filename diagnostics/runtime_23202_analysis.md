# `runtime.mps`: first failing basis at iteration 23,202

The Windows audit in commit `650d2ee` used Julia 1.13.0 with one Julia
thread and six BLAS threads. It checked a fresh sparse LU after each pivot
from 23,156 onward. The LU first failed after pivot 23,202; the basis at
23,201 still factorized. That pivot replaced slack 57,247 in basis row
25,632 with slack 57,784. The updated Suhl–Suhl factorization reported
a tableau pivot of `-6.761199819713067e-7`, a zero dual step, and a
primal step of `1.9581594892750013e9`.

I reconstructed the two basis matrices from the audit CSV, the same MPS
file (SHA-256 `d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68`),
presolve, and scaling. For the old basis and the entering slack column:

| Solve | Tableau element in row 25,632 | Residual infinity norm |
| --- | ---: | ---: |
| Fresh Float64 LU | `7.024451075124088e-48` | `7.09e-17` |
| Fresh Float64 QR, rank 28,453 at tolerance `1e-12` | `-4.839765663383502e-25` | `2.16e-16` |
| Float64 LU with 512-bit residual refinement | `-3.38e-111` | `1.38e-103` |

The refined result is consistent with a zero tableau element; it is not
an exact-arithmetic proof. The new basis has a smallest Float64 LU `U`
diagonal of `1.07e-18`; sparse QR estimates rank 28,452 at tolerance
`1e-12`. On Windows fresh LU reports a singular matrix. On this Linux
machine it completes, but the resulting basis is severely ill-conditioned.

I also replayed the 45 logged basis replacements after the preceding
refactorization, starting from the reconstructed basis at iteration
23,156. With the same Suhl–Suhl update implementation on aarch64, the
updated factors report `4.76e-7` for that next tableau element and the
direction has residual infinity norm `2.63e-3` against the old basis.
Thus the wrong nonzero pivot is reproducible without the Windows LU
failure. The exact sign depends on the floating-point path.

This evidence points to error accumulated in the updated factorization
as the immediate cause of the invalid pivot. Near-zero dual steps show
degeneracy in the same region, but perturbing the costs would only
change which pivots are tried.

## Refactorization before the pivot

The Windows counterfactual in commit `f17464a` rebuilt the same basis
at iteration 23,201 before choosing the next pivot. Immediately before
the rebuild, the updated direction had pivot `-6.761199819713067e-7`
and residual infinity norm `0.003909944934112411`; a fresh LU direction
had pivot `-0.0` and residual `1.7869969230581004e-17`. The rebuild
kept dual infeasibility at zero. The next pivot still used row 25,632,
but entered column 8,590 with tableau pivot `-62.27918240194156`.
The resulting basis passed fresh LU.

The production guard therefore checks the basis equation `Bd = a`
before accepting a pivot no more than ten times the dual ratio test's
coefficient cutoff. If its residual is too large relative to the row
terms and pivot size, the solver rebuilds the basis and repeats that
iteration once. A second failed check returns `NUMERICAL_ERROR`. This
guards the observed false pivot without forcing early refactorizations
for full-sized pivots whose residuals are tiny relative to their size.
The guard rejects the replayed false direction (`4.76e-7` pivot,
`2.63e-3` residual) on this machine. A local run with the guard still
reached 23,201 iterations in 84.5 seconds, matching the prior trace
and elapsed time to that point.
The Windows run still needs to verify the guarded solver beyond 23,202.
