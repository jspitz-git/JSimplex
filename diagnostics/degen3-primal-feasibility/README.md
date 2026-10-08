# Legacy primal phase-I artificial bound normalization

## Reproduced failure

Baseline `c7d35cb57139e1cb00868061d36804a4115ca5c0` fails on Netlib
`degen3.mps` with Float64, primal simplex, PFI/native, interval 80,
steepest-edge pricing, legacy strategy, partial pricing disabled, default
presolve/scaling, and relaxed integrality. The input SHA-256 is
`7a149f601961000bc365c3431276d52d1e13e04ae459f98177d6b459d9a65475`.
The reduced phase I ends at iteration 2345. Fixing its artificial columns to zero
immediately makes the phase-II point infeasible. The original-LP retry repeats
this failure after another 2116 iterations, returning `NUMERICAL_ERROR` at 4461.
This is a phase-boundary failure, not an ordinary phase-II pivot failure.

The 590 artificial columns of the reduced model have a signed sum of
`-1.5852140703135984e-6`, despite a positive basic artificial of
`1.145213623932052e-7` exceeding the `1e-7` tolerance. Tolerated negative
nonbasic values mask that positive artificial in the aggregate objective.
Tightening the artificial bounds and recomputing changes basic values by up to
`6.724391062862267e-7`, with logged aggregate infeasibility
`2.019756003088242e-6` and an individual violation of about `6.45e-7`.

Refactorizing alone at that boundary does not repair the retained nonbasic
values: it fails with exactly the baseline pivot/primal trace hash
`f034e85c6e39d7eb4dd50c5a1f9e25e9b222bb521d89bbb9b901fbd7c97bf3f4`.
A fresh reconstruction of the same basis at exact nonbasic bounds passes the
complete primal point certificate; its largest artificial magnitude is about
`1.47e-14`. Simply clipping artificial values fails the row equations.

`results/transition-probe.toml` evaluates **all** candidate points against the
phase-II bounds/model, including the point named `before`. Its failed
`before` certificate therefore does not mean phase I was already rejecting that
point under the old bounds.

## Repair and scope

The general phase-I transfer already implements bounded native normalization in
`_normalize_phase_artificial_bounds!`; the legacy primal phase-II preparation
now uses it too. Only when an artificial exceeds the removal tolerance does it
restore exact nonbasic bounds, refactor once, and certify the complete point
before fixing artificial columns to zero and restoring original costs.

The existing native-policy gate, cancellation checks, iteration/refinement
budgets, and certificate remain authoritative. No tolerance is relaxed, no
pricing heuristic is introduced, and no precision promotion is added. A point
whose artificials are already removable takes the existing path without an
extra refactorization. Checked/non-native arithmetic keeps its separate path.
The original workspace retains its numerical state if normalization fails;
performed iteration/refactorization work is still charged to its counters.

## Reproduction and evidence

`reproduce/capture.jl OUTPUT_DIRECTORY` captures phase events and data-only
snapshots. It deliberately does not serialize a live LU object. On the baseline,
`transition/state-3.bin` and `state-4.bin` capture the reduced phase boundary;
`state-7.bin` and `state-8.bin` capture the original-LP retry boundary.
`reproduce/probe_transition.jl BEFORE AFTER OUTPUT` reconstructs and compares
those points. Raw snapshots remain local under
`.superpowers/degen3-primal-feasibility/`.

The two `*_prototype.jl` scripts are **baseline-only diagnostic overrides**:
run them on `c7d35cb`, not the repaired source. They retain their generated
source in the output directory. The refactor-only prototype still fails;
normalizing before artificial removal solves the complete problem in 3660
iterations, objective `-987.2940000000002`, with original primal feasibility.
The reference objective is also recorded in
`../refactor-safety/results/models.toml` and
`../simplex-modernization/F25-references.json`.

`reproduce/regression.jl` is the real-model regression. Before the production
change it reports one passed input-hash check and one failed `OPTIMAL` check,
with no test error. An earlier launcher attempt did not create its script and
is not counted as a red regression. An earlier probe mixed fresh basic values
with old nonbasic values; that diagnostic attempt is retained locally but is
superseded by the corrected complete-point probe committed here.

Portable tests in `test/legacy_phase_artificial_bound_tests.jl` reuse the existing
artificial-bound fixtures. They cover Float32/Float64 across PFI, HH, FT, SS and
BG, original-cost restoration, complete-point validity, budgets, cancellation
and callback exceptions, failed-transfer ownership, the no-refactor fast path,
and the separate checked-policy path.

All numerical validation is sequential, using Julia 1.13.0 aarch64, one Julia
thread and one BLAS thread, disabled precompile workload, the preserved 8 GiB VM
wrapper and RAM/swap guard. No prohibited large model is solved or factored.
The first combined target suite hit its 600-second guard in LLVM register
allocation while compiling `test/primal_simplex_tests.jl:171`. This is an
incomplete compilation attempt, not a passed suite or solver numerical failure.
The focused normal-compilation suite then passed all 637 checks in 25.6 seconds,
with process peak RSS 700252 KiB. Broader semantic checks use `--compile=min`.

The additional targeted `--compile=min` suite passes 1673 checks, and the broader
selected semantic suite passes 15688 checks. These suites overlap; these are
per-run counts, not a count of unique assertions. The real-model production
regression passes all four checks. Its instrumented full run matches the
successful prototype: 3660 iterations, objective `-987.2940000000002`, original
primal feasibility, and one phase-I entry (no original-LP restart).

All 100 external combinations (five prepared inputs, two algorithms, two
refactorization backends, five managers) pass 305 assertions, including original
primal feasibility and reference objectives. This is a selected regression
matrix, not the full project test suite.

The full primal runtime HH/native320 validation finishes `OPTIMAL` after 121219
iterations, objective `51425691.76210442`, with original primal feasibility.
It passes both simplex phases, postsolve, and primal cleanup. The timed solve
block takes 759.55 seconds (0.156 seconds of compilation inside that block);
process startup/compilation outside the block is recorded separately in the
resource log. Its log
arrives in delayed batches: the first visible iteration batch already includes
phase II around iteration 94005. Before that batch arrived, one nonterminating
`SIGUSR1` diagnostic was requested on the owned process to distinguish a silent
run from a compilation delay. The stack addresses were Julia JIT code, not
identified LLVM frames; they did not identify the precise activity. The process
was neither terminated nor restarted. Its eventual elapsed time is correctness
validation evidence, not a clean performance benchmark.


## Final audit

`reproduce/audit.py RAW_DIRECTORY` verifies all six sequential validation jobs,
source stability, all 100 unique external combinations against their input
hashes and reference objectives, the degen3 regression, and the full runtime
certificate. It exports the completed reports, compact logs, raw-log hashes,
and exact command/resource provenance to `results/validation.json`.

The tested production aggregate (sorted `Project.toml` and `src/**/*.jl`, each
relative path followed by NUL and file bytes) is
`a98e79913b6f34ad471367181f47b2635cdc9007f63933ba228654382d632cfa`.
The capture reports name baseline HEAD `c7d35cb` because the production repair
was still uncommitted while testing; the aggregate and individual source hashes
identify the repaired files. The focused and broad normal-compilation attempts,
including the incomplete LLVM attempt, remain in the raw directory; only the
completed suites are claimed as passing.

Independent static review found no blocker in the production change and
portable tests. Its two suggestions (nonzero original objective and explicit
checked-policy coverage) were implemented before the final verification.
This repair does not close the outstanding pilotnov sensitive-basis failure or
long-chain FT/SS accuracy cases.
