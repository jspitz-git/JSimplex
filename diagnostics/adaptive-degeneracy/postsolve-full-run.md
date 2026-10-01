# Fresh runtime verification after the postsolve correction

**The fresh solve fails.** This result does not reproduce the successful
[saved Phase-II continuation](postsolve-hints.md) as a complete solve from MPS.
Production commit: `526ceb1`; source SHA-256:
`05cdf44e84749dd1bf94f2d02be60900f06cf95219c64c180eae11504a808725`.
No production code was changed during or after this verification.

## Configuration and scope

The process reads `/home/jspitz/mps/runtime.mps` from scratch, verifies SHA-256
`d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68`,
and runs presolve, scaling and primal simplex. No saved workspace is loaded.
The existing runner warms common methods on the small afiro fixture before
reading runtime; its reported solver time excludes that warmup.

The configuration matches the previous isolated experiment: Float64,
steepest-edge pricing, PFI, native refactorization, interval 80, adaptive strategy,
and integrality relaxation. Adaptive stalling, pricing and primal/dual
perturbation switches and the internal Phase-I construction are enabled; all
other numerical switches are disabled. The same diagnostic method overrides
disable the separate weak-pivot preference and original-LP retry. Phase failure
observation and final snapshot saving remain observational. The production
phase-export and postsolve methods are used without replacement.

The solver budget is 7,200 seconds and 1,000,000 iterations, with a 7,500-second
outer wall guard. Julia 1.13.0/aarch64 uses one Julia and one BLAS thread. The
existing wrapper limits virtual memory to 8 GiB and stops only its owned group
below 6 GiB available RAM or above 1 GiB swap. This was the only numerical Julia
process. No excluded large model was solved or factored.

## Result

| Item | Observed value |
| --- | --- |
| Status | `NUMERICAL_ERROR` |
| Reason | `artificial removal could not be completed` |
| Completed iterations | 82,000 |
| Refactorizations | 1,035 |
| Solver elapsed time | 597.687718492 s |
| Completed pivots / flips | 81,697 / 303 |
| Rejected candidates | 14 |
| Peak process RSS | 1,813,778,432 bytes |
| Phase II / original postsolve reached | No / no |
| Original optimum certified | No |

The process exits normally after writing the numerical-error result. Neither
memory pressure nor either time limit terminates it. Cumulative allocations are
26,130,009,832 bytes; this is not simultaneous memory use.

The final auxiliary-model sample at iteration 82,000 has objective
`-2.6783022201066765e-8`, with reported primal and dual infeasibility zero.
The failure branch is reached only after the auxiliary optimizer returns OPTIMAL,
the auxiliary optimality check passes, and its artificial sum is within the
existing tolerance. `remove_artificials!` then returns false. This routine also
performs the final original-dimension workspace export and certification, so the
message alone does not identify which internal check failed.

The last observed workspace has 28,453 rows and 31,615 columns, rather than the
auxiliary model's 34,186 columns. Its observed original-cost value is
59,070,418.23667619, with zero reported primal infeasibility and large dual
infeasibility. This observation is explicitly uncertified; it is not a returned
solution or an original-input objective claim. The detached snapshot is retained
for targeted export diagnostics and is not an exact outer-driver checkpoint.

All eight observed temporary Dantzig trials return productively to steepest-edge.
There is no recorded bound perturbation, phase-II start, cleanup or original-LP
restart. Precision boosting and LP refinement remain disabled.

## Relation to the earlier trajectory

The old full prefix at `f43b4ef` and this run have identical sampled objectives
at iteration 1,000. At 2,000 they differ by one displayed rounding unit, and by
3,000 they differ materially (604,294.9190404785 versus 604,340.2369458212).
The fresh run therefore reaches a different Phase-I export state. Successful
export and postsolve of the old saved state do not establish robustness on this
new trajectory. The full test is evidence that runtime remains unresolved from
scratch under the isolated configuration.

The next focused investigation is the saved export failure, including the
native primal/dual reconstruction checks. There is no reason to repeat this
entire prefix before inspecting the retained state. No additional correction is
included in this verification commit.

## Reproduction and artifacts

Under the existing memory guard:

```sh
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_transfer_recovery_runtime.jl runtime primal both 7200 /tmp/runtime-postsolve-full
```

Text evidence and hashes are in [results/postsolve-full-run](results/postsolve-full-run/).
The 19-MiB detached workspace and exact runner/wrapper copies remain in
`.superpowers/adaptive-degeneracy/postsolve-full-run/`. The committed artifact
manifest records their hashes. The runner itself is unchanged from the already
committed reproduction used for the preceding fresh prefix.

The subsequent [coupled homogeneous recovery](phase-components.md) identifies
and fixes this specific export failure. A new full solve with the same sampled
Phase-I trajectory then reaches OPTIMAL; this report remains the evidence for
the earlier failure before that correction.
