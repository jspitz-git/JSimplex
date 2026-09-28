# Legacy immutable-LU hypersparse experiment

Decision: retain an explicit diagnostic opt-in; do not change production defaults
or add a public option on this evidence. Baseline a1adfb4. The prototype uses the
existing sparse traversal kernels only for immutable base LU, avoiding updated-U
graph rebuilding entirely. Correction upper and row history stay dense. BTRAN-only
and BTRAN+FTRAN variants use input support cutoff 0.1, with native fallback for
dense/nonfinite input, unsupported scale interpretation and sparse overflow.
Copies own traversal scratch; refactorization constructs a new backend before
changing the live factor. Adaptive strategy and non-native/non-Float64 dispatch
remain unchanged. The prototype is not loaded by the package or precompile workload.

## Validation and measurements

321 diagnostic assertions passed, including successive exchanges, FTRAN/BTRAN,
copy ownership, failed/refreshed refactor, nonfinite and actual overflow fallback,
sparse reuse after overflow, unavailable view cached after one attempt, and
legacy-only installation. Independent review found no wrapper correctness defect.

Two alternating paired repetitions, 320 exchanges, each of FT/SS/BG and dense,
BTRAN-only, both, and PFI variants. Warmup uses 32-row factors and asserts actual
sparse execution. Fresh measured factors charge graph creation to the first solve;
all dense/indexed conversion and fallback costs are included. BTRAN has a unit
RHS at the exchanged basis position; FTRAN uses an entering column and dense DSE-like
RHS. BTRAN-only preserves directions exactly. Other modes may round differently;
all independent scaled residual checks pass at 20/80/160/320 exchanges. Maximum
observed scaled residual: 2.1454700906527652e-13.

Julia 1.13.0 Linux aarch64, one Julia/BLAS thread. Ratios below are median paired
whole-bundle times relative to the dense triangular manager, not LP solve speedups.

| History | Manager | BTRAN only | Both | PFI |
|---|---|---:|---:|---:|
| ft-late.toml.history.30000.bin | BartelsGolubFactorization | 1.183 | 1.209 | 0.782 |
| ft-late.toml.history.30000.bin | ForrestTomlinFactorization | 1.261 | 1.282 | 1.004 |
| ft-late.toml.history.30000.bin | SuhlSuhlFactorization | 1.288 | 1.270 | 0.950 |
| ft-late.toml.history.40000.bin | BartelsGolubFactorization | 1.320 | 1.328 | 0.724 |
| ft-late.toml.history.40000.bin | ForrestTomlinFactorization | 1.338 | 1.489 | 0.961 |
| ft-late.toml.history.40000.bin | SuhlSuhlFactorization | 1.344 | 1.468 | 0.935 |
| medium-history.bin | BartelsGolubFactorization | 1.041 | 0.945 | 0.224 |
| medium-history.bin | ForrestTomlinFactorization | 1.006 | 0.952 | 0.223 |
| medium-history.bin | SuhlSuhlFactorization | 0.909 | 1.026 | 0.241 |

On the runtime histories, the whole bundle is 18–34% slower for BTRAN-only and
21–49% slower with sparse FTRAN too. Early-medium results are mixed and noisy;
none supports a universal speed claim. PFI remains substantially faster on this
large mostly sparse early basis. Reusing the immutable graph alone does not solve
the overhead problem: traversal and conversion still outweigh the native solve
savings on runtime. A future sparse end-to-end pipeline would need different
kernels and measured support propagation; this experiment does not rule it out.

An initial diagnostic warmup failed to enter the sparse path and was corrected
after independent review. Those timings were discarded, not used in this table.

## Reproduce / opt in

Run reproduce/check.jl for correctness. Run reproduce/paired.jl with a fresh
output directory and the identified history paths (hashes in results), optionally
JSIMPLEX_PROBE_REPEATS=2. Only the replay copies are needed; excluded large models
are never solved or factorized.

To test the kernel in a dedicated Julia process:

```julia
using JSimplex
Base.include(JSimplex, joinpath(pkgdir(JSimplex), "diagnostics",
    "basis-legacy-hypersparse", "reproduce", "hybrid.jl"))
JSimplex._install_trial_hybrid!(forward=false, cutoff=0.1)
# Subsequent native Float64 legacy solves opt in; restart Julia to opt out.
```

This is a development-only installation into the running module, not a stable API.
The external runner checks five independent dual FT LP trajectories using the
predecessor corpus manifest, original-LP certificates and objective references.

All five independent LP solves passed (20 assertions). Fast0507 used 6,578
iterations versus dense predecessor 6,211; both reached the same certified optimum.
Elapsed times across these separate runs are not a controlled comparison. No full
runtime or medium solve was attempted for this slower experimental mode. The
predecessor broad-project LLVM timeout remains a full-suite validation limitation.
