# Certified local reconstruction during driver cleanup

Base: `8d9b83e` on `codex/adaptive-degeneracy`.
This follows the native `cycle` failure left by
[reliable price refinement](reliable-price-refinement.md).

## Cause

Native-reader `cycle` reached iteration 868, restored the original bounds after
adaptive perturbation, and stopped with `bounded feasibility recovery exhausted`.
The restored point genuinely violated bounds. However, the driver could not
hand its basis to dual feasibility repair because reconstruction of that basis
failed the componentwise residual check first.

The captured 1264-row basis had compensated FTRAN residuals of about `6.34e-14`
absolute and `0.382` relative. One ordinary native correction plus existing
homogeneous cleanup was insufficient. The existing phase-transfer local
reconstruction repaired the same system to about `6.59e-16` relative residual;
the largest change to the original basic vector was `2.56e-13`. Existing BTRAN
cleanup already repaired the dual solve. Original bounds and costs were active.

A diagnostic substitution of the phase primal helper into driver cleanup
produced a reliable, still bound-infeasible basis. The existing dual repair then
reached a certified working-model optimum at iteration 948. Using the complete
phase-transfer helper would be wrong here: it requires a primal-feasible point
before publication and therefore cannot prepare an infeasible basis for repair.

## Core change

`_native_cleanup_solve!` has a default-disabled `local_reconstruction` option.
Driver recomputation enables it for its FTRAN only. If the previous single native
correction and homogeneous cleanup still fail, the existing local row/component
reconstruction may repair the original corrected candidate using that same
correction-based cutoff. A rejected homogeneous cleanup is discarded before
trying this alternative; otherwise it may have erased genuine tiny neighboring
terms that local reconstruction needs.
There is no extra linear solve or enlarged correction budget. Every equation
must pass the unchanged compensated residual check before publication.

The helper explicitly rejects this fallback for transposed systems. It refreshes
the final quality before any forced-refinement improvement check. The driver
publishes primal values, dual values and prices together only after both solves,
finite prices and the final stop check succeed. Bound feasibility remains a
separate driver decision. This applies to driver basis verification, including
mandatory model cleanup and driver feasibility recovery, for both simplex
algorithms; the existing checked-mode and zero-budget exclusions remain intact.

This is numerical reconstruction in the problem's scalar precision, not an
adaptive pricing or perturbation decision. Previously successful cleanup paths
and ordinary iteration solves retain their existing behavior.

## Portable tests and limits

An independent two-coordinate identity system has RHS `[tiny,1]`. Correcting
an erroneous first value `noise` loses `tiny` through cancellation. Local
reconstruction must retain the nonzero RHS, while the first variable's lower
bound deliberately keeps the accurate basic point infeasible. Tests cover
Float32/Float64, all four managers, both algorithms, and one correction attempt.
They also cover every reached stop/throw boundary, failed BTRAN after successful
FTRAN, a wrong factorization, zero budget and checked-mode exclusion. Failed
operations preserve all published point, scratch-solve, price, bound and basis
state.

A coupled triangular regression uses a real factorization with a one-ulp error
in one diagonal entry. Homogeneous clearing erases a genuine tiny neighbor; the
local fallback succeeds only when it starts from the original corrected vector.
Deleting that reset in a diagnostic process causes 24 of its 40 assertions to
fail. The final portable tests pass 282 assertions with `--compile=min`. Running
the independent cancellation regression against the base implementation gives
80 passes and 48 expected failures.

The first exploratory triangular fixture instead entered an existing local-row
cycle from a zero vector. It was replaced by the identity fixture to isolate
cancellation recovery; this change does not broaden the local reconstruction
algorithm or claim to repair that separate limitation.

## Reproduction

Use one numerical process and the established memory guard (8 GiB virtual-memory
limit, 6 GiB available-RAM floor, 1 GiB swap ceiling), one Julia and BLAS thread,
and local `precompile_workload=false`.

- `reproduce/cycle_cleanup_probe.jl SNAPSHOT` separates reconstruction quality,
  primal feasibility and driver/phase cleanup on the saved failure.
- `reproduce/cycle_solve_probe.jl SNAPSHOT` compares the native cleanup and phase
  local reconstruction for the same FTRAN and BTRAN systems.
- `reproduce/cycle_cleanup_continuation.jl SNAPSHOT` tests production cleanup and
  continuation, with working-model feasibility and optimality certificates.
- `reproduce/driver_reconstruction_semantics.jl MOD010_BOUNDARY_PREFIX OUTPUT_TOML`
  adds the new portable tests to the existing semantic runner.
- `reproduce/broad_corpus.jl INPUTS REFERENCES JOBS OUTPUT_PREFIX` uses the same
  paired 30-configuration corpus and independent original-point/objective checks
  as the previous report. Jobs are retained in `results/driver-reconstruction`.

The original capture is recorded in
`results/reliable-prices/validation-captures.json`. Binary snapshots remain local;
input files, manifests and local preferences are not committed. Reproduce the
original failed cleanup probes on the base commit. Runtime and medium are not
rerun for this bounded correction.

## Whole-model verification

Production source SHA-256:
`6f5d7c7d0d1e721a29464509a65681eecffcec681e81ae9a1850c0fd9ad9ebf7`.

The fresh native `cycle` solve reaches **OPTIMAL in 963 iterations**, with 13
refactorizations and objective `-5.226393024894102` (HiGHS reference:
`-5.226393024894103`). Both the reader model and original unscaled model pass the
primal feasibility check. The full solve retains the original intervention
settings; its dual cleanup then primal continuation differs from the diagnostic
saved-state continuation that directly requested unperturbed dual repair.

The paired corpus improves from **28 to 29 verified optima out of 30**.
The other **29 configurations** have exactly the same status, iterations,
refactorizations, phase sequence and objective as the base. JuMP `stocfor2`
remains a numerical error at iteration 1957 (`primal feasibility lost`). There
are no time limits or harness exceptions. See [the paired results](results/driver-reconstruction/models.md).

All jobs retain Float64, steepest-edge, native refactorization every 80 updates,
relaxed integrality, a 90-second model limit and 1,000,000 iterations. The only
enabled adaptive switches are stagnation monitoring, pricing, primal/dual
perturbations and Phase I; weak-pivot preference and original-LP retry remain
disabled diagnostically. These runs establish neither universal convergence nor
a speed improvement.

## Regression verification

The final portable suite passes **282 assertions** with normal compilation and
`--compile=min`. The broader semantic runner passes **10,729 assertions** with
`--compile=min`.
Counts include overlap between existing runners, not distinct tests. The final
production captured continuation passes **six assertions** with normal
compilation, including reliable basis reconstruction, separate initial bound
infeasibility, and final working-model feasibility/optimality certification.

The earlier focused normal-compilation run passed 1,008 assertions, but its
captured continuation then failed four assertions because the local fallback
started from the already-mutated homogeneous candidate. The final correction
restores the raw corrected candidate; both the successful captured continuation
and the separate coupled regression now cover that failure. The first combined
normal run was explicitly stopped after printing portable-test failures. These
intermediate runs are not reported as final successful validation.

Independent read-only review found no remaining issue in the final change.

The normal-compilation project entry point (`--project=. test/runtests.jl`) was
also attempted with a 300-second wall guard. It was terminated at that limit
(exit 75) in the existing `native_reliable_price_tests.jl:73` testset, with no
failing assertion printed. The short termination log does not establish whether
the time was spent compiling or executing that testset. This is **not a full
project-suite pass**. The successful focused and semantic runs above provide
the completed regression evidence; the broader entry-point run is incomplete.
