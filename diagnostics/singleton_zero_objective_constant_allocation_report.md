# Zero objective constants in singleton aggregation

Round 146 changes only the objective constant addition in
`aggregate_singleton_equalities` in `src/presolve_aggregation.jl`. When the
current exact constant is zero, the already computed objective-ratio/RHS
product becomes the new constant directly. Otherwise general addition remains.
The zero-ratio/RHS and signed-unit product shortcuts are preserved, and the
result still passes through `_represent_exact`.

The test uses the current committed constant, including cancellation after
previous eliminations. It does not infer zero from the original input or round
a tiny nonzero constant. Projection, candidate ordering, the singleton Float32/64
objective-rounding policy, staged updates, rollback, and primal/basis restoration
are unchanged. Arithmetic uses public nonmutating operations.

When a signed-unit shortcut reuses a Rational{BigInt} operand, direct product
reuse may also share numerator or denominator components with an input value.
This follows the model's existing shallow scalar ownership and earlier reuse
paths. Ordinary rational arithmetic and replacing output array elements preserve
the source; mutation through internal GMP APIs is not a deep-ownership contract.

## Method and results

The baseline includes the preceding 145 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 singleton columns and one shared retained column, with
equalities `2*x_i+y=rhs`, bounds `[1,3]` on every x_i, and free y. The first
objective ratio is 3, -3, 1, or -1, and subsequent ratios alternate signs.
The objective price on each x_i is twice its ratio; the price on y is two.
The target RHS is four and the initial constant is zero (negative zero for
negative first ratios). All 128 eliminations succeed. The constant alternates
between zero and the first contribution, so 64 updates use the new shortcut.
After the even number of eliminations, the projected bounds are `[-2,2]`, the
retained cost is two, and the constant is canonical zero. Measurement includes
projection, staging, objective updates and reconstruction.

The nonzero-constant control starts at seven with alternating ratios 3 and -3,
so the constant alternates between seven and nineteen and never takes the new
branch. The zero-RHS control retains the preceding zero-shift shortcut. Both
controls accept all pivots.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| First ratio 3 | 1,025,640 | 1,002,632 | 2.24% | 26,938 → 26,362 |
| First ratio -3 | 1,026,376 | 1,003,656 | 2.21% | 26,938 → 26,362 |
| First ratio 1 | 986,552 | 963,992 | 2.29% | 25,914 → 25,338 |
| First ratio -1 | 986,440 | 963,752 | 2.30% | 25,914 → 25,338 |
| Nonzero-constant control | 1,031,080 | 1,030,328 | — | 27,136 → 27,136 |
| Zero-RHS control | 879,896 | 879,016 | — | 22,778 → 22,778 |

Allocated bytes decrease by **2.21–2.30%** across the four targets.
Both controls retain their allocation counts. Cross-process byte differences
on unchanged paths alone establish no benefit.

- `positive` saves **576 allocations per call**, or 9 per zero-constant update.
- `negative` saves **576 allocations per call**, or 9 per zero-constant update.
- `unit_positive` saves **576 allocations per call**, or 9 per zero-constant update.
- `unit_negative` saves **576 allocations per call**, or 9 per zero-constant update.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 834 | 44,672 → 44,336 |
| afiro | sparse | 4,891 → 4,891 | 214,992 → 214,016 |
| afiro | propagation | 2,437 → 2,437 | 93,016 → 92,648 |
| afiro | presolve | 16,217 → 16,208 | 730,552 → 728,376 |
| afiro | dual | 17,032 → 17,023 | 865,672 → 863,208 |
| afiro | primal | 16,938 → 16,929 | 843,784 → 842,584 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,747 → 2,747 | 174,776 → 174,632 |
| adlittle | propagation | 18,182 → 18,182 | 643,240 → 642,136 |
| adlittle | presolve | 82,433 → 82,433 | 3,329,400 → 3,327,752 |
| adlittle | dual | 84,448 → 84,448 | 4,119,480 → 4,117,256 |
| adlittle | primal | 85,246 → 85,246 | 4,395,928 → 4,394,456 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,368 → 461,112 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,712 → 607,536 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,015 → 2,015 | 110,272 → 109,776 |
| kb2 | sparse | 2,836 → 2,836 | 163,168 → 162,336 |
| kb2 | propagation | 12,948 → 12,948 | 456,720 → 455,520 |
| kb2 | presolve | 229,149 → 229,149 | 10,641,632 → 10,640,096 |
| kb2 | dual | 230,351 → 230,351 | 11,093,760 → 11,092,192 |
| kb2 | primal | 230,518 → 230,518 | 11,108,416 → 11,106,272 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,320 → 877,792 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,848 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 301,456 → 300,576 |
| sc50a | propagation | 6,020 → 6,020 | 224,512 → 223,632 |
| sc50a | presolve | 67,457 → 67,457 | 2,848,632 → 2,846,488 |
| sc50a | dual | 68,529 → 68,529 | 3,193,832 → 3,192,424 |
| sc50a | primal | 68,474 → 68,474 | 3,146,648 → 3,144,824 |
| sc50a | dual_no_presolve | 961 → 961 | 306,176 → 306,112 |
| sc50a | primal_no_presolve | 964 → 964 | 232,232 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 211,544 → 211,240 |
| flugpl | propagation | 3,253 → 3,253 | 124,096 → 123,504 |
| flugpl | presolve | 30,791 → 30,791 | 1,172,528 → 1,171,008 |
| flugpl | dual | 31,462 → 31,462 | 1,281,384 → 1,280,808 |
| flugpl | primal | 31,811 → 31,811 | 1,325,992 → 1,325,384 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

The standalone singleton pass, full presolve, and both solves with presolve
each save **nine allocations on afiro**. The other 46 reference measurements
retain their allocation counts, including both solves without presolve.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`singleton-zero-objective-constant-allocations-before.toml`](singleton-zero-objective-constant-allocations-before.toml)
and [`singleton-zero-objective-constant-allocations-after.toml`](singleton-zero-objective-constant-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=singleton-zero-objective-constant-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function singleton_zero_objective_constant_probe(kind; count=128, T=Float64)
    ratio=kind==:unit_positive ? 1 : kind==:unit_negative ? -1 : kind==:negative ? -3 : 3
    rhs=kind==:zero_rhs ? zero(T) : T(4)
    initial=kind==:nonzero_constant ? T(7) : ratio<0 ? -zero(T) : zero(T)
    prices=T[isodd(i) ? 2ratio : -2ratio for i in 1:count]
    A=hcat(sparse(1:count,1:count,fill(T(2),count),count,count),sparse(ones(T,count,1)))
    problem=LinearProblem(A,[prices;T(2)];objective_constant=initial,
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=[ones(T,count);nothing],column_upper=[fill(T(3),count);nothing])
    return problem,JSimplex.aggregate_singleton_equalities
end

for kind in (:positive,:negative,:unit_positive,:unit_negative,:nonzero_constant,:zero_rhs)
    problem, pass = singleton_zero_objective_constant_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **3,570 assertions** and failed only
the four target allocation guards: 26,983 and 26,946 against 26,638, and two
cases of 25,922 against 25,614. Both control budgets passed. There are
**3,574 new assertions**; existing budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; signed zero
constants; signed unit/nonunit ratios and RHS values; free and finite pivot
bounds; committed constants returning to zero or leaving zero; odd/even numbers
of eliminations; projected matrix/bounds/objective; restored primal and basis;
objective equivalence; and source preservation under output-array mutation.

BigFloat tests use stored 256-bit inputs at ambient precision 32/64/256. Direct
products `±(3+2^-200)` reject at lower precision, while exactly representable
values three and `2^-200` succeed. Float32/64 checks retain rejection for overflow,
half-subnormal products, and tiny nonzero initial constants whose addition is
not exactly representable. The retained column has degree two to prevent an
unrelated alternate singleton candidate. Large rational cases cover both factor
positions and signs, with denominators 5, 7, 15, and 21.

The targeted presolve/allocation suite passed **87,004 / 87,004 assertions**
in 1m58.8s, including every new allocation guard.

Independent read-only review found no issues. An AST-renamed baseline passed
**2,574 assertions across 160 differential models**, plus four assertions in
two alias probes (**2,578 assertions total**).
Coverage included all numeric types and ambient BigFloat precisions, signed
zero/tiny nonzero constants, unit/nonunit factors, zero re-entry after accepted
eliminations, late rejection and rollback, exact-candidate preference and
floating objective rounding, projected/free/fixed bounds, primal/basis
restoration, and source preservation. Alias probes confirmed that direct
rational products can newly share RHS or ratio components, while ordinary
arithmetic remains nonmutating.

The full test suite passed **106,501 / 106,501 assertions** in **6m04.1s**.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
