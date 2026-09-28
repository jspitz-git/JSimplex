# Native weak-pivot correction after point preservation

Starting revision: `78e3d9c`. This continues the rejection-surge and equation-loss
investigations. The task is numerical correctness of the primal core, not an
adaptive response to legitimate degeneracy.

The selected weak pivot may be accurate even when an unrelated homogeneous
row gives a componentwise direction residual ratio of one. The old gate used
`quality.reliable` to reject before the compensated residual could be used for
a native correction. The change removes that veto while preserving failure
on unavailable/nonfinite residuals, nonfinite corrections, cancellation, and a
relative pivot correction larger than `sqrt(eps(T))`.

This is not unconditional acceptance of finite residuals. The original forward
and transpose agreement checks still run, and the pivot sensitivity test still
rejects the captured false pivot. The correction does not replace the selected
direction or change model arithmetic precision. Strong pivots keep their fast
path. Nonbasic structural values and adaptive strategy are unchanged.

The earlier unrestricted experiment exposed an equation-infeasible reconstructed
point. Commit `a6cbba2` independently fixed the demonstrated missed fallback.
The validation therefore certifies actual pricing points, including fresh-factor
retries, instead of inferring safety merely from a TIME_LIMIT status.

The small fixture now includes both zero and positive steps for Float32/Float64
and all four basis managers. Before the gate change it has 104 passes and 72
failures; after the change it is included in 1,762 passing focused assertions.

A first 300-second PFI process-only experiment after point preservation reaches
16,458 iterations, 2,082 refactorizations and 60,168 candidate rejections, with
one reduced phase-I workspace. Its objective is 605519.5025224332. This reproduces
the proposed gate behavior but does not certify all intermediate points.

The production-source PFI run separately certifies all 46,148 pricing points and
the terminal point. It reaches 12,190 iterations and remains at objective
605519.5025266991. Certificate computation takes 124.84 of the 300 solver seconds,
so its iteration count must not be treated as a speed comparison.

Neither run completes phase I. The retained bound-snap obstruction and adaptive
step-selection work remain separate from this narrowly established core defect.

## Certified runtime runs

Every manager uses the user configuration: Float64, legacy primal, steepest-edge,
native refactorization, interval 80, relaxed integrality and a 300-second solver
deadline. One Julia and BLAS thread run under the existing 8 GiB virtual-memory
limit and owned-process guard (6 GiB available-RAM floor, 1 GiB swap ceiling).
The input SHA-256 is
`d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68`.

| Manager | Iterations | Refactorizations | Rejections | Certified pricing points | Auxiliary objective |
| --- | ---: | ---: | ---: | ---: | ---: |
| PFI | 12,190 | 1,266 | 32,815 | 46,148 | 605519.5025266991 |
| Forrest–Tomlin | 6,605 | 1,700 | 41,837 | 50,086 | 605524.4037304176 |
| Suhl–Suhl | 6,662 | 977 | 35,787 | 43,369 | 605524.4037498103 |
| Bartels–Golub | 5,283 | 1,597 | 48,005 | 54,845 | 605524.4037554335 |

All four runs end in TIME_LIMIT with one phase-I workspace, no reported numerical
failure or original-model restart, and passing terminal-point certificates.
They check every point presented to pricing, including retries. This is not a
proof that every FTRAN component is forward accurate, that every direction or
basis is well conditioned, or that an arbitrarily longer trajectory remains safe.
The full point-preservation fallback still rejects an uncertified prediction;
the probe does not guarantee that every possible reconstruction is repairable.

The unchanged plateau is not treated as a solved runtime problem. Exact snapping
of a tolerated structural bound violation can still block a candidate, as shown
by the earlier bound-snap investigation. Retaining those structural values or
changing pricing on stagnation remains a separate design choice and is not part
of this patch.

## Remaining endpoint obstruction

The new certified PFI terminal snapshot is inspected after a fresh native
factorization and rebuilt steepest-edge weights. This is a refreshed reference,
not a replay of live caches. Both pre/post-refresh certificates pass; the primal
point moves by at most 4.537e-9. The selected column is 1,533: cached price
-271771.9230018593, direction price -271771.92300184874, direction infinity norm
19303.330307678687. Harris proposes a zero step at row 23,805 with pivot
0.58538958997852. All 32 highest scored inspected candidates pass the direction
price check and receive zero-step proposals.

The same structural variables 15,754 and 23,386 limit the relaxed step. Their
values are -8.6394e-8 and -7.0570e-8, inside the 1e-7 permitted violation. Exact
snapping would require a negative step and induce respective violations
1.0324e-6 and 8.6799e-7 at another basic variable, 24,106. The existing snap
feasibility check correctly rejects those exchanges under the current convention.
A native residual correction of the selected direction has infinity norm
3.475e-8 and leaves its zero-step proposal unchanged.

This is evidence of the remaining local obstruction, not a proof that every
later rejection or cycle has the same cause. These are ratio proposals; the
inspection does not run every subsequent pivot acceptance check. Changing the
nonbasic-value convention or responding to stagnation remains separate work.

## Verification

The focused runner passes 1,762 assertions with `--compile=min`, including the
new 176-assertion zero/positive-step fixture. The broader semantic runner passes
2,698 with `--compile=min`. Normal compilation passes 125 native-residual checks,
32 captured false-pivot checks and 20 captured accurate-pivot checks. All 80
external LP relaxations (245 assertions) reach the reference optimum and pass
original-model feasibility checks: native/Markowitz, primal/dual and all four
basis managers over the existing five-model manifest. This totals 4,882 assertions,
not a full project-suite run. A further 72 assertions verify compatibility of
the historical process-only intervention with the changed source.

Read-only review found no blocking issue in the gate change or diagnostic observer.
Its recommendation to cover a positive step was added before validation. The
observer makes no solver-state mutation; it stops on the first failed point
certificate and separates terminal-point certification from pricing points, since
a deadline can interrupt reconstruction. Reports record production source hashes;
the initial process-only PFI experiment is separately labeled in
`results/native-pivot-probe/initial-experiment.json`.

## Reproduction

Run one numerical process at a time through the existing guarded Julia wrapper.
Keep local `precompile_workload = false`. From this checkout:

```sh
julia --compile=min --project=. test/legacy_primal_residual_probe_tests.jl
julia --compile=min --project=. diagnostics/primal-phase1-stagnation/reproduce/focused-core.jl
julia --compile=min --project=. diagnostics/primal-runtime-stability/reproduce/regressions.jl
julia --project=. diagnostics/primal-phase1-stagnation/reproduce/certify-runtime.jl /home/jspitz/mps/runtime.mps pfi 300 OUTPUT_PREFIX
julia --project=. diagnostics/primal-phase1-stagnation/reproduce/inspect-candidates.jl OUTPUT_PREFIX.terminal.bin baseline
```

Repeat the certified runtime command sequentially for `forrest_tomlin`, `suhl_suhl` and
`bartels_golub` using fresh prefixes. The runner fails at the first uncertified
pricing point and writes a binary snapshot. Binary snapshots remain local under
`.superpowers/phase1-core/`; hashes and text reports are committed under
`results/native-pivot-probe/`. Old experiments require the source revision recorded
in their reports; their process-only gate override remains callable on both old
and new production source.
