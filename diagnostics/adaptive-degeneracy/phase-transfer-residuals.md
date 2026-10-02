# Native residual correction at the captured phase boundary

This follows [the actual runtime transfer replay](phase-transfer-capture.md).
The approved next step was to localize residual rejection and test one bounded
correction in the problem's precision, including its effect on point feasibility.
This experiment makes no production change and does not continue Phase II.

## Controlled local experiment

The source is unchanged from `20e8bc9`, production digest
`d338c92dd9e92c5064c4621291796bf3808341aa7d56668ff931d34452dcc6d4`.
The existing auxiliary/original snapshot at iteration 102,446 has SHA-256
`70797028c15c9c33f98259dbe17bd2001996ba9c2ff35d35a85de008a7fff7c7`.
The input and isolated adaptive policy are those of the preceding capture.
There is no repetition of its 22-minute prefix and no new adaptive intervention.

The probe reconstructs the mapped original-dimension workspace with retained
nonbasic values. It measures each basis equation using the existing compensated
Float64 residual routine. For each separate variant it reloads the snapshot and
reconstructs a fresh workspace. One ordinary FTRAN or BTRAN solves for the
correction, which is added once in Float64. Nonbasic values remain unchanged.
The dual variants also recompute reduced costs from the corrected prices.

Julia 1.13.0/aarch64 uses one Julia thread and one BLAS thread. Runs are sequential
under the existing 8-GiB virtual-memory guard, 6-GiB available-RAM floor, 1-GiB
swap ceiling and 360-second outer wall limit. No higher-precision linear solve
or factorization is used. The numerical policy and tolerances remain unchanged:
primal tolerance 1e-7 and solve tolerance 5.684341886080802e-14.

## Independent correction results

The following counts use the componentwise residual-to-scale ratio. The existing
quality routine independently decides acceptance using its rounding enclosure.
All variants below pass the complete point certificate and primal feasibility of
the reduced original model; all still fail the complete basis-reliability check.

| Variant | Rejected primal equations | Rejected dual equations | Full point certificate |
| --- | ---: | ---: | --- |
| Mapped reconstruction | 13 (8 homogeneous) | 7 (5 homogeneous) | passes |
| One primal correction | 13 (12 homogeneous) | 7 | passes |
| One dual correction | 13 | 3 (all homogeneous) | passes |
| One correction in each direction | 13 (12 homogeneous) | 3 (all homogeneous) | passes |

After primal correction, the largest absolute residual **among rejected equations**
is 1.1771283820094786e-30. The largest residual over the entire primal system is
2.4651904542252663e-10; its componentwise scale makes it acceptable. The maximum
primal correction is 8.219297001924415e-8, and the relative residual maximum
remains one because some remaining equations contain only tiny contributions.

For example, reduced-model equation 4071 is homogeneous. After correction its
two nonzero terms are approximately -1.1771283820094786e-30 and
7.713801763061988e-74. The residual is tiny in absolute units, but almost as large
as the equation's componentwise scale. Equation 4933 is not homogeneous: its
right-hand side is -5.751854285374511e-66. Its two terms are approximately
-9.115745035929407e-64 and 6.077163357286271e-64; the relative residual is 0.19547.
These tiny right-hand sides belong to the assembled basis system, including
retained nonbasic contributions. They are not asserted to be original MPS input
values. The indices refer to the reduced workspace, not original-input MPS row
numbers.

After dual correction, the largest absolute residual **among rejected equations**
is 1.0951390874978147e-29. The maximum over all dual equations is
1.2011557070673514e-7, larger than before correction but acceptable in those rows'
componentwise scales. The maximum price correction is 7.824490110262515e-5.
The three remaining rejections involve homogeneous equations with contributions
around 1e-29. A claim that every absolute residual improves would be incorrect.

## Why existing native cleanup still rejects

`_try_native_cleanup_recompute!` already attempts one compensated native
correction and calls `_clean_homogeneous_terms!` on a private candidate if needed.
Its acceptance check remains unchanged. The probe separately inspects that
otherwise discarded candidate, then invokes the actual cleanup on a fresh state.

The existing primal cleanup proposal clears **525 basic-vector coordinates**.
Of these, **341 also participate in equations with nonzero right-hand sides**.
The supplied cutoff is 4.6721294222177306e-21. Small values below this cutoff can
still be necessary for equally small nonzero right-hand sides: for example,
after cleanup equation 706 has no nonzero product left, but its right-hand side
is -5.605381189661157e-34. Its componentwise relative residual becomes one.

The proposal leaves **233 rejected primal equations, all nonhomogeneous**.
One was already rejected before cleanup; this is not a count of 233 new failures.
The largest residual among them is 3.983859320692943e-21. Full point and reduced
original-model primal certificates still pass, but the stricter componentwise
basis-solve test does not. Therefore the existing cleanup correctly rejects
publication of the proposal.

The separate dual cleanup trial clears 159 dual-vector coordinates and passes:
maximum relative residual 9.884630649085414e-17, with no rejected equations.
This is a local diagnostic result. The actual combined cleanup stops at its
failed primal stage and never publishes this separately tested dual correction.
All cleared-coordinate indices in the raw report are positions in the solved
basic vector (primal) or price vector (dual), not general model variable indices.

The actual cleanup returns false and leaves the primal vector, dual-price vector
and reduced costs bitwise unchanged. Its failure is a limitation of the recovery
proposal, not acceptance of a corrupt point. Neither a larger zeroing threshold
nor removal of the reliability guard is supported by this experiment.

## Consequence and next investigation

A single native correction substantially reduces the relevant residuals, but
additive correction followed by broad zeroing cannot preserve all coupled tiny
components. The next focused experiment should reconstruct the offending local
relations while retaining their nonzero right-hand sides and coupling to other
rows. Any candidate must still pass the unchanged full-system solve-quality
checks and complete point certificate. This is a numerical recovery question at
the phase boundary, separate from adaptive pricing or perturbation scheduling.

No production fix, complete phase export, Phase-II progress, postsolved original
solution or runtime convergence is claimed. The saved endpoint remains available
for testing the next candidate without another long capture.

## Reproduction and evidence

Use the one-thread wrapper and memory guard described above:

```sh
julia --project=. diagnostics/adaptive-degeneracy/reproduce/probe_phase_transfer_residuals.jl .superpowers/adaptive-degeneracy/phase-transfer/runtime-transfer-capture /tmp/runtime-transfer-residuals
python3 diagnostics/adaptive-degeneracy/reproduce/validate_phase_transfer_residuals.py
```

The final probe passes **9 assertions** with normal compilation (testset time
5.6 seconds). They check baseline point certification and residual rejection,
nonbasic-value preservation, and atomic rejection by the existing cleanup.
The validator additionally checks recorded residual counts, certificate outcomes,
source/snapshot hashes and local artifact provenance. Earlier transfer, structural
retention and continuation evidence validators are rerun on unchanged sources;
there is no new whole-project or external-matrix suite claim.

Results are in [results/phase-transfer-residuals](results/phase-transfer-residuals/).
The final as-run scripts, wrapper, log and rejected-cleanup snapshot are retained
under `.superpowers/adaptive-degeneracy/phase-transfer-residuals/`; the original
capture stays in its prior directory. The artifact manifest records their hashes.
