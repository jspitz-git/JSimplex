# Shared fixed-endpoint sums in implied-bound checks

Round 162 changes only maximum-activity accumulation in
`_equality_implies_column_bounds` in `src/presolve_aggregation.jl`. Before each
minimum update, a Boolean records whether both activity values are identical
(`===`). After the minimum update, the maximum may reuse its result when the
previous sums were identical and the current product came from the existing
fixed-endpoint cache. These conditions prove that both additions have the same
operands. The maximum's zero-sum shortcut still runs first.

Only the Boolean is retained; no extra previous rational value is materialized.
The existing per-term product cache still requires equal finite nonzero endpoints
and a finite maximum activity. Divergent sums or separately computed products
retain their previous addition path. Unbounded/zero guards, signed products,
exact arithmetic, final comparisons, projection, row-removal decisions,
representation gates, staged updates, rollback and postsolve are unchanged.
Shared exact values are never mutated.

## Method and results

The baseline includes the preceding 161 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent two-row, three-column blocks:
`2*x+a*y+b*z=4` and `6*x+5*y+7*z<=100`. The cost of x is zero, the costs of y/z
are two/three, and the objective constant is seven. Both retained variables
are fixed to one in the targets. All 128 pivots are accepted and all equality
rows are removed. The second row's retained coefficients become `5-3*a` and
`7-3*b`, and its upper bound becomes 88. Measurement includes the full sparse
aggregation pass, with input construction outside measurement.

Integer targets use a/b equal to 3/5 or -3/-5; fraction targets use 1/2 and 3/2,
or their negatives. The eliminated x has bounds `[-8,8]`. The first fixed term
establishes a shared exact activity through the existing zero-sum/product
shortcuts. The second term now reuses the updated minimum for the maximum.
Each target has 128 reused maximum sums; fractional sums reduce ±4/2 to ±2.

The variable-prefix control uses a=3 and b=5, y in `[1,2]` and z fixed to one.
The first term makes the activity extremes different, so the second term's
shared product cannot permit a shared sum. The free-pivot control uses a=3,
b=5, y/z fixed to one and free x; the helper returns early. Both controls accept
all pivots and remove the equality rows.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| integer_positive | 2,432,800 | 2,399,744 | 1.36% | 63,315 → 62,291 |
| integer_negative | 2,435,904 | 2,402,560 | 1.37% | 63,315 → 62,291 |
| fraction_positive | 2,463,024 | 2,429,632 | 1.36% | 63,827 → 62,803 |
| fraction_negative | 2,462,912 | 2,429,760 | 1.35% | 63,827 → 62,803 |
| variable | 2,539,792 | 2,540,112 | — | 66,643 → 66,643 |
| free_pivot | 1,846,064 | 1,846,528 | — | 44,115 → 44,115 |

Target allocated bytes decrease by **1.35–1.37%**.
Both controls retain allocation counts. Cross-process byte differences on
unchanged paths alone establish no benefit.

- `integer_positive` saves **1,024 allocations per call**, or 8 per reused maximum sum.
- `integer_negative` saves **1,024 allocations per call**, or 8 per reused maximum sum.
- `fraction_positive` saves **1,024 allocations per call**, or 8 per reused maximum sum.
- `fraction_negative` saves **1,024 allocations per call**, or 8 per reused maximum sum.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 40,928 → 41,088 |
| afiro | sparse | 4,167 → 4,155 | 186,776 → 185,928 |
| afiro | propagation | 2,437 → 2,437 | 92,536 → 92,696 |
| afiro | presolve | 15,653 → 15,641 | 706,120 → 705,848 |
| afiro | dual | 16,468 → 16,456 | 841,736 → 841,960 |
| afiro | primal | 16,374 → 16,362 | 820,088 → 820,472 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,339 → 2,336 | 156,744 → 156,680 |
| adlittle | propagation | 18,182 → 18,182 | 641,576 → 641,496 |
| adlittle | presolve | 81,426 → 81,416 | 3,289,552 → 3,288,672 |
| adlittle | dual | 83,441 → 83,431 | 4,079,648 → 4,077,792 |
| adlittle | primal | 84,239 → 84,229 | 4,356,592 → 4,354,720 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,224 → 461,176 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,504 → 607,392 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,416 → 105,352 |
| kb2 | sparse | 2,259 → 2,257 | 137,304 → 137,192 |
| kb2 | propagation | 12,948 → 12,948 | 454,368 → 454,464 |
| kb2 | presolve | 227,907 → 227,905 | 10,589,696 → 10,589,328 |
| kb2 | dual | 229,109 → 229,107 | 11,044,288 → 11,043,232 |
| kb2 | primal | 229,276 → 229,274 | 11,057,504 → 11,057,280 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,240 → 878,048 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,816 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,174 → 6,164 | 282,400 → 282,016 |
| sc50a | propagation | 6,020 → 6,020 | 222,112 → 222,272 |
| sc50a | presolve | 66,302 → 66,275 | 2,802,200 → 2,801,208 |
| sc50a | dual | 67,374 → 67,347 | 3,148,408 → 3,146,696 |
| sc50a | primal | 67,319 → 67,292 | 3,101,384 → 3,099,368 |
| sc50a | dual_no_presolve | 961 → 961 | 306,144 → 306,112 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 4,667 → 4,667 | 173,480 → 173,480 |
| flugpl | propagation | 3,253 → 3,253 | 123,216 → 123,552 |
| flugpl | presolve | 27,926 → 27,926 | 1,057,640 → 1,058,536 |
| flugpl | dual | 28,597 → 28,597 | 1,167,952 → 1,168,096 |
| flugpl | primal | 28,946 → 28,946 | 1,212,176 → 1,212,736 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each solve with presolve save 12 allocations on afiro,
10 on adlittle, two on kb2 and 27 on sc50a. Standalone sparse aggregation saves
12 on afiro, three on adlittle, two on kb2 and ten on sc50a. The remaining
34 reference measurements retain their allocation counts.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-implied-shared-fixed-sums-allocations-before.toml`](aggregation-implied-shared-fixed-sums-allocations-before.toml)
and [`aggregation-implied-shared-fixed-sums-allocations-after.toml`](aggregation-implied-shared-fixed-sums-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-implied-shared-fixed-sums-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_implied_shared_fixed_sums_probe(kind; count=128, T=Float64)
    fractional=kind in (:fraction_positive,:fraction_negative)
    direction=kind in (:integer_negative,:fraction_negative) ? -one(T) : one(T)
    a=direction*(fractional ? T(1)/2 : T(3))
    b=direction*(fractional ? T(3)/2 : T(5))
    xlo=kind==:free_pivot ? nothing : T(-8)
    xhi=kind==:free_pivot ? nothing : T(8)
    rows=collect(1:2:2count);other=rows.+1;cols=collect(1:3:3count)
    A=sparse(vcat(rows,rows,rows,other,other,other),vcat(cols,cols.+1,cols.+2,cols,cols.+1,cols.+2),
        vcat(fill(T(2),count),fill(a,count),fill(b,count),fill(T(6),count),fill(T(5),count),fill(T(7),count)),2count,3count)
    problem=LinearProblem(A,repeat(T[0,2,3],count);objective_constant=T(7),
        row_lower=[isodd(i) ? T(4) : nothing for i in 1:2count],
        row_upper=[isodd(i) ? T(4) : T(100) for i in 1:2count],
        column_lower=[i%3==1 ? xlo : one(T) for i in 1:3count],
        column_upper=[i%3==1 ? xhi : kind==:variable && i%3==2 ? T(2) : one(T) for i in 1:3count])
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:integer_positive,:integer_negative,:fraction_positive,:fraction_negative,:variable,:free_pivot)
    problem, pass = aggregation_implied_shared_fixed_sums_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **3,038 assertions** and failed only
the four target allocation guards. Both controls passed. There are **3,042 new
assertions**; existing allocation budgets were not relaxed.

An independent endpoint oracle covers 1,200 helper models across Float32,
Float64, BigFloat and Rational{BigInt}, signed pivots/RHS, fixed/variable terms,
shared/different denominators, cancellation and finite/free/one-sided bounds.
The ±1000 witnesses suffice for these small bounded-size fixtures. BigFloat
cases store terms ±(3+2^-200) and ±(5-2^-200) at 256 bits and run at ambient
32/64/256. Their low bits cancel, while a further ±2^-200 residual changes the
bound decision. Large rational sums reduce 300-bit numerators over odd
denominators 5, 7, 15 and 21.

Additional cases place a fixed prefix before a variable term with signed
coefficients and pivots. Tight bounds independently exclude either endpoint;
sharing the previous sums alone must not permit sharing different products.
The allocation control covers the opposite order: a variable prefix before
a fixed term must not permit sharing the different previous sums.

Full aggregation checks cover matrix/bounds/objective, projected/removed rows,
primal/basis restoration, objective equivalence and source preservation after
ordinary output mutation.

The targeted presolve/allocation suite passed **135,890 / 135,890 assertions**
in **2m29.3s**, including every new allocation guard.

Independent read-only review found no issues. AST-renamed baseline helper and
sparse aggregation functions passed **5,012 assertions across 148 differential
models**, including 536 helper comparisons against baseline and an independent
exact interval oracle, 444 primal and 592 basis restoration comparisons. There
were 120 accepted and 28 unchanged models, with 104 removed and 16 projected
rows. Coverage included eight rollback cases, all four numeric types, MIN/MAX
senses, both mixed fixed/variable orders, cancellation and reentry, divergent
extrema, zero endpoints, unbounded orientations/orders, stored-256 BigFloat at
ambient 32/64/256, 300-bit non-dyadic rationals and source preservation.

The full test suite passed **155,387 / 155,387 assertions** in **6m44.7s**.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
