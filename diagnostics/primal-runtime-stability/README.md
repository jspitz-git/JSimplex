# Legacy primal runtime stability

Base: 8c694d0. The preceding optimization series is merged and pushed; this
investigation is isolated in fix/primal-runtime-stability.

## Reproduced failure

Runtime.mps SHA-256:
`d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68`.
Legacy primal, steepest-edge, native factorization, interval 80, Float64,
one Julia and one BLAS thread. PFI fails on the reduced model after 4,135
iterations at approximately 57 seconds with a singular native refactorization.
The original-model retry reaches the 180-second cap at 14,439 total iterations.
These timings overlap unrelated background compilation and are diagnostic only.

The accepted zero-step pivot immediately before singularity is
1.3581620769620776e-12, with direction infinity norm 2.12982140456808e7.
The transpose row gives 1.3581620769620774e-12. Fresh native LU reproduces both:
refactoring the old basis does not eliminate their correlated error.
The new basis is singular. Independent residual refinement at 128 and 256 bits
gives pivot magnitudes about 1.58e-47 and 1.13e-66, respectively.
Higher precision is used only as a diagnostic reference.

One compensated Float64 residual correction gives a pivot correction
-1.3581623130805296e-12, leaving -2.36e-19. Thus native arithmetic already detects
that the proposed pivot is unreliable, although forward/transpose agreement and
ordinary componentwise backward error alone accept it.

## Candidate fix

Only weak legacy Float32/Float64 primal pivots get an extra compensated residual
probe against the actual basis. One correction is solved in the problem type;
the pivot is rejected if its change exceeds the existing relative agreement scale.
The probe does not publish a corrected direction or mutate the basis. Rejection
uses the existing bounded fresh-basis/candidate retries. Strong pivots, adaptive
strategy and generic/exact arithmetic retain their paths.

The two-row correlated-error regression failed 24 assertions before the fix.
Initial focused checks pass 501 assertions, including genuine scaled small pivots.
The captured runtime pivot is rejected by all four managers (16 assertions),
without changing its direction or the basis. Whole-LP follow-up is in progress;
these local checks alone do not establish stable completion of runtime.mps.

## A second cause: aggregate bound-snap rejection

The first guard alone prevents the singular exchange, but PFI still reaches a
180-second cap with only 4,908 iterations and 1,256 refactorizations. An independent
256-bit reduced-cost check confirms the selected column really is improving;
false pricing is not supported by this snapshot.

In the same captured state, snapping the structural leaving variable at row
14,325 would produce a maximum individual violation of 9.9624e-8, within the
1e-7 tolerance. Its pivot is 10,472.8588. The snap check incorrectly summed all
these tolerated errors (4.0712e-6) and rejected this and other large safe pivots.
The ordinary legacy Harris and feasibility checks already operate per bound.
The largest candidate, row 25,257, remains genuinely unsafe (3.84e-6 individual
violation); the correction does not admit it.

Legacy bound-snap validation now uses the same per-bound criterion. A structural
regression fails 48 assertions before this change and passes afterward. The
expanded focused suite passes 1,162 assertions; replay of the captured state
passes 32 checks across all managers, selecting row 14,325 while continuing to
reject the original false pivot. The 600-second PFI run no longer fails, but reaches only 11,339 iterations with
4,443 refactorizations and an almost stationary phase-I objective of 605,519.5025.
This is not a convergence or performance fix for the complete runtime problem.
All four completed bounded tests without a numerical-error termination or an
original-model restart, but none solved runtime.mps:

| Manager | Limit (s) | Iterations | Refactorizations |
| --- | ---: | ---: | ---: |
| PFI | 600 | 11,339 | 4,443 |
| Forrest–Tomlin | 300 | 6,255 | 1,288 |
| Suhl–Suhl | 300 | 13,675 | 10,284 |
| Bartels–Golub | 300 | 8,664 | 2,024 |

These are bounded stability observations, not evidence of full convergence.
Rare-path compilation also affects timings. The first combined batch reached its
global watchdog before BG completed; BG was rerun with its full 300-second budget.

The SS endpoint continues to alternate two bases even after a native refresh and
fresh DSE weights. The entering columns are 26,942 and 26,975; steps are about
3.4694e-17 and the auxiliary objective stays 605,524.4037449533. Basis identities
and states are compared in full, not inferred from hash collisions. Neither FT
nor SS reenters artificial variables in these runs.

The replay also captures the price before each accepted exchange and the implied
price from its FTRAN direction, using the basic costs from before the exchange:
- column 26,942: stored -43.8501894, direction -8.65157184;
- column 26,975: stored -43.8501894, direction -6.25253906.

This establishes a separate price/direction inconsistency. A new step must test
how to handle that disagreement; the two local fixes here do not resolve it.
Fresh pricing weights alone do not remove the cycle. The replay is a reference
continuation after refresh, not an exact restoration of the original pricing cache.

## Validation

- Focused primal checks: 1,162 assertions.
- Captured runtime state: 32 assertions across all managers.
- Broader semantic regressions: 2,698 assertions, including adaptive and exact
  arithmetic paths, using compile=min.
- Native residual/allocation checks: 125 assertions with normal compilation.
- External corpus: 80 optimal, originally feasible, objective-matching LP
  relaxations; 245 assertions. Afiro, adlittle, pk1, flugpl and fast0507,
  with primal/dual, all four managers, and native/Markowitz factorization.

A normal-compilation broader run hit the 240-second watchdog in LLVM while
compiling adaptive_pricing_integration_tests.jl:171. The broader semantic run
subsequently passed with compile=min; allocation assertions were tested separately
with normal compilation. This is not a full project-suite pass.

An independent read-only review found no concrete production defect. Dedicated
NaN/Inf correction fault injection remains a deferred coverage improvement;
cancellation and unchanged-basis behavior are covered.

## Reproduction

`reproduce/capture.jl input manager seconds output_prefix` records provenance,
phase changes and failures. Set JSIMPLEX_PRIMAL_TRACE=true to record the first
rounding-scale accepted pivots. Snapshot binaries stay local; they are not source
fixtures. `inspect.jl` checks actual basis residuals and native/wider reference
corrections; `check-captured-pivot.jl` verifies rejection across all managers.
Do not use compile=min for performance measurements. For sequential captures in
one process (including per-manager logs and snapshots at the time limit):

```sh
julia --project=. diagnostics/primal-runtime-stability/reproduce/capture-managers.jl /path/runtime.mps 300 output/primal pfi forrest_tomlin suhl_suhl bartels_golub
```

The native residual/allocation checks are test/native_residual_tests.jl. The focused
and broader semantic runners are reproduce/focused.jl and reproduce/regressions.jl.
The corpus runner and hashed input manifest are reused from
../basis-selective-preparation/reproduce/external.jl and external-inputs.toml.
reproduce/replay-stall.jl continues a saved state after refreshing the native
factor and DSE weights, recording repeated bases and accepted direction prices.
The 600-second PFI capture predates the time-limit snapshot and zero-step counters;
its absence of snapshots does not imply that the phase-I trajectory converged.

## Resource incident

WSL restarted during investigation. The task-owned baseline had already finished;
no subsequent numerical task had been launched. Before the restart, two unrelated
Julia precompilers occupied roughly 17 GiB RSS combined. The last memory reading
showed 22 GiB RAM and 5.5 GiB swap used. The exact crash cause is unconfirmed;
available journal records do not establish an OOM kill.

After restart, local PrecompileTools workloads were disabled in the main checkout
as well as the test worktree, via untracked LocalPreferences.toml. Numerical jobs
are now wrapped by an owned-process watchdog: refuse/start-stop below 6 GiB
available RAM or above 1 GiB swap use, plus time and virtual-memory limits.
The watchdog never signals editor-owned processes. These local preferences and
scratch wrappers are not changes to package defaults.
