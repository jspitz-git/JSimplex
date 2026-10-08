# Native postsolve box-hint integration

This narrowly integrates the runtime primal HH/native320 postsolve repair from
experimental commit `21bca604eb8c59e7b58887196f93e280ee48db42` onto master
`8d35fd0687fc92e7602be45789ff25a5c8a58f9f`. Other experimental numerical guard
and certificate-reuse changes are excluded. The solver file and new regression
file match the original fix exactly.

## Cause and change

Unscaling can amplify a tolerated column-bound violation. The native basis
projection previously treated the resulting out-of-bound hint coordinate as an
interior variable, attempting to make it basic and blocking useful exchanges.
For an already-infeasible Float32/Float64 native hint, the repair makes a private
copy, clips structural values into their original column bounds, and recomputes
feasibility and row activities before the existing basis projection. The hint
remains subject to reconstructed-point and original feasibility certificates.
Tolerances, pricing, arithmetic precision, caller data, and checked-policy
behavior are unchanged.

## Earlier reproduction

The diagnosed full master baseline completed OPTIMAL but needed 61,021 cleanup
iterations after the reduced solve handed off at iteration 120,063. Thus it
reproduced an expensive detour, not the user's eventual numerical failure.
The repaired experimental full solve completed OPTIMAL at iteration 121,219,
with 1,156 cleanup iterations and original objective 51,425,691.76210442.
An isolated override of only this projection function on the original master
also produced 1,156 cleanup iterations. Those are single diagnosed runs, not a
repeated performance benchmark or proof that every numerical failure is fixed.
Detailed earlier reports remain preserved in the experimental worktree under
`diagnostics/numerical-guard-repair/RUNTIME320.md` and its `results` directory.

## Integration verification

The checked-in `tests.jl` exercises the new regression plus existing postsolve
hint/projection/cleanup and presolve tests. The new regression covers both bound
directions, five basis managers, Float32/64, caller immutability, zero-exchange
cases, and checked-policy rejection.

Fresh verification uses Julia 1.13.0/aarch64, normal compilation (`-g0 -O1`),
one Julia/BLAS thread, the existing 8 GiB virtual-memory / 6 GiB available-RAM /
1 GiB swap guard, and a 600-second per-process limit. The saved runtime handoff
is replayed by `diagnostics/native-certificate-recovery/reproduce/handoff_cleanup.jl`
with the integration checkout as the Julia project, without method overrides.
The handoff is diagnostic saved state, not a general checkpoint guarantee.
Raw logs are preserved in `.superpowers/postsolve-box-integration` in the
integration worktree. Selected checks do not imply that the full project suite
or CI passes. An independent read-only review found no hidden dependency on
excluded repairs and no blocker in the integration.

Fresh results on 2026-10-08:

- All **696** focused and presolve assertions passed with normal compilation;
  process exit 0, wall time 231.11 s, peak RSS 1,644,012 KiB.
- Saved runtime cleanup completed **OPTIMAL**, originally primal feasible,
  objective **51,425,691.76210442**, with **1,156** additional iterations
  (121,219 cumulative). It required no auxiliary cleanup or original-LP restart.
- Cleanup measured 20.56 s, including 11.59 s compilation; process exit 0,
  wall time 23.03 s, peak RSS 993,476 KiB.
- Source digest stayed unchanged during both checks. `source.json`, `tests.log`,
  and `cleanup.toml` retain the compact provenance and verification evidence.

A new full solve was not repeated for this integration; the user will independently
repeat runtime on their machine. The fresh saved-handoff test checks the exact
integrated code at the previously problematic postsolve boundary.
