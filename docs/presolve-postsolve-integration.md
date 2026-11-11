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
Certified inequality activation also supports BigFloat minimization with positive
primal tolerance and nearest MPFR rounding. Checked objective-coefficient rounding
remains limited to Float32/Float64. Unsupported conditions retain the existing paths;
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


## Selected follow-up integration (2026-11-11)

The follow-up integrates families with demonstrated Float64 time, memory or
correctness benefits, including their verified BigFloat counterparts:

- Invocation-local exact conversion and rejected-equality caches, with owned
  BigFloat keys/snapshots and invalidation for all consulted dependencies.
- A shared read-only row index and transfer of attested fresh model arrays,
  retaining original model validation and binary-bound clamping.
- Checked Int128 rational arithmetic for native propagation, falling back to
  BigInt without overflow exceptions. BigFloat and other supported arithmetic
  retain the original exact kernel and endpoint guards.
- Compact identity/constant row maps and checked ordinary-vector restoration.
- At most three productive rounds of certified inequality activation under one
  cumulative inference, sparse-aggregation and dependent-row budget.
- Bounded recovery that does not replenish retries after numerical failures,
  and residual projection preserving the complete original tolerance band.

The Float64 residual regression uses activity 1e10 with a 1.5e-7 residual:
original reconstruction cannot repair it, while residual-unit projection does
so under the unchanged certificate and tolerance. The corresponding private
BigFloat joint-projection method is included and tested, without enabling new
automatic driver routes or bypassing existing eligibility gates. Hardware FTZ
still gates native inequality activation; it does not gate MPFR BigFloat.

Parallel-structure/activity/delta caches, throwing small arithmetic, equality
row sparsification, actual-fill, cheap-first and new objective-constant rounding
are excluded. No solver tolerance, coefficient-dropping rule or precision policy
has been relaxed.

### Fresh integrated Float64 presolve measurements

Reference presolve source is production commit `1be2b042`; candidate is the
integrated source, including the task-local lookup per exact conversion.
Each measurement used a fresh process, one Julia/BLAS thread, Float64 LP
relaxation, tolerance 1e-7 and the same original work caps. Input reading and a
small synthetic presolve warmup were outside the timer. Complete presolve,
cache setup/release, history construction, GC and remaining compilation were
inside. Pair 2 reversed both model and arm order. These are **presolve-only**
measurements; largo was never passed to the simplex solver.

| Model | Reference 1 / 2 (s) | Integration 1 / 2 (s) | Change 1 / 2 | Ratio of means |
|---|---:|---:|---:|---:|
| runtime | 11.338 / 11.927 | 11.256 / 11.388 | -0.72% / -4.52% | -2.67% |
| largo | 167.982 / 169.849 | 75.194 / 75.121 | -55.24% / -55.77% | -55.51% |

Each arm reproduced its own full model/history fingerprint. Candidate results
and the complete postsolve/proof history matched an independent run of the
original BigInt propagation kernel exactly on both inputs. Inputs were unchanged
and both task-local contexts were released. Additional activation changes the
reduced model: runtime goes from reference 25,527 x 28,799 / 197,264 nonzeros to
22,351 x 25,623 / 181,975; largo from 998,746 x 841,233 / 3,818,583 to
998,744 x 841,231 / 3,818,579. These reductions are not simplex-kernel speedups.

| Model | Allocated GB, reference → integration | Allocations, reference → integration | GC 1 / 2, reference → integration (s) |
|---|---:|---:|---:|
| runtime | 11.491 → 7.212 | 299,839,303 → 167,251,608 / 167,251,605 | 3.432 / 3.584 → 2.202 / 2.189 |
| largo | 134.314 → 52.998 | 3,098,393,314 → 750,495,033 / 750,495,035 | 48.109 / 48.227 → 17.238 / 17.850 |

Allocated bytes decrease 37.23% and 60.54%, allocation counts 44.22% and 75.78%.
Included compilation was reference 0.133/0.136 versus candidate 0.270/0.279 s
on runtime and 0.136/0.143 versus 0.280/0.298 s on largo; none was subtracted.
Peak RSS, including input loading/warmup/compilation, was reference
1.983/1.920 versus candidate 1.376/1.334 GB on runtime, and 8.425/7.926 versus
5.156/5.401 GB on largo. RSS is not retained presolve memory.

The reachable result-plus-history graph **increases** from 143.072 to 147.008 MB
on runtime (+2.75%) and 2,074.253 to 2,104.499 MB on largo (+1.46%). Compact maps
save storage within individual steps, while further reductions add history
steps (52→68 and 43→58); combined retained history does not shrink. Graph-size
walks occurred after timing and RSS capture. Units above are decimal GB/MB.

Small 32-by-64 sparse/dense fixtures also matched reference output exactly.
Seven warm batches of ten presolves had median times 6.460→3.702 ms (160
nonzeros) and 202.946→104.422 ms (2,048 nonzeros). Median allocated bytes fell
13,294,416→7,481,088 and 259,237,584→196,876,192; allocation counts
364,648→180,079 and 7,133,828→5,129,809. Compilation was zero in these batches.
These are synthetic operation checks, not whole-solver benchmarks. Two full
presolve repetitions on one ARM64 machine do not establish universal speedups,
and the small runtime timing difference remains weak evidence.

### Validation and cost review

The final production tree passed 8,052 targeted assertions. The matching owned
candidate also passed 6,661 assertions in 23 existing model, presolve, postsolve
and primal-recovery files. Coverage includes Float32/Float64, BigFloat at
32–512 bits and mixed stored/working precision, unsupported-arithmetic fallbacks,
cache ownership/invalidation, spare CSC buffers, nested/task isolation,
cancellation/exception cleanup, shared-budget exhaustion, map/scatter semantics,
original certificates and all production basis managers. The FTZ integration
regression demonstrated three clean failures before the separate BigFloat gate
was restored, then passed. This is not a complete repository test-suite run.

Independent component and whole-branch reviews found no remaining important
correctness issue or newly unnecessary full-vector scan, basis solve, copy or
retained workspace/factor graph. Explicit costs remain:

- Setup/presolve: a task-local dictionary lookup per exact conversion; row-cache
  hits compare CSC buffers and dependencies in O(nnz+n+m). Rebuilds own one last
  CSC snapshot and row index. Exact/rejection caches hold at most 100,000 entries
  each; the BigFloat 64 MiB estimate limits exact keys/rationals, not the entire
  session. There is no cross-solve cache retention.
- Each propagation candidate: checked integer operations and occasional BigInt
  fallback. The measured small-arithmetic implementation retains an additional
  rational normalization gcd after cross-cancellation.
- Repeated presolve: extra scans, verification and history under unchanged
  cumulative work caps. The caps do not bound every independent verification
  or copying operation.
- Recovery only: residual-projection arrays/scans and exact arithmetic, with
  eight sweeps and degree-plus-one redistribution retained. BigFloat exact
  arithmetic storage can grow with exponent magnitude. Final certification and
  rollback remain authoritative.

No ordinary simplex iteration or refactorization gains a new scan, basis solve,
or cache-maintenance operation from these presolve changes.


### Final-tree whole runtime verification (2026-11-11)

One complete Float64 dual/Devex/legacy Huangfu–Hall/native160 solve on the
final production tree finished OPTIMAL, objective 51,425,691.762043536,
37,373 iterations and 241 refactorizations. Independent original-primal
feasibility passed, input bytes were unchanged, and both presolve contexts
were released. All original solver certificates remained active.

This was a correctness run, not a paired speed comparison: wall time
105.865 s included 34.405 s compilation, 4.305 s GC, 19.912 GB cumulative
allocation / 279,303,647 allocations. The solver-reported elapsed time was
74.997 s; no compilation time was subtracted to create a benchmark result.
Largo was not solved. The first verification launcher failed on a missing
SparseArrays import before reading input or invoking solve; it was archived,
the launcher import was fixed, and only then was this single full solve run.
