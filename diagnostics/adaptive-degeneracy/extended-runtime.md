# Extended runtime Phase-I diagnostic

Production baseline: `d12f260`, complete source digest
`1abe1ec7943e8736581d61b5f4b7a04ac5d1c5184148df0f7d7adad4be41d73c`.
This follows the [bounded native recovery](representable-point-recovery.md).
The experiment increases only the solver time budget from 300 to 900 seconds.
PFI/native/80, Float64, primal steepest-edge and the isolated adaptive pricing
plus perturbation policy remain unchanged. The original-LP retry stays disabled
so the first failure is visible. Julia 1.13.0 on aarch64 uses one Julia thread
and one BLAS thread, guarded by the existing 8-GiB virtual-memory limit and
available-memory/swap thresholds. The outer wall budget is 1,140 seconds.

## Extended run

The run ends before the requested limit: NUMERICAL_ERROR at iteration 19,222,
523.065 seconds, 3,936 refactorizations and 103,966 rejected pivot candidates.
The reason is `primal point could not be certified`. There is no phase transition.
The guard does not terminate the process.

All thirteen shared sampled pivot observations from iteration 2,000 through
14,000 exactly match the previous 300-second run in objective, infeasibility,
pricing and perturbation levels. The subsequent samples show substantial further
auxiliary-objective reduction:

| Iteration | Solver seconds | Working auxiliary objective | Stored primal infeasibility |
| ---: | ---: | ---: | ---: |
| 14,000 | 268.61 | 589,324.09259 | 0 |
| 15,000 | 305.08 | 586,148.15793 | 0 |
| 16,000 | 355.99 | 580,848.95651 | 0 |
| 17,000 | 407.33 | 572,973.84054 | 0 |
| 18,000 | 459.32 | 552,811.15271 | 0 |
| 19,000 | 510.00 | 232,004.07271 | 0 |

These are sampled pivot events of the perturbed auxiliary LP, not returned
original-LP solutions or proof of eventual convergence. The terminal workspace
is explicitly uncertified: auxiliary objective 228,386.46937, stored primal
infeasibility 2.27310e-5 across fourteen basic coordinates. It must not be treated
as an achieved feasible objective bound.

The adaptive trace still contains one bound perturbation, nine closed pricing
trials and seven productive returns, with no new intervention after the previous
run's last sample. The ordering validators find no overlap. There is no precision
boost. Ninety-three of ninety-four joint projection attempts are accepted; the
last attempt fails. The observed barrier is another numerical point-certification
failure following continued progress, not a return to the earlier objective plateau.

## Reconstruction-only inspection

The portable terminal snapshot has fourteen bound-infeasible basic coordinates
and no bound-infeasible nonbasic coordinates. Its stored row equations pass.
Invoking recovery without a prediction rejects at local interval construction
and restores the point. This is deliberately recorded as a reconstruction-only
probe, not a replay of the actual prediction-anchored recovery. The actual run's
attempt counter proves it reached the projection stage. A targeted capture is
therefore required to inspect the prediction and failed sweeps.


## Actual pivot and recovery replay

The targeted capture reproduces the entire numerical event trace and event counts,
ending at the same iteration and point after 525.678 seconds. The preserved full
workspace replays the single failing pivot with identical ordered basis, states
and terminal primal vector. It enters activity x59881, leaves structural x8504,
and has zero step with pivot 0.924529571. The pre-pivot point passes the complete
working-LP certificate. Its reconstruction already has larger bound errors before
this pivot; those reconstruction errors are not newly created by the zero step.

The pivot prediction respects stored variable bounds, but fails model/equation
checks on rows 25,691, 25,692 and 25,695. The actual joint recovery uses prediction
as its anchor. After sweep two only row 25,695 remains invalid: its model-bound
excess is 3.83215e-21. Sweeps three through eight repeat this row error. Stored
bounds and all equations pass, nonbasic values remain unchanged, and the rejected
trial restores the original reconstruction. The maximum movement from prediction
is approximately 1e-7, well inside the existing locality budget.

## Exact incompatibility of the fixed nonbasic assignments

A diagnostic search of the 33 by 33 representable neighbors of basic structural
coordinates x8507 and x8508 finds no feasible witness. This finite search alone
would not establish infeasibility. A separate exact calculation does:

After the pivot, rows 25,695 and 25,697 have identical coefficients over **all**
basic structural variables, and both fixed nonbasic structural contributions
are exactly zero. Their common expression is
`y = -q(1.07184324)*(x8507+x8508)`, where `q` denotes the exact rational value
of the stored Float64 number. Two necessary certificate inequalities are:

- Working model lower bound of row 25,695:
  `y >= q(-1.6999999999999998e-6) - q(1e-7)`.
- Equation tolerance around the fixed nonbasic activity of row 25,697:
  `y <= q(-1.9e-6) + q(1e-7)`.

The required lower endpoint exceeds the required upper endpoint by exactly
`1/4722366482869645213696`, approximately 2.11758e-22. This contradiction uses
the original certificate tolerance, before projection interior margins or
locality limits. No choice of the basic variables can satisfy it while the
captured nonbasic assignments remain fixed. More projection sweeps, a larger
locality radius or higher arithmetic precision cannot resolve that restricted
problem. This is **not** an infeasibility certificate for the original LP or the
whole perturbed LP.

The zero-step transition changes x8504 from -9.221159309491286e-8, a tolerated
violation of its zero lower bound, to exactly zero. Retaining the pre-pivot point
with the new basis states passes the complete certificate. Relative to the failed
recovery's nonbasic assignments, only x8504 changes in this witness. Thus the
bound assignment, rather than a lack of projection iterations, is the immediate
obstacle to retaining a certified point.

## Counterfactual transition and next implementation boundary

The existing `_primal_bound_snap_feasible` guard accepts the captured transition.
A process-local diagnostic variant extends the existing tolerated-row-value
preservation rule to structural coordinates, using their original column bounds
or the owned working bounds under perturbation. It changes no production files.

On the captured workspace, the baseline again returns NUMERICAL_ERROR. With the
diagnostic variant, the **same captured basis exchange** completes at iteration
19,222, the primal vector is bitwise identical to the pre-pivot vector, x8504 keeps
its tolerated value, and the complete certificate passes. This is one-pivot
counterfactual evidence, not a continued driver run or a production-ready fix.

The next implementation should address certified point preservation during
zero-step structural bound transitions in the core, with explicit regression
coverage of nonbasic reconstruction, working-bound ownership, fixed variables
and positive steps. The diagnostic variant is broader than that single case;
its scope and invariants need validation before promotion. Adaptive pricing and
perturbation scheduling remain unchanged. No new whole-project, external-matrix
or medium result is claimed in this diagnostic-only step.

## Reproduction and retained evidence

Run each Julia payload separately through the existing guard, with one Julia
thread and one BLAS thread. The two full-run payloads use a 900-second solver
limit and 1,140-second outer wall limit. Local inspection/probe wall limits are
180–360 seconds. Do not overlap Julia processes.

```sh
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_one_first_failure.jl runtime primal both 900 /tmp/runtime-representable-long
python3 diagnostics/adaptive-degeneracy/reproduce/analyze_extended_runtime.py /tmp/runtime-representable-long.toml diagnostics/adaptive-degeneracy/results/representable-point/runtime-representable-anchor.toml /tmp/runtime-representable-long-summary.json
julia --project=. diagnostics/adaptive-degeneracy/reproduce/inspect_joint_failure.jl /tmp/runtime-representable-long.bin /tmp/runtime-representable-long-point
julia --project=. diagnostics/adaptive-degeneracy/reproduce/capture_extended_runtime.jl runtime primal both 900 /tmp/runtime-extended-capture
julia --project=. diagnostics/adaptive-degeneracy/reproduce/inspect_extended_runtime.jl /tmp/runtime-extended-capture /tmp/runtime-extended-inspection.toml
julia --project=. diagnostics/adaptive-degeneracy/reproduce/probe_extended_pair.jl /tmp/runtime-extended-capture /tmp/runtime-extended-inspection.toml /tmp/runtime-extended-pair-proof.toml
julia --project=. diagnostics/adaptive-degeneracy/reproduce/probe_extended_transition.jl /tmp/runtime-extended-capture /tmp/runtime-extended-transition.toml
python3 diagnostics/adaptive-degeneracy/reproduce/validate_extended_runtime.py
```

Use fresh output prefixes when repeating the experiments. Committed text evidence
is in [results/extended-runtime](results/extended-runtime/). Full logs, mathematical
and one-pivot snapshots, sweep vectors, interval context, the diagnostic method
and as-run scripts are retained in `.superpowers/adaptive-degeneracy/extended-runtime/`,
with hashes in the committed local artifact manifest. The exact rational checks
are independent diagnostics; the solver and trial point updates use Float64.

## Implemented follow-up

The subsequent [structural-bound retention change](structural-bound-values.md)
implements and tests the proposed core boundary. Its new long-run trajectory
supersedes this diagnostic baseline for current behavior; the captured failure
and exact incompatibility proof above remain baseline evidence.
