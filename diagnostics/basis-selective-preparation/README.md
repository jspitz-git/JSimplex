# Selective preparation of triangular updates

Baseline: `dbf3cc0`. The public `forward_solve!` API still prepares reusable
spikes. The legacy solver now requests preparation explicitly for entering
columns; weight solves, recomputation and residual corrections skip its copies
and finite scans. Auxiliary solves invalidate provenance before overwriting a
prepared destination, including rounded-equal results. Generic/exact arithmetic
and PFI retain their existing solve paths. Adaptive preparation is unchanged.

Entering-column intent is propagated through primal/dual pivots, postsolve basis
projection, crash candidates and accepted artificial-variable removal. Candidate
screening during artificial removal remains ordinary because the accepted column
is solved again. No tolerance or precision change is included.

## Initial paired histories (before the cache-lifetime follow-up)

`reproduce/paired.jl` compares two FTRANs, one update and one BTRAN for 320 recorded
exchanges, with alternating measurement order and the first exchange excluded as
warmup. Each case has three repetitions, one Julia thread and one BLAS thread,
Julia 1.13.0 on Linux aarch64. Baseline preparation is used for both FTRANs;
the candidate prepares only the entering-column FTRAN. Directions, auxiliary
solutions, transpose solutions, packed coefficients, permutations and update
records are exactly equal. Independently scaled matrix residuals are checked at
20, 80, 160 and 320 exchanges.

Median candidate/baseline total time ratios (lower is better):

| History | FT | SS | BG |
| --- | ---: | ---: | ---: |
| runtime at iteration 30,000 | 0.990 | 1.006 | 0.948 |
| runtime at iteration 40,000 | 0.985 | 0.999 | 0.965 |
| early medium, 360,982 rows | 0.903 | 0.675 | 0.797 |

The two-FTRAN time alone fell by about 0.7–2.1% on runtime histories and 9.7–11.5%
on early medium. The larger total changes on medium include downstream timing
effects; update arithmetic was not changed by this feature. These are fixed
histories, not full-solver speedups, and small differences can be measurement
noise. No claim of a complete medium solve is made.

## Verification

Focused triangular and pipeline regression checks passed (33,808 assertions).
Final affected-path checks after review fixes passed 1829 assertions under
`--compile=min`, including the automatic-pricing integration file that stalled
in LLVM under normal compilation. Selective preparation is explicitly restricted
to legacy options, including when an adaptive policy disables hypersparsity. A review found two
residual-correction sites still preparing updates; a new regression failed on all
three triangular managers before the fix and passed afterward. Independent review
also checked public compatibility, alias handling and optional entering sites.

The full project entry point was attempted with normal compilation and a
900-second limit. It did not finish: LLVM was compiling the multi-type automatic
pricing integration test when the time limit terminated the process (exit 137).
No assertion failure was printed. This does not establish a full-suite pass or
attribute the compilation duration to this change; see `results/project-tests-limited.txt`.
All 80 external solves passed 245 assertions: afiro, adlittle, pk1, flugpl and
fast0507, primal/dual, FT/SS/BG/PFI, native/Markowitz. Every result was OPTIMAL,
matched the independent objective and passed original-problem primal feasibility.

Retaining the entering spike across more auxiliary solves can change full-solver
trajectories. In native dual fast0507, FT used 6,211 iterations and SS 7,528;
the previous committed diagnostic report recorded 6,012 and 6,237 respectively.
With Markowitz, SS used 6,868 versus the earlier 5,752. These are successful solves
but an iteration regression on this workload. Primal FT/SS iteration counts match
the earlier report. Historical wall times are unpaired and are not a controlled
whole-solver performance comparison. The optimization is motivated by avoiding
unneeded preparation and the larger-basis measurements, not a universal LP speedup.
Raw paired results, source hashes and input hashes are in `results/replay`.

## Reproduction

Use the project environment with dependencies instantiated. During source
experiments the local PrecompileTools workload preference was disabled; timing
runs used ordinary compilation, while pure correctness probes used
`--compile=min`. The latter timings are not performance evidence.

```sh
julia --project=. diagnostics/basis-selective-preparation/reproduce/focused.jl
JSIMPLEX_BASELINE_SOURCE=/path/to/dbf3cc0/src JSIMPLEX_BASELINE_REVISION=dbf3cc0 \
  julia --project=. diagnostics/basis-selective-preparation/reproduce/paired.jl \
  /fresh/output/directory /path/to/history.bin
julia --project=. diagnostics/basis-selective-preparation/reproduce/external.jl \
  diagnostics/basis-selective-preparation/reproduce/external-inputs.toml \
  /fresh/output.toml
```

The external manifest identifies prepared local inputs by SHA256 and original
NetLib/MIPLib paths. Adjust the prepared paths for another machine, retaining
input hashes and reference objectives. Historical basis recordings are local
binary diagnostic data, not portable source fixtures.

## Cache-lifetime follow-up

End-to-end runtime validation exposed a regression missed by short fixed-pivot
replays: retaining entering spikes through arbitrarily many auxiliary FTRANs
changed rounding and the cleanup trajectory. In the combined production stages
1–3, the retained-cache run hit 900 seconds after 102,579 iterations. A diagnostic
control changing only ordinary-solve cache eviction reached the certified optimum
51,425,691.76210457 in 62,939 iterations and 317.834 seconds, matching the old
iteration count. These are separate runs, not a precise paired speed estimate.

The follow-up preserves the original two-slot advancement on every FTRAN while
still omitting auxiliary spike/direction copies and finite scans. The evidence
above supersedes the earlier decision to accept extended cache lifetime. Historical
replay/corpus files remain evidence for the initial revision, not for this follow-up.
A new regression compares three auxiliary solves against public FTRAN for every
triangular manager in Float32/Float64, checking eviction, bit-identical outputs
and update coefficients, and original matrix residuals. It failed 27 assertions
on the initial implementation before the fix. Full-runtime control records are
in results/cache-lifetime; the control uses the later fused kernels and is explicitly
identified as such in the source hashes.

After the fix, all 33,919 focused assertions passed under `--compile=min`, including
the 96-assertion lifecycle regression. Independent review found no blocking defect.
