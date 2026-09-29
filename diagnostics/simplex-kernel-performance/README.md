# Arithmetic-preserving simplex kernel performance

Base revision: `61e8bf972758296e8b0e944ba5fed60bde53bf28`.

CSC tableau-row pricing now checks multiplier/output lengths once before its
indexed loops. The scalar products and their accumulation order are unchanged.
This removes repeated bounds checks without changing working precision, pivot
selection, numerical checks, or adaptive policies. Basis managers are unchanged.

## Numerical equivalence

All **51 paired solves** pass the automated identity comparison (612 field
comparisons): 48 small corpus cases, both algorithms on fast0507, and runtime
dual. Ordered pivot/step traces, periodic full numerical-state hashes, final
primal vectors, objectives, iteration/refactorization counts and all diagnostic
counters match the baseline exactly. Every optimum passes the original-input
primal certificate.

Runtime dual remains `OPTIMAL` at **62,853 iterations**, **793 refactorizations**,
and objective **51425691.762103125**, with no original-LP restart. Its full pivot
trace and checkpoint hashes match, including the native cleanup recovery.
The run has a 600-second solver budget and finishes before that limit. Its
instrumented elapsed time is not used as a performance comparison.

See `results/equivalence.json` and `reproduce/compare.py` for the exact comparison.

## Final production performance

The final same-process kernel comparison uses the original scalar traversal as
its reference. Seven alternating-order warmed samples of 200 calls each give:

| Matrix | Type | Scalar reference (µs/call) | New production (µs/call) | Less time |
|---|---|---:|---:|---:|
| fast0507 | Float32 | 366.23 | 283.35 | 22.6% |
| fast0507 | Float64 | 370.87 | 293.76 | 20.8% |
| runtime | Float32 | 187.20 | 129.75 | 30.7% |
| runtime | Float64 | 192.32 | 140.99 | 26.7% |

Both versions allocate zero bytes in every measured sample; compilation is also
zero. These measurements do not imply the same gain for an entire simplex solve.

Complete fast0507 solves use normal compilation, one full warmup and three
measured repeats without profiling or the trace observer. Every measured sample
has zero compilation time. Medians and ranges are:

| Algorithm | Before median (s) | After median (s) | Before range (s) | After range (s) |
|---|---:|---:|---:|---:|
| Dual | 8.373 | 7.807 | 8.362–8.519 | 7.646–7.841 |
| Primal | 15.108 | 15.038 | 14.880–15.756 | 14.974–15.175 |

Dual takes 6.8% less time in this measurement. Primal's 0.5% median difference is
within the observed variation; no whole-primal speedup is established. Both
versions retain 6,986 iterations/88 refactorizations for dual and 4,923/63 for
primal. All solutions have objective `172.14556667654887` and pass the original
primal certificate. Separate full traces match exactly for both algorithms.
The benchmark harness SHA256 is identical before and after.

## Investigation method

1. Profile the current solver, without repeating completed basis-manager work.
2. Measure a small isolated candidate before changing production code.
3. Verify exact scalar-reference agreement, including cancellation, signed zeros,
   stored zeros, exceptional floating values, and generic arithmetic types.
4. Compare ordered pivot/step traces, periodic full numerical-state hashes,
   final primal vectors, iteration counts, refactorizations, and diagnostic
   counters with the baseline on actual models.
5. Run relevant existing regressions and warmed performance measurements.
6. Commit validated changes; merge and push require a separate user instruction.

All numerical runs are sequential under the existing 8-GiB address-space and
available-memory/swap guard, with one Julia thread and one BLAS thread. Local
precompilation preferences and manifests are retained and excluded from commits.
Excluded large models and their aliases are not solved or factorized.

## Initial evidence

A warmed sampling profile of fast0507 dual (native PFI, steepest edge, legacy,
refactorization interval 80) reaches the optimum in 6,986 iterations and 88
refactorizations. CSC tableau-row pricing appears in 1,200 of 3,745 attributed
samples. Array bounds checks contribute substantially within that traversal.
Sampling adds overhead: the profile time is not an uninstrumented solve timing.

The first candidate moves vector-dimension checks outside the CSC traversal.
Each column retains the exact scalar `value += rho[row] * coefficient` order;
there is no reassociation, fused multiply-add introduction, or skipped zero.

## Isolated candidate measurement

Before modifying the production function, seven warmed samples alternated the
reference/candidate/production order on the original fast0507 and runtime
matrices with deterministic dense multipliers. Each sample executes 200 calls;
all measured samples report zero compilation time and zero allocation.

| Matrix | Type | Original production (µs/call) | Candidate (µs/call) |
|---|---|---:|---:|
| fast0507 | Float32 | 348.52 | 267.78 |
| fast0507 | Float64 | 353.98 | 284.09 |
| runtime | Float32 | 193.81 | 133.66 |
| runtime | Float64 | 198.27 | 142.80 |

These are median kernel times, not complete-solver speedups. The raw records are
in `results/baseline-kernels.toml`; the unchanged scalar oracle also agrees with
the original production performance and results. The numerical test suite
includes an explicit example where introducing FMA would change the answer.

## Reproduction

Run from the checkout root using the existing guarded Julia wrapper. Labels
such as `baseline` and `current` require fresh output paths. The same scripts
are used against the base and changed production source.

- `reproduce/kernel-bench.jl OUTPUT.toml`: normal compilation, isolated warmed
  scalar-reference/candidate/production measurements.
- `reproduce/corpus.jl LABEL`: `--compile=min`, 48 semantic cases: afiro,
  adlittle, flugpl × primal/dual × legacy/adaptive × all four basis managers.
- `reproduce/fast-bench.jl LABEL`: normal compilation, one full warmup and
  three uninstrumented measured solves for each algorithm, followed by a
  separate ordered trace on fast0507. An optional `runtime` argument adds the
  600-second-budget runtime dual trace after these runs.
- `reproduce/measure.jl INPUT ALGORITHM ITERATIONS SECONDS PREFIX trace`:
  standalone trace (normal compilation for large models). Use `profile` for
  sampling without the trace observer.
- `reproduce/regressions.jl`: `--compile=min`, focused pricing/integration and
  numerical recovery regressions. Run the new CSC tests with normal compilation
  as well.
- `python3 reproduce/compare.py`: compare the paired numerical records.

All paths above are relative to this diagnostic directory. The wrapper must
retain the single-thread and memory limits described above. Runtime traces use
at least a 600-second solver budget and may finish earlier at an optimum.

The trace records every completed pivot/flip's entering variable, leaving row,
primal step and dual step, plus iteration/phase offsets. Every 80 iterations and
at termination it hashes the full basis indices/states, primal, reduced costs,
working costs and pricing weights. Final primal vectors and all diagnostic
counts are compared separately. Input SHA256 values identify the external data.
The initial runtime baseline buffered checkpoint bytes before hashing; the final
harness hashes the identical byte stream incrementally to bound diagnostic
memory. Runtime trace allocation/time differences are therefore not performance
measurements. Only the warmed, uninstrumented fast0507 solves support whole-solve
timing comparisons.

## Regression status and existing failures

The focused suite passes **3,401/3,401** checks with `--compile=min`. The new
CSC tests also pass **135/135** with normal compilation. The 48 small corpus
pairs have identical ordered pivot/step traces, state hashes, final primal
vectors, objectives, iteration/refactorization counts and diagnostic counters;
every solution is optimal and passes the original-input primal certificate.

The exploratory extended suite reports **3,556 passed and 6 failed**. The six
failures reproduce on unchanged master `61e8bf9` (213 passed, 6 failed in the
three partial-pricing files), with the same evaluated values:

- `partial_pricing_integration_tests.jl:98–99`, "Wide bound flips save pricing
  scans without changing the optimum": 0 pool hits and 16,834 scanned entries.
- `partial_pricing_edge_tests.jl:34,35,40,46`, "Cancelled pivot and recovery
  preserve live candidate state": the pivot commits one iteration and the
  associated pool expectations differ.

They are not regressions from this change. The focused runner excludes those
two integration/edge files; pass `--extended` to reproduce the wider run. Both
complete failure logs and the passing focused log are retained under `results`.
This is targeted validation, not a claim that the complete project suite passes.
