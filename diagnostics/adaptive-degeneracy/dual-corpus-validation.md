# Paired dual verification after the phase-context correction

This extends the [postsolve phase-context verification](dual-entry-phase.md)
from its predominantly primal corpus to the corresponding dual configurations.
It compares `a7f1fac9a608e2ad5f1eb77f2e4abb8984ad9548` (before the correction)
with `d5390a221e8c4c8edd0fe2215beb53e05523c737` (after the correction).
No production source or solver policy is changed for this verification.

## Selection and controls

Start with the 30 jobs in `results/stocfor2-point/jobs.toml`, change only
`algorithm` to `dual`, and deduplicate by model, reader, manager and permutation
seed. The two existing native/JuMP dual `mod010` jobs duplicate converted primal
jobs, leaving **28 configurations over nine models**:

- NetLib: `degen2`, `degen3`, `boeing1`, `scsd6`, `cycle`, `stocfor2`.
- MIPLib LP relaxations: `mod010`, `p0201`, `misc07`.
- Readers: 12 native, 9 JuMP, 7 explicitly permuted.
- Managers: 22 PFI; two each for Forrest–Tomlin, Suhl–Suhl and Bartels–Golub.
  All four managers cover permuted `mod010` seed 1 and native `scsd6`.
  Additional PFI permutations use seeds 2, 17 and 29.

Each job retains Float64, steepest-edge pricing, native factorization, an
80-update refactorization interval, 1,000,000 iterations and a 90-second solver
limit. Only stagnation monitoring, adaptive pricing, primal/dual perturbations
and Phase I are enabled among the numerical switches. The separate primal
weak-pivot preference and original-LP retry remain disabled by the existing
process-local diagnostic instrumentation. Other adaptive functions, including
precision boosting and optional feasibility recovery, remain disabled.

Use the same `broad_corpus.jl` instrumentation and the same hashed inputs and
HiGHS references on both commits. Native/JuMP/permuted models must agree exactly
after mapping rows and columns by name. An `OPTIMAL` result is counted as
verified only if the returned point passes both the reader-model and original
unscaled primal checks, and its objective agrees with the independent reference
(`rtol=1e-8`, `atol=1e-7`).

Both processes run serially with Julia 1.13.0, one Julia thread and one BLAS
thread, normal compilation and `precompile_workload=false`. Each uses the
existing 8 GiB virtual-memory limit, 6 GiB available-RAM floor, 1 GiB swap ceiling
and a 3300-second whole-process wall guard. This outer guard accommodates
compilation and the maximum aggregate per-model budget; it is not the per-model
limit. No other numerical process runs concurrently.

## Reproduction

Retain the existing broad-validation input files and environment. Export
`Project.toml`, `src` and `test/fixtures/solver/afiro.mps` from `a7f1fac` into a
separate local directory with `git archive`. Copy local preferences into it.
Copy the existing broad-validation environment and adjust only its local
JSimplex source path in `Project.toml` and `Manifest.toml` to this export. This
avoids changing the active checkout. Do not commit either local manifest or
preferences.

For each environment, run the following through the established Julia wrapper
and memory guard, with a distinct output prefix:

```text
julia --project=ENV diagnostics/adaptive-degeneracy/reproduce/broad_corpus.jl \
  diagnostics/adaptive-degeneracy/results/broad-validation/inputs.toml \
  diagnostics/adaptive-degeneracy/results/broad-validation/references.toml \
  diagnostics/adaptive-degeneracy/results/dual-corpus/jobs.toml OUTPUT_PREFIX
```

Compare the completed TOML reports with:

```text
python3 diagnostics/adaptive-degeneracy/reproduce/compare_dual_corpus.py \
  diagnostics/adaptive-degeneracy/results/dual-corpus/base.toml \
  diagnostics/adaptive-degeneracy/results/dual-corpus/candidate.toml \
  diagnostics/adaptive-degeneracy/results/dual-corpus/comparison
```

The comparator checks configuration identity, input/reference identity, reader
mapping, scalar environment, instrumentation hashes and policy equality before
comparing outcomes. It also retains diagnostic-event and coverage differences.
See `results/dual-corpus/provenance.json` for exact commit and file hashes.

## Results

Both commits complete **28/28 verified optima**, for **56 completed whole-model
solves** under normal compilation. There are no numerical errors, time limits,
harness exceptions, failed primal certificates, objective mismatches or
original-LP retry attempts. The largest objective relative error against HiGHS
is `5.827013230329738e-12` on both commits.

Every pair has exactly equal status, iteration count, refactorization count,
recorded phase sequence and objective. All diagnostic-event counts and repair
coverage counts also agree. See the [paired table](results/dual-corpus/comparison.md)
and machine-readable `comparison.json`; full reports and logs are retained
beside them. The observed process peak RSS is about 1765 MiB for the base and
1806 MiB for the candidate. Neither memory guard fires.

Some representative unchanged iteration counts:

| Model | Native PFI | JuMP PFI |
| --- | --- | --- |
| degen2 | 534 | 548 |
| degen3 | 2075 | 2036 |
| cycle | 571 | 634 |
| stocfor2 | 1627 | 1626 |
| scsd6 | 288 | 288 |

These cases exercise phase boundaries, not just ordinary dual pivots. Each run
records a primal phase after cleanup; nine runs record an auxiliary phase.
Native and JuMP `cycle` each record one Dantzig switch and one progress-triggered
return to steepest-edge pricing. Those events and their counts are unchanged.
The phase-event records do not establish coverage of every direct legacy cleanup
branch; the portable regressions accompanying the correction cover those paths.

None of these dual runs enters the local/component phase-transfer repair.
Consequently, this result establishes no additional coverage of that repair's
numerical corner cases. The existing primal evidence remains necessary.

## Interpretation and next coverage gap

No additional core defect or regression is exposed by these dual counterparts,
so there is no production change in this verification commit. In combination
with the previous 30-configuration result, the selected corpus now covers 56
unique configurations: 28 primal and 28 dual (two dual jobs were already present
in the earlier set). This is still only nine underlying models, not 56 distinct
LPs, and the non-PFI managers cover two configurations each per method.

The runs use the isolated adaptive policy described above. They are not a
full-default-policy validation, a legacy-strategy validation, a full project
unit-suite pass or a speed benchmark. `runtime.mps` and `medium.mps` are not
rerun; this result does not establish their convergence.

The next useful expansion is the remaining models from the broader 33-model
manifest, starting with dual PFI through both readers under the same controls.
Keep presolve failures, bounded stagnation and numerical core failures separate.
In particular, the previously observed `pilotnov` presolve discrepancy remains
outside this nine-model phase-dispatch verification and is not declared fixed.
