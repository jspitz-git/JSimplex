# Fused triangular solve stages

Baseline: e8e6194. Compose compiled row coordinates, packed-upper coordinates and
basis column order during vector transfers. Preserve elimination order and save
prepared spikes in logical coordinates, including copied BG factors whose upper
coordinates have been rebased. BTRAN keeps backend input separate when callers
use spike scratch as destination. Read the ordered last diagonal entry directly,
with the previous lookup as fallback; no diagonal metadata is maintained.

## Validation

Affected triangular/hypersparse/selective/metadata tests: 33,155 assertions passed.
Final focused additions: 436 passed, including empty factors and the prepared
spike of a copied BG factor. Independent review found no blocking defect; its
coverage suggestion was incorporated. Float32, Float64, BigFloat, aliased input,
work RHS, spike destination and nonfinite inputs are exercised.

Three paired repetitions of 320 exchanges per manager/history agree exactly in
solutions, packed coefficients, permutations and history. Independent scaled
residual checks pass at 20/80/160/320 updates. First exchange excluded for warmup;
Julia 1.13.0 Linux aarch64, one Julia/BLAS thread. Ratios are median paired candidate
/ baseline, including total update + two FTRAN + BTRAN, or the two FTRAN alone.

| History | Manager | Total ratio | FTRAN ratio |
|---|---|---:|---:|
| ft-late.toml.history.30000.bin | BartelsGolubFactorization | 1.008 | 0.951 |
| ft-late.toml.history.30000.bin | ForrestTomlinFactorization | 0.975 | 0.955 |
| ft-late.toml.history.30000.bin | SuhlSuhlFactorization | 0.980 | 0.969 |
| ft-late.toml.history.40000.bin | BartelsGolubFactorization | 0.961 | 0.957 |
| ft-late.toml.history.40000.bin | ForrestTomlinFactorization | 0.967 | 0.969 |
| ft-late.toml.history.40000.bin | SuhlSuhlFactorization | 0.988 | 0.974 |
| medium-history.bin | BartelsGolubFactorization | 0.859 | 0.968 |
| medium-history.bin | ForrestTomlinFactorization | 0.913 | 0.887 |
| medium-history.bin | SuhlSuhlFactorization | 0.705 | 0.889 |

These are fixed-history measurements, not whole-solver speedups. Large-basis
update timing varies despite unchanged update arithmetic; total differences
should not be attributed solely to instruction count in the changed solve loops.
Background editor compilation was present during parts of this run. Alternating
paired timing reduces but cannot eliminate host noise. Raw samples are retained.

The predecessor's normal-compiled full-project attempt timed out in LLVM
compilation; this stage does not claim a full-project pass. The focused suite
covers the affected kernels and generic precision paths.

Reproduction: reproduce/focused.jl; reproduce/paired.jl takes an output directory
and history paths, with JSIMPLEX_BASELINE_SOURCE, JSIMPLEX_BASELINE_REVISION and
JSIMPLEX_PROBE_REPEATS environment variables. External runner takes the predecessor
external-inputs.toml and a new output path. Histories are identified by hashes.

External native-backend corpus: all 40 primal/dual solves across FT/SS/BG/PFI
passed 125 assertions, including original-LP certificates and reference objectives.
All iteration counts equal the selective-preparation predecessor. This is not a
controlled wall-time comparison. Markowitz is covered by focused kernel tests
and the predecessor external corpus, not a repeated external corpus here.
