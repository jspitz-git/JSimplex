# Huangfu–Hall with Markowitz refactorization

Select `basis_update=:huangfu_hall, basis_refactorization=:markowitz` in
`SolverOptions`, or set the same two MOI raw attributes in either order.
All supported HH scalar types are accepted. Native Float64 still requires
64-bit indices; Markowitz does not add that restriction.

The existing Markowitz backend supplies sparse elimination factors and the
trailing dense LU. HH extracts independent CSC L/U factors in the task scalar.
The trailing LU row permutation is composed with the outer row order and applied
to the lower-left sparse block. Upper sparse rows retain their column coordinates.
The dense matrix is not reconstructed or refactorized during extraction.

Backend choice is a factor type parameter, so an empty reset, copy, failed
refactorization or working-precision transfer cannot silently switch backends.
Backend construction uses its existing private output-slot reuse. Extracted
active factors and saved copies never alias mutable backend arrays. Ordinary HH
updates, reach-based unit-transpose preparation, bounded scalar pools and the
native UMFPACK path are unchanged. Explicit hypersparse policies continue using
HH's dense solve kernels and preserve stored BigFloat precision.

## Verification

`test/huangfu_hall_markowitz_tests.jl` first failed for all six tested scalar
types because the combination was rejected. Its initial implementation passed
828 component checks: sparse-only, dense-only and mixed factorizations, nontrivial
core and outer permutations, prepared/unprepared updates, forward/transpose
aliases, copied factors, singular refactorization rollback and dimension changes.
Existing public/MOI, precision-transfer and BigFloat hypersparse tests now also
exercise Markowitz. Exact equation assertions are used for rational types.

Use the normal Julia compiler for `test/huangfu_hall_tests.jl` allocation checks;
semantic tests can use `--compile=min`. Run one Julia/BLAS thread at a time with
the existing memory guard and the 8 GiB numerical virtual-memory ceiling.
`LocalPreferences.toml` remains configured with `precompile_workload=false`.
No precompile workload expansion is part of this change: the existing workload
already covers native HH and the shared Markowitz backend.

The external runner reuses the pinned afiro, adlittle, pk1, flugpl and fast0507
inputs and the public HH harness utilities. Every solve must reach OPTIMAL,
match the reference objective and certify feasibility in the original model.
The runtime selection solves only dual runtime.mps with its pinned input digest,
a default 900-second solver limit (optional fourth argument overrides it),
steepest-edge pricing, legacy strategy, no partial
pricing and an 80-update interval. Reports retain failures before the runner
exits unsuccessfully; a timeout is not classified as convergence.

```sh
julia -g0 -O2 --project=. diagnostics/huangfu-hall-markowitz/reproduce/external.jl markowitz small OUTPUT
julia -g0 -O2 --project=. diagnostics/huangfu-hall-markowitz/reproduce/external.jl markowitz runtime OUTPUT
```

The split runner passed 2,510 semantic checks with `--compile=min` and 1,833
checks with normal `-g0 -O2` compilation, including the original HH allocation
regressions and complete Markowitz allocation testsets. Two earlier attempts to
compile all public scalar combinations together reached the 300-second guard
inside LLVM. An initial mixed interpreter run reported three allocation failures;
all three pass under normal compilation. The split runner preserves the original
assertions and selects whole testsets, without weakening allocation limits.

```sh
julia --compile=min --project=. diagnostics/huangfu-hall-markowitz/reproduce/targeted.jl semantic
julia -g0 -O2 --project=. diagnostics/huangfu-hall-markowitz/reproduce/targeted.jl compiled
```

The earlier full
suite's baseline failures and compilation limit are documented in the
[scalar-extension record](../huangfu-hall-precision/README.md); this change does
not alter unrelated primal tests or solver heuristics.

## Extended runtime check

The initial 900-second Markowitz runtime check reached TIME_LIMIT after 60,732
iterations and 763 refactorizations, with no original-model restart. Its final
logged objective was 51,178,463.86519393, primal infeasibility 1,610.1267947153437,
and dual infeasibility zero. This was not an optimal or feasible result. Only
0.184 seconds of the solve were attributed to compilation. One SIGUSR1 profiling
peek was requested during this diagnostic; its timings are not a performance
comparison. A second run used a predeclared 1,800-second limit to check completion.
The runner now flushes diagnostic messages promptly.

Source review identified potential costs, without attributing the slowdown:
Markowitz's existing dictionary elimination and pivot search, conversion of its
dense core to CSC, and any additional fill in the extracted factors. Both HH
backends use the same triangular/update kernels after extraction. No heuristic,
precision or factorization-interval change was introduced to alter convergence.

The scalar external controls use afiro and adlittle in BigFloat and
Rational{BigInt}, both algorithms, plus afiro in Float32 with the previously
measured `sqrt(eps(Float32))` primal/dual tolerances. Defaults remain unchanged;
these controls do not claim to fix the known default-tolerance Float32 failures.

The extended runtime check returned **OPTIMAL** after 66,158 iterations and
835 refactorizations, with zero original-model restarts. The objective was
51,425,691.76206371, matching the reference, and original-model feasibility was
independently certified. Solve time was 1,011.180 seconds, including 0.274 seconds
of compilation. Whole-process peak RSS was 2,481,856 KiB (2.37 GiB), including
warmup and parsing. It used one Julia/BLAS thread and the 8 GiB virtual limit.
The shared logged trajectory prefix matches the initial attempt exactly; the
longer time limit allowed the same solve to finish, including postsolve cleanup.

This backend is substantially slower on this control than the previously
recorded native HH run (166.439 seconds, 61,705 iterations). These are different
factorizations and trajectories, not an isolated measurement of extraction cost.
The new backend is an additional explicit choice; the default remains native.

## Clean integration verification

On the integration branch based directly on master, all **2,516 semantic checks**
and **1,833 normally compiled checks** passed. This includes the additional
Float64 MOI solves through both backends. All ten external Markowitz controls
(afiro, adlittle, pk1, flugpl and fast0507, both algorithms) reached certified
OPTIMAL, with no original-model restarts. Ten further native HH controls match
the earlier certified native trajectories exactly: objectives, iteration and
refactorization counts, restarts, primal-vector bits and progress-log digests.

All ten scalar external controls also reached certified OPTIMAL (30 assertions).
These cover afiro/adlittle with BigFloat and Rational{BigInt}, and the predeclared
Float32 afiro tolerance control. The full runtime result above is additional.
No excluded large model was solved or factorized. The full project suite was
not rerun; this is the targeted/backend verification, with the pre-existing
broader-suite limitations linked above. No full package cache build was repeated.

[The machine-readable report](results/final.json) retains the successful runs,
the initial runtime timeout, input/source/harness digests and resource summaries.
Run `reproduce/audit.py` against the retained local reports to repeat the audit.
