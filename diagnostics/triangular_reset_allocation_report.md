# Reuse triangular upper storage during refactorization

This change addresses the largest avoidable allocation site left in the
[iteration kernel report](iteration_kernel_optimization_report.md): rebuilding
the identity upper matrix in Forrest–Tomlin, Suhl–Suhl and Bartels–Golub.

`refactorize!` now calls `_reset_identity_upper!` to reuse the outer vector and
its owned index/value vectors. Existing columns are resized to one entry and
assigned their identity row and `one(T)`. New dimensions allocate only missing
columns. Shrinking, growing and empty bases remain supported. Constructors still
create independent storage, and copied factorizations retain independent arrays.

The new backend is constructed before the reset, preserving the old factor when
backend construction fails. Backend selection, numerical LU construction,
permutations, update clearing and row scratch reset are unchanged. BigFloat
identity values are recreated at the current ambient precision; existing scalar
objects in saved factor copies are not mutated.

## Iteration audit

Measurements use the same Julia 1.13.0, aarch64-linux-gnu, one-thread configuration
as the preceding report: Float64/native, presolve disabled, scaling off, two
warmups, three samples and deterministic state replay outside measurement.
All 504 measured rows have zero compilation time. Snapshot metadata, preparation
status, next-iteration status and completed-step counts agree with the baseline.

On all 36 triangular-method snapshots of adlittle, refactorization saves exactly
**226 allocations**: four allocations per column for 56 columns, plus two for the
outer vector. The 12 PFI controls and all other kernel allocation counts are
unchanged. These early next-iteration probes do not themselves refactorize; the
whole-solve measurements below establish the effect when refactorization occurs.

After five steps with steepest-edge pricing:

| Method | Algorithm | Refactorization allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| pfi | dual | 89 → 89 | 39,280 → 39,280 |
| pfi | primal | 87 → 87 | 72,712 → 72,728 |
| forrest_tomlin | dual | 315 → 89 | 47,312 → 39,104 |
| forrest_tomlin | primal | 313 → 87 | 80,920 → 72,712 |
| suhl_suhl | dual | 315 → 89 | 47,312 → 39,104 |
| suhl_suhl | primal | 313 → 87 | 80,920 → 72,728 |
| bartels_golub | dual | 315 → 89 | 47,312 → 39,120 |
| bartels_golub | primal | 313 → 87 | 80,952 → 72,712 |

The triangular refactorization count drops by **71.7–72.2%**, to the native PFI
backend level. Focused repeated-reset probes also match PFI exactly with
Markowitz: 829 allocations each on the tested 64-row basis (native: 81 each).
The native LU and assembled basis storage still allocate; this change does not
reuse symbolic/numeric LU factors or change their failure semantics.

## Complete solves

A separate probe compares the current implementation with the exact old
`refactorize!` method, loaded only in the baseline Julia process. It covers afiro
and adlittle, all four basis methods, both algorithms, and refactorization
intervals 20 (default) and 1 (frequent-refactorization stress case). Presolve and
scaling are off. Each case is warmed twice and measured three times. The probe
also records final status, objective, iterations and refactorizations.

All **32 before/after pairs** reach OPTIMAL with identical objectives and iteration
and refactorization counts, and zero measured compilation time. All 24 triangular
cases improve; the eight PFI controls retain exactly the same allocation counts.
With the default interval, each afiro solve saves 110 allocations and each
adlittle solve saves 1,130 allocations.

Default-interval complete solves on adlittle:

| Method | Algorithm | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| pfi | dual | 1,206 → 1,206 | 541,888 → 541,824 |
| pfi | primal | 1,244 → 1,244 | 583,448 → 583,320 |
| forrest_tomlin | dual | 3,266 → 2,136 | 641,824 → 601,056 |
| forrest_tomlin | primal | 3,272 → 2,142 | 702,536 → 661,400 |
| suhl_suhl | dual | 3,242 → 2,112 | 642,256 → 601,504 |
| suhl_suhl | primal | 3,258 → 2,128 | 703,752 → 662,600 |
| bartels_golub | dual | 3,399 → 2,269 | 639,888 → 598,944 |
| bartels_golub | primal | 3,329 → 2,199 | 702,888 → 661,752 |

For the frequent-refactorization adlittle primal case, Forrest–Tomlin and
Suhl–Suhl drop from 27,445 to 8,687 allocations, and Bartels–Golub from 27,619 to
8,861: 18,758 allocations saved over 83 refactorizations. The configured interval
is an initial interval; dual adaptation can make actual refactorization counts
differ from the number of iterations. No runtime speedup is claimed because
measurement overlapped other validation. Small cross-process byte variations in
unchanged library paths, including PFI controls, are not claimed as savings.

## Storage tradeoff and scope

Resetting in place retains the vectors' backing capacity. A previously dense
upper factor can therefore retain O(n²) index/element-slot storage after the
logical matrix has become identity. This avoids repeated allocation and can
serve later updates, but it is not a claim of lower retained or peak memory.
Removed reference-valued entries remain collectible; the backing slots persist.

A shallow alias to the internal `factor.upper` now observes its reset. The
supported `copy_basis_factorization` path owns separate arrays and remains
isolated. New tests check that refactorization and subsequent pivots leave the
saved factor's FTRAN/BTRAN results unchanged. This change does not pool eta
updates, change primal pricing initialization, or reuse native LU storage.

## Validation and reproduction

The initial regression run passed 771 assertions and failed three allocation
checks as intended: each native triangular refactorization used 339 allocations
against a backend budget of 83. The expanded suite passes **1,560 assertions**
across both backends, all three triangular methods, Float32/Float64/BigFloat,
fixed/arbitrary-width rational types, dimension changes, saved copies, subsequent
updates, singular failures and BigFloat precision changes. It is registered in
`test/runtests.jl`. Independent review found no blocking correctness issue and
confirmed the retained-capacity tradeoff.

The complete production suite passes **196,552 assertions** in one run
(7m44.6s), including all MOI tests with the corrected project import path.
The checked-in solve probe was executed separately and reproduced the baseline's
32 statuses, objectives, iteration/refactorization counts and allocation counts.
All 504 audit rows were checked against the claimed deltas. `git diff --check`
passes.

Run from the repository root:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'push!(LOAD_PATH, pwd()); include("test/runtests.jl")'
julia --startup-file=no --compiled-modules=existing --project=dev dev/iteration_allocations.jl adlittle --basis-update=all --pricing=all --samples=3 --profile --output=diagnostics/iteration-kernels-triangular-reset.toml
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/triangular_reset_solve_probe.jl before diagnostics/triangular-reset-solves-before.toml
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/triangular_reset_solve_probe.jl after diagnostics/triangular-reset-solves-after.toml
```

The baseline probe substitutes the prior allocating identity assignment into the
current refactorization method in that process only. Its resulting method was
checked against the saved pre-change source; repository files are not rewritten.

Raw data: [iteration baseline](iteration-kernels-optimized-backends.toml),
[iteration after](iteration-kernels-triangular-reset.toml),
[complete solves before](triangular-reset-solves-before.toml),
[complete solves after](triangular-reset-solves-after.toml).
