# First equation-feasibility loss on the residual-probe trajectory

The results and decisions below describe the recorded historical revision. See
[the native pivot-probe follow-up](NATIVE-PIVOT-PROBE.md) for the later core fix,
its certified runtime runs, and the remaining bound-snap obstruction.

This follows [the rejected finite-residual experiment](REJECTION-SURGE.md).
The starting revision is `a4bac56b629d0c1de77f45e490137c8f5c6169b9`.
At that stage, the residual-gate relaxation remained a process-only diagnostic intervention.

## First failing point

A fresh PFI run checks the full point before every pricing call, including retry
calls after refactorization. The first 13,572 checks pass. Check 13,573, at
iteration 3,604, fails both phase-model feasibility and consistency between
matrix activities and stored row variables. All individual bound violations
remain within 1e-7; the maximum is 9.923975477223495e-8. Thus the loss predates the
known restart at iteration 3,683.

The transition entering column 23,107 at row 9,144 has step
1.5471258360254222e-20, pivot 0.49635989003713604, and direction infinity norm
1.6303389505233952e8. The preceding point passes both equation certificates;
its maximum stored-equation residual, evaluated at 256 bits, is 3.279e-11.
The recomputed point has maximum residual 4.632277252063395e-7. Rows 20,945–20,947
have actual activity -59.99999953677227 against an upper bound and stored row
value of -60.0. These are actual violations of the phase model, not merely a
mismatch inside an otherwise feasible inequality.

The existing Float64 point predicted from the accepted direction passes all
certificates. It differs from the recomputed point by at most 1.356e-6. A separate
diagnostic Float64 correction, using a compensated residual of the full stored
point and the saved basis factor, also yields a certified point. The 256-bit
calculation evaluates stored equations only; no high-precision factorization
or high-precision solver update is used.

## Why the existing fallback misses it

`_restore_legacy_primal_point!` previously returned immediately whenever all
basic values were finite and the stored bounds were feasible. Equation consistency
was checked only while certifying a fallback after a bound failure. That allowed
a bound-feasible but equation-infeasible reconstruction to replace a valid
predicted point and persist until the later refactorization exposed bound errors.

The narrow change probes the complete stored point with the existing native
compensated residual routine before taking that early return. A residual above
the absolute primal tolerance enables the existing predicted-point fallback.
Its original bound, phase-model and stored-row certificates still control
acceptance, and cancellation or failed certification restores the reconstructed
values. The probe uses the full matrix and nonbasic contributions, avoiding a
rounded assembled right-hand side. An unavailable native probe retains the
previous behavior; this change does not escalate arithmetic precision.

This adds one compensated matrix scan after a bound-feasible legacy reconstruction.
It adds no basis solve, candidate rejection or refactorization. It does not remove
the weak-pivot residual gate, adopt the structural-value intervention, or prove
phase-I convergence.

## Verified transition and limits

The new small regression initially has 56 passing and 32 failing assertions
across Float32/Float64 and all four managers. With the change, all 88 pass;
combined focused coverage passes 1,586 assertions with `--compile=min`.
Eight additional normally compiled assertions verify the actual captured point:
it is repaired without changing the basis or iteration counter.

A fresh finite-residual diagnostic run with the point repair certifies every
visited pricing point through iteration 4,000: 17,787 checks, 478 refactorizations,
and final auxiliary objective 605519.5025242418. All equations and bounds pass
at the endpoint. This is a targeted continuation of the experiment past the
known failure, not a complete solve. It does not adopt the finite-residual gate
relaxation in production or remove the original objective plateau.

Read-only review found no blocking correctness or scratch-aliasing issue. Its
performance concern is the added full-matrix scan; runtime reports below record
the resulting observed workload, not a controlled timing benchmark.

The broader semantic regression runner passes 2,698 assertions with
`--compile=min`; native-residual tests pass 125 assertions with normal
compilation. All 80 external LP relaxations pass optimum and original-feasibility
checks (245 assertions). Combined with the focused and snapshot checks, this
is 4,662 passing assertions, not a run of the full project suite.

The additional scan has a visible cost on fast0507. The four native primal
managers take 16.05–17.56 seconds, versus 12.52–13.98 seconds in the earlier
stored direction-price report, with identical iteration counts. The observed
ratios are about 1.20–1.28. These are historical single-run comparisons, not a
controlled benchmark; the correctness fix is not claimed to be cost-free.

## Fresh runtime validation

All four managers run for 300 solver seconds with the production change only:
legacy primal, steepest-edge pricing, native refactorization, interval 80,
iteration limit 1,000,000, and relaxed integrality. Neither process-only
intervention is enabled. All finish with `TIME_LIMIT`, one reduced phase-I
workspace, and no reported numerical failure or original-LP restart.

| Manager | Iterations | Refactorizations | Rejections | Auxiliary objective |
| --- | ---: | ---: | ---: | ---: |
| PFI | 7,537 | 2,292 | 133,801 | 605519.5025248753 |
| Forrest–Tomlin | 8,327 | 2,377 | 99,075 | 605524.4037340614 |
| Suhl–Suhl | 4,006 | 622 | 83,896 | 605524.4037455912 |
| Bartels–Golub | 7,127 | 1,394 | 72,605 | 605524.4037401350 |

None finishes phase I. The original plateau remains. FT and SS perform more
rejections/refactorizations than in the prior reports; changing the maintained
point can change the subsequent trajectory. The patch itself requests neither
rejections nor refactorization, but these runs are not evidence of improved
convergence or generally reduced work. They also do not independently certify
every point of the four default runs; that stronger per-point check was run on
the bounded 4,000-iteration diagnostic trajectory described above.

Text reports, source hashes and snapshot hashes are in
[results/equation-loss](results/equation-loss). Binary snapshots, local manifests
and preferences remain uncommitted. Initial reports retain the hashes of the
runner versions that produced them; the final diagnostic also has an explicit
before-fix mode and rejects an unexpected second phase-I start.

The remaining convergence work concerns degenerate step selection and the
previously identified bound-snap obstruction. The finite-residual gate relaxation
and structural-value retention remain diagnostic experiments requiring further
validation before adoption. This fix only removes the demonstrated hole in
certified point preservation.

## Reproduction

Use the same single-process Julia/BLAS and memory guard as the parent report.
The input is `/home/jspitz/mps/runtime.mps`, SHA-256
`d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68`.
Do not redirect logs to a filename colliding with the fresh snapshot prefix.

```sh
# Disable only the new equation trigger to reproduce the original first loss.
julia --project=. diagnostics/primal-phase1-stagnation/reproduce/first-equation-loss.jl /home/jspitz/mps/runtime.mps finite_residual_before_fix 300 PREFIX
julia --project=. diagnostics/primal-phase1-stagnation/reproduce/inspect-equation-loss.jl PREFIX

# With the equation-preservation change, check the actual captured point.
julia --project=. diagnostics/primal-phase1-stagnation/reproduce/check-equation-point.jl PREFIX

# Stop after certifying all visited pricing points through iteration 4000.
julia --project=. diagnostics/primal-phase1-stagnation/reproduce/first-equation-loss.jl /home/jspitz/mps/runtime.mps finite_residual 300 NEW_PREFIX 4000
```

The first-loss snapshots are local under `.superpowers/phase1-equations/first.*`.
The preceding snapshot saves point and basis metadata, not a complete previous
factor/pricing state. The transition snapshot saves the actual accepted direction
before recomputation, while the failure snapshot retains the live updated factor.
These files support point/transition inspection; they are not advertised as an
exact restart of the preceding pricing cache.
