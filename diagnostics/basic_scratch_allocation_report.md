# Reuse staged row changes in basic presolve

Round 31 reuses the temporary row-bound change vector in `_presolve_basic`.
The vector is allocated lazily when the first selected column reaches staging,
then emptied before every later staging attempt. This includes empty columns and
attempts following a rejected candidate. Earlier skips cannot commit stale
entries because they never reach the commit loop.

Selection, exact arithmetic, representability checks, commit order, and postsolve
values/states remain unchanged. The buffer is local to the pass; results retain
bound values, not the scratch container. Its capacity remains available until the
pass ends and is bounded by the largest staged column.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times with setup
outside measurement and garbage collection before each sample. Tables report
minimum allocated bytes. All 32 measurements per run recorded zero compilation
time. The baseline includes the preceding 30 rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped validation; no runtime-speedup claim is made. Values are allocated
bytes per call, not peak or retained memory.

Both probes have 256 variables fixed to zero and one retained variable `y` with
bounds `[0,2]`; all objective coefficients are one. The fixed-column probe has
256 rows `0 ≤ xᵢ + y ≤ 1`. The empty-column probe has only `0 ≤ y ≤ 1`, so the
fixed columns have no matrix entries.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Fixed columns with row entries | 512,712 | 466,568 | 9.00% | 12,617 → 12,107 |
| Empty columns | 268,008 | 258,984 | 3.37% | 7,481 → 7,226 |

The fixed-column probe avoids 255 replacement vectors and their backing storage;
the empty-column probe avoids 255 replacement empty vectors.

All five reference fixtures retain identical bytes and allocation counts in the
standalone basic pass. Full presolve and both whole-solve algorithms also retain
identical allocation counts. These fixtures therefore do not establish a
whole-solver allocation benefit from buffer reuse. Small byte differences are
not attributed to the change: full presolve ranges from -2,336 to +288 bytes,
while unchanged whole-solve paths without presolve vary from -320 to +16 bytes.
The measured benefit is in passes with repeated staging, as exercised above.

All ten model snapshots (five fixtures × basic/full presolve) matched exactly:
CSC arrays, objective and constant, sense, bounds, domains, names, and original
column count. All 20 whole-solve combinations remained `OPTIMAL`, with identical
status, objective, complete primal vector, and iteration count (`isequal`).

Machine-readable results:
[`basic-scratch-allocations-before.toml`](basic-scratch-allocations-before.toml)
and [`basic-scratch-allocations-after.toml`](basic-scratch-allocations-after.toml).

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=basic-scratch-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for kind in (:fixed, :empty)
    count = 256
    A = kind == :fixed ?
        hcat(sparse(1:count, 1:count, ones(count), count, count), sparse(ones(count, 1))) :
        sparse([1], [count + 1], [1.0], 1, count + 1)
    rows = size(A, 1)
    problem = LinearProblem(A, ones(count + 1);
        row_lower=zeros(rows), row_upper=ones(rows),
        column_lower=zeros(count + 1), column_upper=[zeros(count); 2.0])
    println(measure_allocations(_ -> JSimplex._presolve_basic(problem); samples=3))
end
```

## Regression coverage

Both final budgets failed against the original basic-pass body: 504,600 bytes
against a 490,000-byte fixed-column limit, and 7,526 allocations against a 7,350
empty-column limit. Both now pass. The empty-column test uses an allocation count
to distinguish the removed vectors from byte variability in exact arithmetic.
Direct-call test measurements differ from the warmed benchmark context above.

The 74 new assertions cover both budgets, cumulative shifts with varying staging
lengths, and a partially staged rejection followed by an empty column, both with
and without an earlier accepted elimination. Checks include objective constants,
row bounds, retained columns, postsolve values, and deep-copied input preservation.
Successful cases cover Float32, Float64, BigFloat, and Rational{BigInt}; deliberately
inexact rejection cases use Float32 and Float64. Together with the existing lazy
row-bound and exact elimination-value tests, all 274 targeted assertions pass.

Independent review found no issue. Its 432 differential cases across six numeric
types, including explicit selections and 13 failures, matched baseline fields,
CSC storage, postsolve values, and unchanged inputs. A no-eligible-candidate
probe retained its 4,080-byte allocation total. It independently passed all 74
new assertions.

The complete mandatory suite passed **17,570/17,570** tests, including the 74 new
checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
