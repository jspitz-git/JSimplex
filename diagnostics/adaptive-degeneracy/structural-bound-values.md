# Certified structural values across zero primal steps

This implements the core correction proposed by the
[extended runtime diagnostic](extended-runtime.md). The measured baseline is
`5df7515`; the complete candidate production digest is
`d338c92dd9e92c5064c4621291796bf3808341aa7d56668ff931d34452dcc6d4`.

## Numerical change and boundaries

A structural variable leaving the basis at a zero primal step can already lie
just beyond its selected bound within the existing feasibility tolerance. Exact
assignment to the bound can destroy the certified point. The captured runtime
transition at iteration 19,222 made the remaining certificate inequalities
incompatible with those nonbasic assignments, even in exact arithmetic.

The existing native tolerated-row-value rule now also covers nonfixed structural
variables on the legacy primal path that supports fully certified point recovery. Retention requires
the value to lie outside the selected bound, within its working-bound tolerance,
and within the original-bound tolerance unless an active, owned perturbation
journal authorizes the working bound. Recovery trials must still pass the
complete point certificate. The existing fast reconstruction acceptance checks
stored variable bounds and equations; this change does not replace it with a
complete model certificate after every pivot. Both originally fixed and working-fixed structural variables
retain their exact assignment. Positive-step exits still reach the exact bound;
existing retained nonbasic values survive subsequent reconstructions. Initial
nonbasic initialization remains exact.

The implementation does not change tolerances, precision, pricing or perturbation
scheduling. The dual and other numerical-policy paths are excluded from this new
structural rule. Existing row retention is unchanged. No new workspace storage
or persistent state is introduced.

## Regression evidence

The portable two-row regression represents the incompatible zero-step transition
for Float32 and Float64, both lower and upper bounds, and all four basis managers.
On the baseline, all sixteen actual pivot cases fail. The first test version
records 114 passing and 142 failing assertions (256 total). The initial fix
passes all 256. Review-driven scope checks then expose the uncertified
`solve_refinement` path (278 pass, 2 fail), and an unowned tightened working
bound (278 pass, 6 fail after adding four assertions). Both gaps are closed;
the final focused suite passes all 284 assertions.

Coverage also includes positive-step exits, subsequent native refactorization,
fixed columns under owned relaxation, absent/inactive/wrong-owner journals,
restoration, initial assignment, values beyond tolerance, and excluded policies.

Five earlier mathematical point snapshots remain recoverable with their nonbasic
values unchanged. Four actual captured pivots (6,799; 8,464; 14,186; 19,222)
complete and pass the full certificate with the captured basis exchange.
At 14,186 and 19,222 the pre-pivot point is bitwise unchanged. The combined replay
has 38 passing assertions. These are local replays, not full driver continuations.

| Validation | Passing checks | Mode |
| --- | ---: | --- |
| Focused structural regressions | 284 | `--compile=min` |
| Semantic and adaptive interaction regressions | 7,160 | `--compile=min` |
| Structural, point recovery and allocation regressions | 1,172 | Normal compilation |
| Earlier mathematical points and actual pivots | 38 | Normal compilation |

These suites overlap; their counts must not be added as independent coverage.
They do not constitute a whole-project test run.

## Fresh runtime experiment

The fresh solve uses runtime.mps with the checked SHA-256
`d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68`,
Float64, primal steepest-edge, PFI/native/80, one million iterations and a
900-second solver limit. Only adaptive stagnation monitoring, pricing and bound/
cost perturbations are enabled, with the same internal Phase-I construction as
before. Independent weak-pivot preference and the original-LP retry are disabled
by the existing diagnostic harness. These method overrides are hashed in the
report. This run is a convergence diagnostic, not a controlled speed benchmark;
the numerical trajectory is allowed to change.

All Julia payloads run sequentially with one Julia and one BLAS thread under
the existing 8-GiB virtual-memory guard, 6-GiB available-RAM floor and 1-GiB
swap ceiling. The long solve has an outer wall limit of 1,140 seconds. No new
medium result is claimed in this step.

The run reaches **TIME_LIMIT at 77,180 iterations and 900.017 seconds**, with
18,040 refactorizations and 47,170 rejected candidates. It does not reach Phase
II and does not return an original-LP solution. There is no numerical termination,
original-LP restart, precision boost or guard termination in this bounded run.

The changed core rule changes the trajectory from early in the solve. The
sampled completed-pivot auxiliary objectives are monotonically nonincreasing:

| Iteration | Solver seconds | Auxiliary objective | Stored primal infeasibility |
| ---: | ---: | ---: | ---: |
| 10,000 | 43.55 | 594,328.85489 | 0 |
| 20,000 | 101.22 | 208,637.95479 | 0 |
| 30,000 | 215.52 | 13,150.56061 | 0 |
| 40,000 | 305.83 | 9,522.39894 | 0 |
| 50,000 | 404.92 | 5,174.20241 | 0 |
| 60,000 | 527.09 | 3,976.52448 | 0 |
| 70,000 | 748.30 | 1,917.04772 | 0 |
| 77,000 | 898.33 | 812.97805 | 0 |

The final observed workspace has auxiliary objective 799.62161 and stored
primal infeasibility zero. It is explicitly labeled `uncertified_after_termination`
by the harness, so this is not a certified final objective or feasibility claim.
The last completed-pivot sample, at iteration 77,000, has objective 812.97805.
Even a feasible auxiliary point with positive artificial objective would not
establish feasibility of the original LP.

Although perturbations are enabled, **none are triggered** on this new trajectory.
The auxiliary bounds remain unperturbed. Eight pricing trials close: seven
productive returns and one expiration, all back to steepest-edge. There are no
open trials, overlapping interventions or phase transitions. This run therefore
does not exercise a new real-model interaction with an active perturbation;
owned-bound regression tests and the old perturbed snapshots cover that scope.
The diagnostics record eight preserved primal points and no joint-projection
attempts, unlike the preceding trajectory. This is evidence of continued progress
within the measured budget, not proof of convergence or permanent stability.

## External solver matrix

All 80 external solves pass: afiro, adlittle, pk1, flugpl and fast0507, each
with primal and dual simplex, four basis-update managers, and native/Markowitz
factorization. Each solve reaches OPTIMAL, matches its known objective and passes
the original-model primal feasibility check. The runner passes 245 assertions,
including five input hashes, and checks the complete production digest before
and after the matrix. These use the legacy strategy. No prohibited large model
is solved or factorized.

This matrix and the focused tests support the bounded core correction. The
remaining runtime Phase-I convergence question is separate; no claim of medium
convergence or successful restoration from a newly triggered perturbation is made.

## Reproduction and retained evidence

Run the payloads below sequentially through the existing memory guard and Julia
wrapper, with `precompile_workload=false` preserved. Use outer wall limits of
360 seconds for each regression/replay payload, 1,140 seconds for runtime, and
720 seconds for the external matrix. These are Julia payload commands; do not
start concurrent numerical processes. Choose fresh output names when repeating.

```sh
julia --project=. --compile=min diagnostics/adaptive-degeneracy/reproduce/structural_value_semantics.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/structural_value_compiled.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/structural_value_replay.jl /tmp/structural-replay.toml
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_one_first_failure.jl runtime primal both 900 /tmp/runtime-structural
julia --project=. diagnostics/adaptive-degeneracy/reproduce/representable_external.jl diagnostics/basis-selective-preparation/reproduce/external-inputs.toml /tmp/structural-external.toml
python3 diagnostics/adaptive-degeneracy/reproduce/validate_structural_values.py
```

The validator checks the committed text evidence against the current production
source digest. Historical validators for earlier production digests should be
run on their corresponding baseline revisions, not interpreted as regressions
of this changed source. The replay additionally requires the retained local
snapshots listed and hashed in its report; it is not a portable fixture test.

Committed evidence is in [results/structural-values](results/structural-values/).
Raw red/green logs, the measured source patch and a snapshot of diagnostic scripts are retained in
`.superpowers/adaptive-degeneracy/structural-values/`, with hashes in the local
artifact manifest. Older binary snapshots remain in their original directories.
