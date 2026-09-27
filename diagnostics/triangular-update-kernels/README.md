# Reusing prepared triangular update spikes

Work based on `17be8a3`, in `fix/triangular-update-kernels`. The user reports
triangular managers still taking over twice the PFI runtime. Allocation
investigation is outside this work.

## Confirmed unnecessary work

The managers represent `B = B0 R^-1 U Q^-1`. A dense entering-column FTRAN
first computes `s = R B0^-1 a`, then solves `U z = s` and permutes `z` to
basis coordinates. Replacement previously reconstructed `s` by multiplying
`U Q^-1 direction`. That multiplication traverses the growing upper factor
and adds a second rounding step to a vector that was already available.

The implementation retains two private prepared spikes for Float32/Float64.
Two slots accommodate the steepest-edge FTRAN between the entering-column
solve and replacement. A slot requires the identical output buffer with
exactly unchanged values and finite direction/spike coefficients. Other or
corrected directions use the original reconstruction. BigFloat and exact
arithmetic retain their original path.

Updates and successful refactorizations invalidate both slots. Factor copies
start without prepared outputs. BTRAN, indexed solves, and pipeline copies
invalidate overwritten destinations, including overlapping views. Internal
scratch cannot publish a prepared output. Failed validation retains the
unchanged factor; a partially completed output cannot publish a prepared spike.
No tolerances, pivot selection rules, precision policy, or refactorization
policy are changed. Avoiding reconstruction changes floating-point rounding,
so old/new simplex trajectories are not expected to be identical.

## Investigation and limits

The initial FT diagnostic prefix reached iteration 48400 in 695.705 seconds,
with status ITERATION_LIMIT. It is not an optimal solution. Production source
was still `17be8a3`; the report's dirty flag came from test/document edits.
The profiler attributed about 44% of sampled execution to replacement.
Histories contain 320 actual exchanges after iterations 30017 and 40097.
The 48000 window did not finish before the prefix limit; the reproducer now
allows 48500 iterations by default and saves incomplete final windows too.

The initial stage replay showed that spike reconstruction and packed row
rotation, rather than elimination alone, dominated replacement. A prototype
moving the eliminated row to dense scratch preserved coefficients exactly but
failed to improve timings consistently and was rejected. A prototype starting
from the backend's actual L/U factors reduced stored entries but was also
slower with the existing update representation. Neither prototype is enabled.

The current representation retains a complete backend LU plus an additional
upper factor. It does not directly update the backend LU. Parity with PFI is
therefore not implied by the manager names; removing reconstruction addresses
one measured cost, not every remaining structural cost.

## Paired replay results

Medians of three alternating runs, 320 recorded exchanges per run. Times are
seconds for replacement alone. The last column includes both the entering
column FTRAN and an intervening weight FTRAN, so it includes cache maintenance.
The comparison uses the same entering columns and basis exchanges, without
an extra cache-warming probe. These percentages are **not full solver gains**.

| Model / starting iteration | Manager | Replacement, original → prepared | Reduction | Reduction including two FTRANs |
|---|---|---:|---:|---:|
| runtime 24017 | FT | 0.639 → 0.371 | 42.0% | 25.6% |
| runtime 24017 | SS | 0.656 → 0.394 | 39.9% | 24.2% |
| runtime 24017 | BG | 1.461 → 0.839 | 42.5% | 31.0% |
| runtime 30017 | FT | 0.799 → 0.398 | 50.2% | 30.5% |
| runtime 30017 | SS | 0.876 → 0.456 | 47.9% | 29.4% |
| runtime 30017 | BG | 1.784 → 1.062 | 40.5% | 29.1% |
| runtime 40097 | FT | 0.866 → 0.490 | 43.4% | 24.3% |
| runtime 40097 | SS | 0.953 → 0.560 | 41.3% | 25.0% |
| runtime 40097 | BG | 2.064 → 1.416 | 31.4% | 23.3% |
| medium 2000 | FT | 3.386 → 2.627 | 22.4% | 12.6% |
| medium 2000 | SS | 2.878 → 2.134 | 25.9% | 13.9% |
| medium 2000 | BG | 4.075 → 3.258 | 20.0% | 12.8% |

The maximum scaled forward/transpose residual over all checkpoints and
managers, including the PFI control, was 1.13e-13; the acceptance threshold was
1e-10. The medium history starts at iteration 2000 and is not a full solve.
Triangular operations still cost substantially more than PFI on this history.

## Full runtime solve

FT at commit `99ba627` completed `runtime.mps` with OPTIMAL status in
844.240 seconds and 62,939 iterations. The original primal solution passes the
solver's feasibility check. Objective 51,425,691.76210457 agrees with the
previous hash-matched PFI result 51,425,691.76210421 (difference 3.6e-7).
Peak RSS was 7.82 GiB. The budget was 1,200 seconds / 1,000,000 iterations.
There was one residual-triggered refactorization, 4,770 successful native
corrections out of 4,777 attempts, and one cleanup phase. The interval remained
80 until iteration 61,456, then briefly increased to 160 and returned to 80
at iteration 61,747.

At iteration 48,000 the new run took 547.021 seconds against 687.640 in the
baseline prefix. This is a roughly 20% shorter prefix, but the pivot trajectory
and effective interval differ: the baseline had increased its interval to 160
at iteration 21,058. A full old/new solver speedup is therefore not established
by these two runs, and neither the full result nor replay establishes parity
with PFI. The old PFI time of 271.741 seconds is from a separate historical run,
not an interleaved control under identical host load.

The final profile still attributes about 39% of sampled execution to
replacement (29,055 of 74,214 task samples). Packed storage/index manipulation
remains substantial. The selected change removes one measured redundant
operation but does not solve the whole structural performance gap.

## Verification

- 19,895 assertions passed in factorization, composed-row, incidence,
  hypersparse, and prepared-spike tests on the final implementation.
- 72 external LP solves (both primal/dual, all four managers) ended OPTIMAL
  with original primal feasibility and independently referenced objective
  checks: 225 assertions passed. Inputs came from NetLib, MIPLib and mps,
  including fast0507. This run preceded the final overlapping-view invalidation
  guard; the guard then passed the targeted numerical and alias tests above.
- The full `-O1 --project=. test/runtests.jl` run did not complete in its
  900-second wall-clock budget. After TERM and a 15-second grace period the
  timeout ended with exit 137. A nonterminating diagnostic stack showed LLVM
  code generation; the termination stack showed LLVM optimization while
  compiling `test/partial_pricing_edge_tests.jl:11`. This is **incomplete
  validation**, not a full-suite pass. The process was confirmed gone; editor
  processes were left untouched. The log and outcome are retained in `results`.
- Read-only review found and helped test stale provenance through BTRAN,
  indexed destinations, alias-copy pipelines, and overlapping views. Final
  review found no remaining blockers.

## Reproduction

Use one Julia process at a time and a 24 GiB virtual-memory ceiling. The local
Manifest and serialized model histories are not repository artifacts. Do not
solve big.mps, largo.mps, or AnyMod.mps. Completion attempts must allow at least
360 seconds. Measurements use Julia 1.13.0 on aarch64 with one Julia/BLAS thread.
The host also has an independently running editor analysis process; paired
kernel measurements are more controlled than separate wall-clock solves.

- `reproduce/capture-late.jl INPUT METHOD OUTPUT ITERATION_LIMIT SECONDS`
  captures real pivot histories and a solver profile with legacy dual,
  steepest-edge, native factorization, and initial interval 80. A finite
  iteration limit denotes a diagnostic prefix.
- `reproduce/compare-prepared.jl OUTPUT_DIRECTORY HISTORY...` compares the
  production path with frozen `17be8a3` FTRAN/replacement routines. It includes
  an intervening weight FTRAN and three repetitions in alternating order.
  At 20, 80, 160, and 320 updates it checks both solve residuals against the
  actual basis. It inspects only output-buffer identities before timing,
  avoiding an extra cache-warming copy. These are replay results, not full LP
  solve times. PFI is included as a control.
- `reproduce/reference-updates.jl` contains the baseline diagnostic kernels.
- `reproduce/verify-factors.jl` runs the focused numerical and provenance tests.
- To capture the medium replay, use
  `diagnostics/simplex-basis-cleanup-performance/reproduce/capture-history.jl`
  with arguments `INPUT OUTPUT 2000 320`.
- The external corpus uses
  `diagnostics/simplex-basis-cleanup-performance/reproduce/prepare-corpus.py`
  and `quick-corpus.jl`, with `JSIMPLEX_CORPUS_MANIFEST` and
  `JSIMPLEX_CORPUS_OUTPUT` pointing to local files. See the committed corpus
  results for input hashes and individual checks.

The prepared-spike feature is commit `99ba627`. The paired replay used that
production implementation before committing it; diagnostic reference routines
are frozen from `17be8a3`.

## Related implementation review

[Comparison with Simplex.jl](simplex-source-review.md) distinguishes its eta
managers from its actual BGTransform implementation and records candidate
optimizations. The user reports BGTransform was extremely slow; it is not
proposed as a wholesale replacement.
