# Bounded retained upper-column capacity

This integrates the storage policy from experimental commit
`da7deb6e74ab8d6fbfb55f9d167d46510b0d54be` onto master `7abb8cf`.
The direct-LU and persistent-incidence prototypes, packed-slot optimization,
BG allocation repair, and dual cleanup repair are separate changes and are not
included in this integration.

## Policy

After successful refactorization, FT, SS and BG reset their upper transformation
to identity. Index/value vectors with backing capacity above 256 entries release
that reserve; smaller buffers remain reusable. Active columns can still grow
without a cap. This applies to native and Markowitz backends, both index
representations, and generic scalar types. Copied factors own their storage.

For Float64/Int64, retained index/value payload after reset is at most 4 KiB per
column, excluding container overhead. This is not a limit on active fill or
process memory. The implementation uses the Julia 1.13 vector backing Memory
length to detect excess capacity, including front offsets, and shrinks through
`sizehint!` after resetting the active length to one. Julia 1.13 is the supported
minimum. No coefficients, arithmetic order, precision, pivot choices or
refactorization intervals change.

## Historical measurement evidence

The experimental branch measured ordinary FT on runtime.mps with dual simplex,
legacy strategy, steepest-edge pricing, native refactorization, interval 80 and
integrality relaxation. These are historical measurements, not new timings of
this integration build:

| Policy | Solve times | Whole-process peak RSS |
| --- | --- | --- |
| Unbounded retained capacity | 314.064 / 313.763 s | 6.705 / 6.839 GiB |
| Bounded retained capacity | 255.632 / 256.139 s | 1.912 / 2.024 GiB |

All four solves reached certified OPTIMAL at 61,720 iterations and 792
refactorizations, with zero restarts. Objective, primal-vector bits and all 788
logged progress states matched. Mean measured solve time fell by 18.5%; runs were
not randomized or interleaved. Peak RSS includes a preceding fast0507 solve.
The second old run used O1 flags but loaded the same O2 native images; new runs
used O2. These limitations prevent treating the timing difference as a universal
speedup. Full-run benefit was measured for FT only, not SS or BG.

The original report, replay scripts, fingerprints and raw local outputs remain
in the preserved `codex/basis-update-chain-bench` worktree at
`/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl`, under
`diagnostics/basis-bounded-capacity/` and `.superpowers/upper-capacity/`.
The original report is available with
`git show da7deb6:diagnostics/basis-bounded-capacity/README.md` in that repository.
Reproducing those historical benchmarks requires that experimental checkout and
its retained local environments; the independent integration tests below do not.

## Integration verification

The results below record the capacity-only integration at `a738b41`. The
subsequent [BG allocation repair](../bg-transpose-allocation/README.md) removes
the known failure recorded here; all 13,957 checks in the unchanged allocation
driver now pass. The historical verification record is preserved.

The focused capacity tests cover oversized buffers, front offsets, preservation
of small buffers and copies, dimension changes, subsequent updates, FT/SS/BG,
native/Markowitz, Float32/Float64/BigFloat and two rational types. The standalone
semantic runner omits the experimental packed-slot test because that optimization
is not part of master. It passed 17,148 checks on the integration source using
`--compile=min`.

Run semantics and allocation checks separately, with the package environment
instantiated and only one numerical process at a time:

```bash
OPENBLAS_NUM_THREADS=1 JULIA_NUM_THREADS=1 julia --startup-file=no --compile=min --project=. diagnostics/basis-bounded-capacity/reproduce/regression.jl
OPENBLAS_NUM_THREADS=1 JULIA_NUM_THREADS=1 julia --startup-file=no --project=. diagnostics/basis-bounded-capacity/reproduce/allocations.jl
```

With normal compilation, 13,956 checks passed and one failed. The allocation
driver intentionally retains the pre-existing BG transposed-solve assertion (`test/factorization_tests.jl:262`): 32 bytes are allocated versus an
expected zero. Its separate repair is not included in this integration. Do not
interpret this driver as passing when it reports that failure. A fresh check of
unchanged master `7abb8cf` reproduced the same failure (362 passed, one failed).
No other failures or errors occurred in either targeted run. The read-only
integration review found no actionable issues. Verification fingerprints are
in [verification.json](results/verification.json); raw logs remain locally under
`.superpowers/bounded-capacity-integration/`.

Local verification uses the existing 8-GiB virtual-memory wrapper and the
available-RAM/swap guard, with one Julia/BLAS thread. Local manifests and disabled
precompile-workload preferences are not committed. This report does not claim
that the full project suite passes.
