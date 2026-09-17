# runtime.mps: numerical failure in the reduced LP

## Reproduction

- Source: `C:\Disk_D\tmp\runtime.mps` (10,395,519 bytes; SHA-256 `D0AC16E1A52A7D3411CBAC28616BBA9D3BEB0C0EDBDB2D72AB0477CE075F6C68`).
- Repository base: `c6663648a4c591eb02e8a6d3a6a4ae5e2cecb971`; branch `investigate/runtime-numerics` in `.worktrees/runtime-numerics`.
- Julia 1.13.0; `Sys.MACHINE == "x86_64-w64-mingw32"`; one Julia thread. `Float64` + `basis_refactorization=:native` uses `UMFPACKBackend` inside `SuhlSuhlFactorization`.
- Options: `iteration_limit=100_000`, `time_limit=6000.0`, `basis_update=:suhl_suhl`, `basis_refactorization=:native`, `refactorization_interval=50`. The diagnostic script disables progress logging; this does not alter numerical settings.
- Run `julia --project=. -e 'using Pkg; Pkg.instantiate()'` once in the worktree, then `julia --project=. diagnostics/runtime_probe.jl > diagnostics/runtime_probe_2.log 2>&1` for the original probe or `julia --project=. diagnostics/runtime_pivot_audit.jl > diagnostics/runtime_pivot_audit.log 2>&1` for the per-pivot audit. Use the actual Julia binary if the WindowsApps `julia` alias is broken. Both scripts call `presolve_problem`, `scale_problem`, `make_dual_feasible!`, then `_dual_optimize!` on the reduced LP, so neither enters the original-LP retry.
- Original matrix: 43,021 × 47,148, 277,210 nonzeros. Reduced matrix: 28,453 × 31,615, 211,789 nonzeros. The second run reproduced `NUMERICAL_ERROR: dual feasibility lost` after 22,256 completed iterations and 446 refactorizations. The first run gave the same values.

## First freshly computed violation: iteration 22,233

The audit assembles each basis in separate arrays and uses a new sparse LU after **every completed pivot from 22,207 through 22,256**, before the scheduled refactorization. It does not call `basis_matrix(workspace)` or `recompute!` and writes no workspace field. The freshly computed costs are dual feasible after iteration 22,232 and first violate dual tolerance after **22,233**: four variables, sum `950.84920856094`. Fresh-LU infeasibility is present at 22,233, 22,235–22,238, and 22,251–22,256 (11 of 50 sampled bases). It disappears at 22,234 and 22,239–22,250. The workspace's incrementally stored prices remain dual feasible until the refactorization at 22,256.

The pivot from 22,232 to 22,233 replaces basic variable 40838 in basis row 9223 with variable 1408. The four affected variables do not change basis state or perturbation cost:

| Index | State | Stored reduced cost before and after | Fresh reduced cost before | Fresh reduced cost after | Perturbed cost |
| ---: | --- | ---: | ---: | ---: | ---: |
| 19825 | `AT_LOWER` | 7.534705546315035 | 158.68343771912743 | -396.85020318096633 | 0.0 |
| 19826 | `AT_LOWER` | 7.534705546315035 | 158.68343771912743 | -396.85020318096633 | 0.0 |
| 50165 | `AT_UPPER` | -62.16430894596473 | -139.7764315191441 | 145.47998056751288 | 0.0 |
| 57787 | `AT_LOWER` | 17.93062946096862 | 28.994146939202704 | -11.66882163149448 | 0.0 |

The leaving variable is below its bound by `2.322893883551531`. The bound-flipping ratio test has 26 eligible candidates and chooses 1408 with **no bound flips**; a separate read-only replay using fresh prices and tableau row makes the same choice. The oriented coefficient is `0.017744543230273073`; stored and fresh candidate steps are `41.40093315286712` and `41.40095142076178`. The pivot element from the tableau row and column is `-0.01774454323027307` in both the updated and fresh solves. The updated and fresh solves of the tableau row coincide: `‖Bᵀρ-e₉₂₂₃‖∞ = 1.249000902703301e-16`, and the row coefficient is zero for all four variables. Their stored prices therefore remain unchanged across this pivot.

Transporting the *fresh pre-pivot* dual solution by that same pivot produces a dual solution for the new basis with `‖Bᵀy-c_B‖∞ = 6.709073857907033e-10` and retains all four feasible pre-pivot prices. A separate fresh LU of the **new** basis has residual `2.148357344337131e-10` but gives the four infeasible prices above. These two dual vectors differ by `1137.9021668826456` in infinity norm, while the floating-point calculations give `‖Bᵀ(y₁-y₂)‖∞ = 6.644707241322041e-10` and `‖Bᵀ‖∞ = 24.615317678906248`. The resulting directional condition estimate is `4.215358526429109e13`; its last digits are subject to roundoff. The opposite price signs from two small-residual solves of the same basis demonstrate severe numerical sensitivity; a Float64 fresh-LU price is not by itself an exact dual-feasibility certificate.

For the bases immediately before and after pivot 22,233, `‖Bx-b‖∞` using the workspace primal is `0.0009765625` and `0.001606963535800959`; using fresh LU primal solves it is `0.013124932135767153` and `0.019037830827296365`. Fresh dual residuals are `6.709073857907033e-10` and `2.148357344337131e-10`.

A control run without fresh LU and the measured run have **identical traces for all 50 pivots**, including basis row, entering/leaving variable, bound flips, and tableau pivot values. Both stop with `NUMERICAL_ERROR: dual feasibility lost` at iteration 22,256 after 446 refactorizations. A third measurement run reproduced all 50 per-pivot log lines exactly.

## What scheduled refactorization reveals at iteration 22,256

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

Fresh LU first reports the four violations at iteration 22,233, but the transported dual vector shows that even a small-residual fresh solve cannot reliably determine their signs in this ill-conditioned basis. The investigated pivot has the same row/column value and ratio-test choice with updated and fresh data. No individual algorithm or factorization-update defect is isolated by these measurements. Keep `NUMERICAL_ERROR`; none of `OPTIMAL`, `INFEASIBLE`, or `UNBOUNDED` is supported. A safe follow-up is to detect growth in the sensitivity or solve residual during Suhl–Suhl updates, refactorize or refine earlier, and recheck dual feasibility with a reliability criterion strong enough for the observed conditioning. If feasibility cannot be established, retain `NUMERICAL_ERROR`.

The focused factorization and dual-simplex tests pass (`1631/1631`) with `julia --project=. -e 'using JSimplex, Test; @testset "Runtime-relevant tests" begin include("test/factorization_tests.jl"); include("test/dual_simplex_tests.jl"); end'`. The full baseline `Pkg.test()` run on `c666364` exited 1 and exposed at least one separate Windows type mismatch in `test/primal_simplex_tests.jl`: `_primal_weighted_score(::BigFloat, ::Tuple{Int32, BigFloat})` has no method (the available method expects `Tuple{Int64, BigFloat}`). No solver code or regression test was changed for this investigation.
