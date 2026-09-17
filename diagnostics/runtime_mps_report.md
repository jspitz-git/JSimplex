# runtime.mps: numerical failure in the reduced LP

## Reproduction

- Source: `C:\Disk_D\tmp\runtime.mps` (10,395,519 bytes; SHA-256 `D0AC16E1A52A7D3411CBAC28616BBA9D3BEB0C0EDBDB2D72AB0477CE075F6C68`).
- Repository base: `c6663648a4c591eb02e8a6d3a6a4ae5e2cecb971`; branch `investigate/runtime-numerics` in `.worktrees/runtime-numerics`.
- Julia 1.13.0; `Sys.MACHINE == "x86_64-w64-mingw32"`; one Julia thread. `Float64` + `basis_refactorization=:native` uses `UMFPACKBackend` inside `SuhlSuhlFactorization`.
- Options: `iteration_limit=100_000`, `time_limit=6000.0`, `basis_update=:suhl_suhl`, `basis_refactorization=:native`, `refactorization_interval=50`. The diagnostic script disables progress logging; this does not alter numerical settings.
- Run from the worktree: `julia --project=. diagnostics/runtime_probe.jl > diagnostics/runtime_probe_2.log 2>&1`, using the actual Julia binary if the WindowsApps `julia` alias is broken. The script calls `presolve_problem`, `scale_problem`, `make_dual_feasible!`, then `_dual_optimize!` on the reduced LP, so it never enters the original-LP retry.
- Original matrix: 43,021 × 47,148, 277,210 nonzeros. Reduced matrix: 28,453 × 31,615, 211,789 nonzeros. The second run reproduced `NUMERICAL_ERROR: dual feasibility lost` after 22,256 completed iterations and 446 refactorizations. The first run gave the same values.

## What changes at iteration 22,256

At 22,256 completed pivots, just before the 50-update refactorization, `dinf=(0.0, 0)`. The four affected variables have feasible stored reduced costs; recomputing them from the **updated** Suhl–Suhl factors agrees with those stored values within about `1.2e-7`. They have the same basis state and perturbation cost `0.0` across the refactorization. Solving the **same** basis matrix directly with a fresh sparse LU before refactorization already gives the four infeasible reduced costs listed below. The scheduled refactorization then reproduces those values and `dinf=(801.7210961960537, 4)`.

| Reduced variable index | Kind | State | Reduced cost before | Perturbed cost | Reduced cost from fresh LU / after |
| ---: | --- | --- | ---: | ---: | ---: |
| 19825 | structural | `AT_LOWER` | 7.534705546196206 | 0.0 | -339.1978356350196 |
| 19826 | structural | `AT_LOWER` | 7.534705546196206 | 0.0 | -339.1978356350196 |
| 50165 | slack for reduced row 18550 | `AT_UPPER` | -62.16430894590371 | 0.0 | 115.87653929289922 |
| 57787 | slack for reduced row 26172 | `AT_LOWER` | 17.930629460959924 | 0.0 | -7.448885633115343 |

The infinity norm of the difference between updated-factor and fresh-LU dual solutions is `710.2138930273238`. For the updated factors, `‖Bᵀy-c_B‖∞ = 0.00010496988704744581`; with fresh LU it is `4.662615002037818e-10`. Thus the observed dual-solve error amplifies that residual by at least `6.76e6` in infinity norm. The corresponding `‖Bx-b‖∞` is `0.0014118292091872086` before and `0.02731552551535636` after refactorization; `‖x‖∞ ≈ 4.164e12`, so the primal residuals are small in relative terms but cannot justify a successful classification.

The last actual pivot (iteration 22,255 → 22,256) leaves reduced variable 43656 from basis row 12041 and enters variable 21806. The tableau-row and tableau-column pivot values both equal `-1.32362637375`; an independent fresh solve gives the same value to the displayed precision. The leaving bound violation is `2.5219018933205835`. The bound-flipping ratio test sees variable 21762 at its lower bound with reduced cost `0`, oriented coefficient `1.32362637375`, and width `1.403890754`, so its flip gain is `1.8582268278581735`. This leaves about `0.663675` of the violation. Entering variable 21806 also has step `0` and gain `1.8582268278581735`, enough to finish the pivot. The selected pivot is far above the `1e-12` zero tolerance. These measurements do not identify a pivot-direction or bound-flipping error.

## Assessment and next step

The four violations first appear when the updated-basis dual solve is replaced by the fresh sparse-LU solve of the same, sensitive basis. No individual software defect is isolated by these measurements. Keep `NUMERICAL_ERROR`; none of `OPTIMAL`, `INFEASIBLE`, or `UNBOUNDED` is supported. A safe follow-up is to detect growth in `‖Bᵀy-c_B‖` during Suhl–Suhl updates, refactorize or refine the solve earlier, and recheck dual feasibility after that correction. If the fresh basis is still dual infeasible, retain `NUMERICAL_ERROR` unless a separately verified recovery step restores feasibility.

The focused factorization and dual-simplex tests pass (`1631/1631`) with `julia --project=. -e 'using JSimplex, Test; @testset "Runtime-relevant tests" begin include("test/factorization_tests.jl"); include("test/dual_simplex_tests.jl"); end'`. The full baseline `Pkg.test()` run on `c666364` exited 1 and exposed at least one separate Windows type mismatch in `test/primal_simplex_tests.jl`: `_primal_weighted_score(::BigFloat, ::Tuple{Int32, BigFloat})` has no method (the available method expects `Tuple{Int64, BigFloat}`). No solver code or regression test was changed for this investigation.
