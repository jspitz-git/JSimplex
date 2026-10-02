# Longer runtime after structural point retention

This follows [certified structural values across zero primal steps](structural-bound-values.md).
The production baseline is `47d06ff`, with complete source digest
`d338c92dd9e92c5064c4621291796bf3808341aa7d56668ff931d34452dcc6d4`.
No production code changes are included in this experiment.

## Controlled extension

The solver limit increases from 900 to 1,800 seconds. The experiment is a fresh
solve from the original input, not a continuation from a serialized factorization
or adaptive checkpoint. Float64, primal steepest-edge, PFI/native/80, the one-million
iteration budget and the isolated policy remain unchanged. Only stagnation
monitoring, adaptive pricing and perturbations are enabled, with the same
internal Phase-I construction. The independent weak-pivot preference and the
original-LP retry remain disabled by the existing hashed diagnostic overrides.

The input is `/home/jspitz/mps/runtime.mps`, SHA-256
`d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68`.
Julia 1.13.0 on aarch64 uses one Julia thread and one BLAS thread. The existing
guard limits virtual memory to 8 GiB and stops only its owned process group if
available RAM falls below 6 GiB or swap usage exceeds 1 GiB. Its outer wall limit
is 2,040 seconds. Local precompilation preferences remain disabled.

The comparison checks all shared sampled events, including objective,
infeasibilities, pricing state and perturbation state. Timings and process-local
object identities are deliberately excluded. A `phase_primal` event following
Phase I establishes the transition to the original objective of the reduced
model; successful original-input postsolve certification is a separate endpoint.
Only an OPTIMAL returned solution with the original-input feasibility check can
support a full-solve success claim. Final workspace observations at other
terminations remain explicitly uncertified.

## Longer-run result

All **111 shared trace events, including 77 completed-pivot samples**, match the
previous run exactly in the compared numerical and policy fields. The solve
then continues reducing the auxiliary objective:

| Iteration | Solver seconds | Auxiliary objective | Stored primal infeasibility |
| ---: | ---: | ---: | ---: |
| 77,000 | 920.74 | 812.97804633 | 0 |
| 80,000 | 971.13 | 529.48539802 | 0 |
| 85,000 | 1090.48 | 345.56623804 | 0 |
| 90,000 | 1160.08 | 268.31765684 | 0 |
| 95,000 | 1235.06 | 176.32549043 | 0 |
| 99,000 | 1276.63 | 44.22079381 | 0 |
| 100,000 | 1287.65 | 37.28928793 | 0 |
| 101,000 | 1299.01 | 22.77335207 | 0 |
| 102,000 | 1309.94 | 1.07578269 | 0 |

The run ends with **NUMERICAL_ERROR at iteration 102,446 after 1,314.768 seconds**,
with 25,475 refactorizations and 60,103 rejected candidates. The reason is
`artificial removal could not be completed`. There is no time-limit or guard
termination. No Phase-II event or original-input solution is reached.

The eight pricing trials still comprise seven productive returns and one
expiration, with no open trial. No new trial, perturbation, joint projection or
precision boost occurs in the additional interval. The observed obstacle is a
numerical failure at the phase boundary, after substantial further objective
reduction, rather than a repeated objective plateau.

## Boundary localization and its limits

The error occurs inside the final transfer from the auxiliary workspace to a
fresh workspace for the reduced original model. This follows from the existing
control flow and trace dimensions:

- The reported error can only be reached after the auxiliary optimizer returns
  OPTIMAL, its auxiliary optimality certificate passes, and the finite artificial
  sum does not exceed the primal tolerance. These are control-flow deductions;
  the exact final auxiliary sum was not logged.
- No `artificial_removed` event is recorded. The final observed workspace has
  31,615 structural columns instead of the auxiliary 34,186, with the same 28,453
  rows. The fresh workspace is created only after the artificial-exchange loop;
  consequently no artificial remained basic at that boundary.
- The fresh reconstruction reports total basic bound violation 1.981218994982207e-5
  across ten coordinates. This fails the `_start_primal_feasible` criterion;
  the trace does not establish whether earlier checks also fail. The
  auxiliary solution is not adopted into the original workspace.

The final observed dot product, 61,547,897.15814, belongs to this uncertified
reconstruction with the original reduced-model costs. It is neither a feasible
objective bound nor a returned original-input solution. It must not be compared
with the preceding auxiliary objective as a jump within one objective function.
The earlier dual reference for the original input is 51,425,691.762103125; this
experiment never reaches an endpoint that could be compared with it.

The existing failure hook captures failed auxiliary optimization, not failed
basis export after auxiliary optimality. Thus this run produces no mathematical
or full-workspace snapshot of the transfer point. The trace localizes the failure,
but does not identify which particular retained values or reconstruction errors
cause the runtime transfer to fail.

## Portable transfer control

A diagnostic-only control reuses the two-row structural-bound fixture and adds
an exactly zero nonbasic artificial column. The auxiliary point passes the full
point and optimality certificates; its mapped structural point also passes
original-model feasibility. There is no basic artificial to pivot out.

The existing `remove_artificials!` rejects all sixteen cases: Float32/Float64,
lower/upper bounds, and four basis managers. The original basis and primal vector remain unchanged; consumed work counters
are retained. A controlled alternative copies the mapped primal point along with
its basis. Copying nonbasic values alone is insufficient: fresh reconstruction
still violates a basic bound. Passing the mapped basic candidate to the existing
bounded native `_finish_legacy_primal_point!` succeeds in every case, preserves
the mapped point bitwise, and passes both the complete point certificate and
original-model feasibility. All **192 assertions** pass with `--compile=min`.

This establishes a portable defect in the transfer path and a viable local
recovery mechanism. It is not a replay of the runtime transfer and does not prove
that this mechanism alone will repair runtime. No production change is promoted
in this diagnostic step. The next investigation should capture the actual
transfer point and validate mapped-point completion against it, including the
effect of possibly nonzero nonbasic artificials and the original-model certificate.

## Reproduction and retained evidence

Run Julia payloads sequentially through the existing guard and one-thread
wrapper. Use a 2,040-second outer wall limit for the long run and 240 seconds
for the portable control. Use fresh output paths on repetition.

```sh
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_one_first_failure.jl runtime primal both 1800 /tmp/runtime-structural-1800
julia --project=. --compile=min diagnostics/adaptive-degeneracy/reproduce/probe_structural_phase_transfer.jl /tmp/structural-phase-transfer.toml
python3 diagnostics/adaptive-degeneracy/reproduce/analyze_structural_continuation.py /tmp/runtime-structural-1800.toml diagnostics/adaptive-degeneracy/results/structural-values/runtime-structural.toml /tmp/runtime-structural-1800-summary.json
python3 diagnostics/adaptive-degeneracy/reproduce/validate_structural_continuation.py
```

Committed text results are in [results/structural-continuation](results/structural-continuation/).
The complete trace log, measured-source metadata and as-run scripts are retained
under `.superpowers/adaptive-degeneracy/structural-continuation/`, with hashes in
the committed artifact manifest. The validator checks current production source,
exact common-prefix agreement, intervention ordering, the portable control and
retained-file hashes. The earlier structural-retention validator is also rerun
against the unchanged production source. No new external matrix or whole-project
suite result is claimed in this diagnostic-only step.
