# Presolve and postsolve integration

The integrated path includes directed bound propagation with its exact-bound
cache, corrected original-row basis hints, restoration of dual values and the
basis through singleton rows, equality elimination and propagation, compact
propagation history with an empty-history fast path, exact dual propagation
and certified inequality activation, checked rounding of objective coefficients,
and an invocation-local cache for unchanged dependent-row reductions.

New objective-constant rounding, actual-fill and cheap-first are excluded.
The original fill estimate, aggregation work limits, solver tolerances and
original-model certification remain in place. Dual/basis restoration applies
to Float32/Float64 and BigFloat minimization with positive primal tolerance.
Inequality activation and checked objective-coefficient rounding remain limited
to Float32/Float64. Unsupported conditions retain the existing paths;
inconclusive basis restoration falls back to ordinary original-model cleanup.

BigFloat directed propagation rounds the exact rational implication outward at
the current working precision, using a single MPFR quotient conversion. Stored
input precision is preserved; the bound cache contains the exact image of the
newly stored endpoint. The conversion uses explicit rounding without changing
the caller's precision or rounding context. Exact-only propagation remains
available and is retained for zero primal tolerance. BigFloat bound-side hints
use the existing interval predicate to avoid rounding away tolerance violations.
Original-model feasibility, optimality and objective checks remain unchanged:
solving higher-precision data at lower precision can still be inconclusive.
The performance figures below describe the earlier Float64 integration, not a
BigFloat speedup.

## BigFloat extension validation

The extension passed 10,750 assertions in 16 focused files on Julia 1.13.0,
including directed endpoints at 32/64/128/256 bits, mixed stored precisions,
singleton/equality/propagation restoration, conservative rejection, and the
existing Float32/Float64 regressions. Only the targeted suite was run. Small
sparse/dense operation checks quantify additional history work and memory; no
BigFloat whole-solver speedup has been established. The regressions are included
in the regular test suite: [directed bounds](../test/presolve_bigfloat_bounds_tests.jl)
and [dual/basis restoration](../test/presolve_bigfloat_postsolve_tests.jl).
The subsequent fast0507 benchmark was cancelled by request before any complete
measurement finished; it provides no whole-solver performance conclusion.

## Earlier Float64 integration validation

The committed source/test bytes were checked against the verified integration:

- 2,841 assertions in 16 focused regression files, including Float32/Float64,
  exact/higher-precision fallbacks, cancellation, rollback, original certificates,
  and postsolve recovery across all five production basis managers.
- Eight additional allocation/coefficient-ownership checks and 61 exact checks
  against the tested inequality-proof prototype, including 1,826 certificates
  found on the common reduced runtime model.
- All 16 standard LP-relaxation solves (eight models, primal and dual) optimal
  and feasible in the original model, with expected objectives.
- Two fresh pairs of whole runtime.mps solves against original production commit
  `3dc0bcda7cc14810f9559cc97131124726f3820a`, in order reference/candidate,
  candidate/reference. The earlier partial working copy containing directed
  bounds and a cleanup regression is **not** this performance reference.

| Pair | Original production (s) | Integration (s) | Change |
|---|---:|---:|---:|
| 1 | 128.756078 | 92.518888 | -28.144% |
| 2 | 128.904040 | 94.960929 | -26.332% |

Ratio of mean times: -27.238%. Total iterations: 54,753 to 43,421;
refactorizations: 350 to 293. All four solves were optimal and original-primal
feasible. Each arm reproduced its own bitwise objective and full primal SHA;
cross-arm objective difference was +2.8312206268310547e-7. The solver's original
certificate remains authoritative; these plain benchmarks did not record each
internal decision or certificate invocation.

Conditions: ARM64, Julia 1.13.0, Float64, production Huangfu–Hall/native160,
dual/Devex/legacy, presolve on, automatic scaling, one Julia/BLAS thread,
primal/dual tolerances 1e-7, zero tolerance 1e-12, unlimited time/iterations.
Full afiro and 100 runtime iterations warmed each process outside the timer.
The timer included setup, presolve, reduced solve, recovery, postsolve and
certification. Candidate compilation inside the timer was 11.688/18.192 ms
(reference zero); it was included, not subtracted.

Memory is a tradeoff: mean allocation count increased 137.89%, cumulative
allocated bytes 14.40% (20.09 to 22.99 GB), and mean peak RSS 30.26%
(2.25–2.37 to 3.00–3.02 GiB). Peak RSS includes warmup and compilation; it is
not retained-history size. Two repetitions of one large model do not establish
a universal speedup, and changed iteration counts are not a kernel speedup.
No complete multi-hour repository test run is claimed.

## Computational work and ownership review

No additional basis solve or full scan was added to an ordinary simplex
iteration. Terminal capture retains the already certified dual vector until
postsolve, without another solve or capture copy. Subsequent unscaling and
restoration allocate vectors sized to the restored models. History owns only
required column slices and proof/event data, rather than a workspace or factor;
it is cleared before retrying the original LP. Empty propagation history avoids
column-sized bitmaps and scans.

The unchanged-result cache holds at most one owned snapshot per base presolve,
restricted to Float32/64 models with at most 256 rows, 10,000 columns and 10,000
stored coefficients. Hits compare dimensions, CSC structure/values and row
bounds exactly; misses clear the key before computing. Synthetic sparse/dense
20-by-40 cases with 20 unchanged calls in two reversed orders confirmed lower
allocations, including the first cache fill. These are cache measurements, not
whole-solver speedups.

Independent exact activation checks and working-model copies intentionally
remain on each restaging attempt. The original search budgets limit their
specified visits/edges/expansion, not all independent verification and copying.
The review found no remaining avoidable workspace/factor retention or repeated
work in the accepted changes; these correctness costs remain explicit.

## Testing another machine or input

The new regressions are included in `test/runtests.jl`. A quick subset from the
repository root is:

```julia
using JSimplex, Test
@testset "Presolve/postsolve integration" begin
    include("test/presolve_costs_cache_tests.jl")
    include("test/presolve_inequality_proof_tests.jl")
    include("test/presolve_postsolve_integration_tests.jl")
end
```

For a comparable solve, start Julia with `JULIA_NUM_THREADS=1` and
`OPENBLAS_NUM_THREADS=1`, activate the repository project, and use:

```julia
using JSimplex
problem = read_mps("your-model.mps")
options = SolverOptions(algorithm=:dual, pricing=:devex,
    basis_update=:huangfu_hall, basis_refactorization=:native,
    refactorization_interval=160, simplex_strategy=:legacy,
    presolve=true, scaling=:auto, primal_tolerance=1e-7,
    dual_tolerance=1e-7, time_limit=Inf, iteration_limit=typemax(Int),
    verbose=false)
solution = solve(problem; options, relax_integrality=true)
@show solution.status solution.objective_value solution.statistics
```

`relax_integrality=true` measures the LP relaxation, not a MIP solve. Use
separate processes, the same warmup and reversed paired order for comparisons
with the original commit; a first call includes compilation and is not a
warmed comparison. Compare status and original-model feasibility as well as
elapsed time. No dependency on local diagnostic snapshots is required.
