# Numerical guard repairs

Work starts from master `3807f50` on `codex/numerical-guard-repair`.
The historical findings are in `../numerical-guard-audit/README.md`. Numerical
repairs precede performance changes. No tolerances or candidate policies are
relaxed. Numerical jobs run sequentially with one Julia/BLAS thread, the existing
8 GiB VM / 6 GiB available RAM / 1 GiB swap guard, and preserved local preferences.

## Greenbea: ambiguous terminal row complementarity

The original BG/native80 dual legacy solve reproduces `NUMERICAL_ERROR` after
9,061 iterations. Its first terminal candidate is at iteration 3,350, before
postsolve. Primal feasibility passes, but row-activity variable 5203 fails the
independent original-objective complementarity check. Its negative price is
approximately -100 and its upper bound is 50; the coarse activity enclosure is
[49.99999995562166, 50.00000010464976]. The upper endpoint lies just beyond the
absolute primal tolerance 1e-7. Three native dual corrections, or a fresh LU dual
solve, do not resolve this row-activity uncertainty; after the first correction
the basic stationarity error already falls below 1e-12.

The repair batches only unresolved, nonstationary Float32/Float64 row activities
and checks their distance to the bound selected by the certified price sign.
Passing that same bound as both lower and upper targets preserves absolute
complementarity, rather than merely accepting row feasibility. The existing
native compensated row filter is tried first; the existing bounded exact
fallback remains available for unresolved extreme arithmetic. Basic stationarity,
structural-variable checks, finite-bound checks, and both tolerances are unchanged.
No refinement storage is created when the ordinary certificate succeeds.

The repaired full solve returns OPTIMAL after 3,640 iterations, objective
-72555248.1298455, and independently verified original primal feasibility. This
matches the preserved HiGHS reference -72555248.12984599 for the identical input
SHA-256. The first 42 logged progress samples (excluding timestamps) are identical to the baseline;
the trajectory changes only after the formerly rejected terminal candidate.
The solve then completes postsolve cleanup, without an original-LP restart.
Peak process RSS is 2.198/2.203 GiB (baseline/repaired, including compilation).
Whole-call time is 38.04/37.50 s and compilation 34.67/35.88 s: these cold diagnosed
runs establish correctness, not a speedup.

The focused test initially fails all four optimal-witness assertions on the
baseline (Float32/Float64, lower/upper active bounds), while the feasibility and
negative controls pass. After repair these 28 checks pass. Four further negative
controls reverse the row price while preserving basic stationarity, so rejection
cannot be attributed to the basic-column check. The combined targeted numerical
and allocation suite passes 1,381 checks. Independent static review found no
blocker; its sign-test suggestion was incorporated. Broader semantic validation passes all 15,681 assertions; 100 unique external
combinations pass all 305 assertions, including original primal feasibility and
reference objectives. `results/external-audit.json` verifies completeness and
unchanged source throughout both guarded jobs. These are selected regressions,
not a claim that the entire project suite passes (known baseline failures remain).

Raw snapshots remain in `.superpowers/numerical-guard-repair/greenbea-baseline`
and `greenbea-repaired`. They contain candidate equations and values, not live LU
pointers. `results/greenbea-probe.toml` records the baseline candidate analysis. Reproduce its `certified=false` fields
against baseline `3807f50`; the probe calls the certificate in the loaded checkout,
so the repaired code should instead certify that same stored candidate.
The result files' `source_revision` is the base HEAD; the repaired run additionally
uses the uncommitted row-complementarity patch, whose source aggregate was recorded after the solve without further source changes
and is stored
in `results/final-validation-source.json` (Project.toml plus src/**/*.jl sorted by
relative path, each path followed by NUL and file bytes).

## Reproduction

Run all Julia scripts under the repository's existing memory guard and Julia
wrapper. `reproduce/capture.jl INPUT MANAGER BACKEND OUTDIR` uses native reading,
Float64, dual legacy steepest-edge, interval80, no partial pricing, integrality
relaxation, a 300 s solver budget, and terminal-only snapshots. Each output
directory must be fresh. `reproduce/probe_terminal.jl SNAPSHOT OUTPUT` separates
feasibility, stationarity, and row/column complementarity; its 256-bit selected
price dots are independent diagnostics, not production iteration arithmetic.
`reproduce/targeted.jl` runs the focused numerical and allocation regressions.

## Fresh dual rows and configured small-pivot refinement

Two independent core defects were reproduced and repaired after the greenbea
change. These changes do not constitute a complete pilotnov repair.

* A fresh factorization bypassed the legacy BTRAN row-residual check. Fresh LU
  does not guarantee a reliable transpose solve. Apply the existing check to
  fresh factors too, preserve stop precedence, and allow the existing bounded
  native correction budget. When correction disproves a tableau candidate,
  the transactional recovery repeats the same configured ratio test and checks
  the replacement direction and bound flips before publication. Retaining the
  final low correction during compensated pricing avoids rounding away a small
  tableau coefficient. This is the narrow core port of experimental `3f4e973`;
  no experimental factor optimizations or pricing-policy changes are included.
  The focused regression changes from 190 passes, 43 failures and 12 errors to
  419 passes.
* Exceptional small-pivot certification unconditionally constructed native LU,
  even when Markowitz was selected. On the captured pilotnov iteration663 basis,
  this preconditioner exhausted the existing 32 corrections, leaving a relative
  residual around2.37e-25 instead of the required1e-40. The selected Float64
  Markowitz factor reaches the existing256/512-bit diagnostic targets in2/5
  corrections. Preserve the chosen backend for this exceptional path. This
  does **not** introduce another precision escalation: the existing BigFloat
  certificate and its targets remain unchanged; its preconditioner and solves
  remain Float64. Native-backend callers retain the previous solve path.
  A portable2x2 regression first fails its certification assertion, then passes;
  expanded positive, infeasible-price, stop, orientation and ownership checks
  pass50 assertions across all five Markowitz managers.

### Pilotnov: historical failure, subsequently repaired

The account below records the unresolved state at this report's revision.
The subsequent [ratio and restoration audit](../pilotnov-ratio-audit/README.md)
identifies exact-breakpoint pivot selection and a scaling-only cleanup gap.
With those repairs, all ten public manager/backend combinations solve pilotnov
with the dual algorithm and pass original feasibility and the reference objective.
The earlier failed experiments below remain historical evidence.

`results/pilotnov-cases.json` distinguishes the successive experiments. On
PFI/Markowitz80, current-master-based code first fails at355. The fresh-row port
reproduces the historical experimental failure at663. Retaining Markowitz in
small-pivot certification passes that point, but a fresh BTRAN fails at696 in
phaseII. There is no postsolve or cleanup transition at this failure.

The row696 inverse action has infinity norm about1.60e30. Fresh native and
Markowitz factors both fail the legacy row-residual test; twelve native
corrections do not recover it. Independent direct256/512-bit factorizations
agree, and their Float64-rounded result passes the unchanged row check
(ratio0.002775). Thus the solution is representable, but ordinary factorization
is unreliable for this extremely sensitive basis. Independently equilibrating
that basis allows native Markowitz and two compensated corrections to pass.
An isolated full-solve prototype, however, changes the trajectory and fails at
435. This scaling prototype is **not** in production.

All696 recorded accepted pivot entries agree with independent refined reference
solves; this alone says nothing about the rest of their directions or states.
The subsequent full-state reference audit in `pilotnov-state-reference.toml`
checks selected early growth transitions, including49 and121. Accurate directions
and reconstructed basic values reproduce the enormous increases, from about
5.4e6 to9.2e10 and3.4e11 to2.5e17. These next-point estimates use the recorded primal step and old basic slots;
they are not an independent ratio/step audit. The sampled early growth is
reproduced by reference basic values and directions, and no false-pivot cause
was found. Later primal values still have substantial absolute drift. Investigate
the ratio decisions and basis conditioning further; do not claim convergence
from passing iteration663.

### Direct SS: distinguish stored-factor error from application error

The preserved fast0507 tape with directSS/native and interval320 reproduces the
historical step640 dense-RHS residual4.476e-10; freshLU gives5.90e-17. Probing
every step561..640 locates an earlier failure at631. A late elimination
multiplier reaches2.4e6. Applying the *same stored factors* at256 bits, then rounding the result to
Float64 for residual measurement, leaves
residual3.48e-11, so both factor storage and application contribute. In contrast,
one existing native compensated residual correction reduces all probed failing
dense solves to about1e-17. No early refactorization is used in these probes.

Diagnostic-only FMA elimination, FMA application, and compensated row-operation
application improve selected samples but do not clear every probe. They are not
production changes or successful fixes. `ss-native-probes.json` retains all
failing probes for each valid variant. Earlier `ss-fma-both` changed an inactive
application path (effectively elimination only); `ss-compensated`,
`ss-compensated-counted`, and `ss-compensated-dispatch` did not exercise their
new method and are invalid application experiments. Their raw files are retained;
the valid `ss-compensated-finish` run asserts2341 calls to the actual specialized
finish path. No speed benefit is claimed for these arithmetic prototypes.

The combined production repairs pass1,850 focused/numerical/allocation checks
with normal compilation and15,688 semantic checks with `--compile=min`.
Independent final static review found no blocker. Source and log hashes are in
`results/dual-recovery-validation.json`. These checks are selected regressions;
final broader external and runtime validation is still pending at this checkpoint.
