# Simplex data movement and late-state profiling

Completed investigation from baseline `495da30`. This investigation covers repeated
basis assembly, prepared-direction handoff, certificate temporaries, and later
`medium.mps` states. It does not change pricing, tolerances, precision, pivot
selection or certification requirements.

## What the inventory established

The existing basis CSC storage is already reused. The remaining validation and
assembly work does not justify a persistent basis cache in these measurements:

| Instrumented case | Iterations measured | Assemblies | Assembly seconds | Point certificates | Certificate seconds |
|---|---:|---:|---:|---:|---:|
| medium dual prefix | 4,000 | 12 | 0.595 | 0 | 0 |
| medium primal prefix | 2,000 | 7 | 0.011 | 0 | 0 |
| medium cleanup, primal origin | 512 | 6 | 0.060 | 512 | 54.775 |
| medium cleanup, dual origin | 512 | 6 | 0.056 | 512 | 55.224 |

The cleanup windows took 188.753 and 198.900 seconds, respectively, including
profiling/instrumentation and GC. They are bounded continuations from original-LP
handoffs at iterations 335,046 and 212,280, not new complete medium solves.
The current cleanup path uses primal iterations for both origins. Each stops at
its deliberately selected iteration limit; that is not an optimum certificate.

An initial full runtime dual inventory returned OPTIMAL at 54,591 iterations and
passed original feasibility. It recorded 11,430 basis assemblies and 394 repeated
basis-index sequences within the same iteration. Its diagnostic dictionary held
strong workspace references, and one SIGUSR1 profile peek was taken; do not use
its elapsed/allocation data as an uninstrumented solver benchmark. It completed
normally before a considered interruption, so no termination signal was sent.
The corrected inventory uses weak keys. Native tableau recovery was called only
55 times (0.154 s inclusive in that first run); no basis-cache change is adopted.

## Implemented changes

- HH hardware-vector prepared direction: combine finite/equality predicates in
  blocks of 128 entries. After a mismatch, scan only the remaining direction
  for finiteness. This bounds redundant comparisons to 127 entries beyond the
  mismatch, instead of reading the complete prepared vector. Generic input
  keeps its original error/comparison order.
- FT/SS/BG: check both finite inputs while copying into an unpublished owned
  prepared buffer. Publish only on success. Aliased writable storage, published
  entries, mismatched dimensions and generic inputs use the original method.
- Primal point certification: lazily retain three native vectors of lengths
  `n`, `m`, `m`; recompute values on every call with the same CSC arithmetic.
  Construct row-activity bounds directly during the ordinary consistency scan,
  materializing the full Bound vector only when the existing fallback needs it,
  directly from a view to avoid an additional numeric activity copy.
- PFI's eta packing was already made direct in `d1978a1`; no duplicate new change
  is made here. The common triangular method benefits FT, SS and BG; historical
  late-factor replay in this investigation is HH-only.

The certificate retains `sizeof(T)*(n+2m)` numeric bytes after its first use,
plus small object headers. There is no cached verdict, changed tolerance, new
basis solve, or new matrix traversal. Phase adoption creates fresh scratch;
candidate workspaces own their buffers. The fallback still allocates its own
native/exact work arrays and now constructs each activity bound twice (once in
the scan and once in the materialized vector). This small extra fallback work
must be weighed against the removed unconditional arrays, not hidden.

## Work and memory review

| Change / frequency | Work removed | Added work or retained storage |
|---|---|---|
| HH direction validation, each column replacement | Separate direction read for equality on prepared hits | At most 127 comparisons past a mismatch; scan remains complete on invalid vectors; no retained storage |
| FT/SS/BG prepared handoff, each prepared solve | Separate finite-input traversals around an existing copy | Private buffer may be overwritten before finite failure; publication still waits for success; no additional storage |
| Native point certificate, each recovery/cleanup call | Three repeated vector allocations; unconditional activity slice and Bound array | Lazy `(n+2m)sizeof(T)` payload per workspace; current point is still copied and row enclosures still recomputed |
| Native row fallback, only when enclosure is inconclusive | Numeric activity slice before constructing owned Bound entries | Bounds are constructed again after the ordinary row scan; existing refinement work remains |

No new basis solves, matrix traversals, precision conversions, tolerances or
cached numerical verdicts are introduced. The prepared specialization is only
for Float32/Float64 vectors; existing generic precision paths remain intact.
Ownership/alias fallback checks protect published or shared prepared buffers.
The native certificate scratch is workspace-owned and created only on demand;
phase/workspace adoption constructs fresh scratch. There is no process-global
certificate cache. This review found avoidable scans and temporary arrays in
the original paths; the accepted changes remove them with the explicit costs
above. A persistent basis cache was rejected because its lifetime/invalidation
cost was unsupported by the measured assembly share.

## Historical late factors

Six immutable snapshots from the original medium reproduction retain explicit
HH base factors and update chains. `late-hh-kernels.jl` restores that stored
factor representation without fresh factorization. They are historical kernel
states, not checkpoints proving an identical current-version solve trajectory.

| Snapshot | Rows | Updates | U nonzeros | Update nonzeros | Dense FTRAN ms | Dense BTRAN ms |
|---|---:|---:|---:|---:|---:|---:|
| primal phase I start | 360,982 | 0 | 360,982 | 0 | 0.575 | 0.546 |
| primal phase II start | 360,982 | 122 | 560,977 | 79,677 | 0.981 | 0.915 |
| primal terminal candidate | 360,982 | 127 | 889,523 | 6,791 | 1.379 | 1.356 |
| dual auxiliary start | 360,982 | 0 | 360,982 | 0 | 0.575 | 0.593 |
| dual enlarged phase start | 586,972 | 0 | 586,972 | 0 | 1.016 | 0.962 |
| dual terminal candidate | 360,982 | 95 | 906,559 | 15,221 | 1.292 | 1.288 |

These are medians of nine warmed samples of ten calls, with zero measured
compilation. The terminal triangular solves are around 2.3 times the initial
ones in this replay. However, ordinary factor solves around 1.3 ms do not by
themselves explain roughly 0.1 s spent per point certificate in the late cleanup.
No claim about every update chain or every manager follows from six snapshots.

Excluding each first window (which includes initialization), the instrumented
256-step windows took 12.9–20.3 ms/step for the dual prefix and 25.9–35.8 ms/step
for the primal prefix. The full late cleanup windows took 198.9–205.8 ms/step
and allocated 37.78 MB/step. Prefix windows with refactorization allocated about
0.85–1.04 MB/step, while some refactor-free windows allocated almost nothing.
These profiled windows locate the late-stage extra work; they are not a controlled
whole-solver speed comparison or an explanation of every hour of a full solve.
The cleanup certificate remains a substantial target even after buffer reuse.

## Focused performance evidence

The final prepared-vector benchmark uses 13 alternating warmed samples for each
of 120 Float32/Float64, sparse/dense, length and hit/miss combinations. It varies
an input pair and consumes the result, preventing the discarded-work issue in
the initial probe. All cases allocate zero bytes. At lengths 2,048–360,982:

| Operation | Float32 new/old time | Float64 new/old time |
|---|---:|---:|
| HH prepared hit | 0.203–0.235 | 0.410–0.460 |
| HH first/early/middle/last mismatch | 0.190–0.240 | 0.382–0.470 |
| Common FT/SS/BG prepared copy | 0.174–0.237 | 0.310–0.365 |

There is a small-vector tradeoff: Float64 mismatch cases at length 8 are up to
13% slower (about 0.6 ns), and at length 64 up to 19% slower (about 3.1 ns).
The fused finite scan also does more work on invalid vectors than an immediate
short-circuit rejection. These costs are bounded and retain error semantics;
the large-vector savings are not a claim of universal speedup.

Native certificates use nine alternating warmed samples. Conclusive sparse
fixtures reduce allocation from 49,512 B (Float32, 2,048 rows) or 98,664 B
(Float64, 2,048 rows) to 32 B. Their new/old time ratios are 0.891 and 0.845;
the 32,768-row Float64 fixture has ratio 0.930 and 1,573,224 B → 32 B.
Dense 512-row cases have ratios 1.002 (Float32) and 0.985 (Float64): arithmetic
dominates, so no material timing improvement is demonstrated there. Measured
kernel compilation is zero. Full samples remain in the raw TOML records.

On the final actual medium cleanup workspaces, old/new certificate kernels
allocate 36,236,184 B and 18,784,280 B per call, respectively (48% less).
Nine alternating warmed samples gave 21.454 → 20.788 ms for the primal origin
and 19.949 → 19.003 ms for the dual origin. The observed median reduction is only 3–5%,
with overlapping samples (primal old 19.72–22.39 ms, new 18.60–23.04 ms;
6/9 paired samples improve). Halving allocation therefore does not establish
a comparable timing improvement; remaining arithmetic/refinement work is still
substantial. Both current 128-step continuations match
the old recorded pivot/state fingerprints and stop at the intended iteration
limits (335,174 and 212,408). Neither is a new complete medium solve.

## Preserved unsuccessful measurement attempts

- `prepared-probe` discarded predicate results. LLVM could eliminate work, so
  none of those times is performance evidence. v2 varies an input pair and
  consumes predicates/copy output using `Base.donotdelete`.
- The initial fused HH loop slowed Float64 first-entry mismatches by up to 33%.
  A first-entry check fixed index 1 but left other early mismatches expensive.
  The final 128-entry blocks bound that extra work; index 3, middle and last
  mismatches are included in the final benchmark.
- `certificate-bench` was intentionally stopped with SIGTERM to its own process
  group: the synthetic Float32 32,768-row initialization selected dense native
  LU and consumed approximately 4.7 GiB RSS before measuring the target kernel.
  This was a benchmark-fixture mistake, not a solver numerical failure or guard
  exhaustion. The corrected benchmark keeps Float32 cases at 2,048/512 and the larger sparse case in
  Float64. All attempt records are retained locally.

- A manager batch was accidentally run with `--compile=min`: 3,558 assertions
  passed and two allocation budgets failed. This is unsuitable for compiled
  allocation tests. Its corrected `-O2` run passed all 4,091 assertions,
  including workspace and triangular allocation checks. The first process
  had already exited before any considered stop; no signal was sent.
- The full project suite exceeded its 300-second diagnostic guard while LLVM
  was compiling `legacy_primal_direction_price_tests.jl:186`. No assertion
  failure preceded termination. This is **not** a full-suite pass.
- The added fallback allocation budget was observed failing at 157,112 B
  before removing the numeric slice. The final focused suite passes all 252
  assertions, including the 142,000 B budget and prepared handoff edge cases.

- The first `runtime-final` attempt exited before reading/solving runtime:
  Julia rejected a diagnostic method-extraction variable in global soft scope.
  The script is preserved as `runtime-final-invalid-v1.jl`; the corrected local
  scope runs in the new `runtime-final-v2` directory. Production source did not
  change. This is a harness failure, not a solver numerical failure.

## Reproduction and evidence

Measurements used Julia 1.13.0 on WSL aarch64 with one Julia thread and one BLAS
thread. The local PrecompileTools workload remains disabled. Raw reports,
process records, source/environment/input hashes and logs live in
`.superpowers/simplex-data-movement`. `reproduce/run.py` enforces the established
8 GiB virtual-memory, 6 GiB available-RAM and 1 GiB swap guards, one Julia/BLAS
thread and one numerical process. Its timeout is a diagnostic bound, not an
optimality result. Source and script hashes are checked after each job. Local
Manifest and LocalPreferences are not committed. The `source_revision` fields
record HEAD during experiments, when the production diff was still uncommitted;
the exact tested source is identified by the per-file hashes, not by that HEAD
alone. The final audit checks those hashes against the current production files.

The cleanup baseline solve records are reused from the earlier paired run,
with explicit `reused_from` provenance. They validate unchanged recorded pivots
and states; their elapsed times are not a fresh alternating timing comparison.
Final old/new certificate kernel timings are instead measured alternately on
the same current late workspace, after each continuation.

Runtime comparison hashes every pivot/flip selection and
step, and workspace arrays every 80 iterations plus the terminal workspace.
Cleanup comparison hashes every pivot/flip selection, basis indices, primal,
reduced costs and pricing weights. Matching fingerprints validate the recorded
trajectory; they do not compare every internal value at every instant. Kernel
ratios alone are not whole-solver speedups.


## Final validation and limits

The final audit passed against the exact production source hashes in
[results/audit.json](results/audit.json). The successful validation batches are:

| Batch | Result |
|---|---|
| Focused certificate/prepared handoff tests | 252 assertions passed |
| Prepared traversal budget | 14 assertions passed |
| Compiled manager/precision/allocation regressions | 4,091 assertions passed |
| Broader semantic regressions (`--compile=min`) | 15,689 assertions passed |
| External LP relaxations | 100 unique certified optima; 305 assertions passed |
| Medium cleanup origins | Both recorded 128-step trajectories match |
| Full runtime dual, HH/native320 | OPTIMAL, 54,591 iterations, 194 refactorizations |

External coverage is five inputs × primal/dual × PFI/HH/FT/SS/BG × native/Markowitz,
in Float64. Every input hash, iteration count, status and objective matches the
previous certified external records; each original primal point is checked.
Generic precisions have separate manager tests. This is not a claim of testing
every manager/precision/problem combination.

The final runtime objective is **51,425,691.76210138**, with original feasibility.
Both recorded trajectory hashes match the frozen reference exactly. Its measured
solve region took 175.855 s, including 0.422 s compilation and diagnostic work;
there is no repeated paired full-solver timing comparison, so this is a numerical
regression check, not evidence of whole-solver acceleration. The HH handoff
counter reports 54,434 hits and 503 mismatches: 501 first mismatches occur at
indices 2–128, one at index 1 and one in the remaining first half. This supports
covering early non-first mismatches rather than only the first element.

[results/provenance.json](results/provenance.json) preserves process/log/preflight
hashes and all successful and unsuccessful attempt statuses.
[results/prepared.csv](results/prepared.csv) and
[results/certificate.csv](results/certificate.csv) contain compact medians;
full benchmark samples, final solve/cleanup records, inventory records and test
logs are archived alongside them. The complete project suite remains incomplete
because of the documented LLVM/diagnostic-time-limit termination. No full new
medium solve or full primal runtime solve was performed in this investigation.

Independent read-only review checked numerical/ownership semantics, computational
work, retained memory, frozen-reference identity and the recorded final evidence.
No production-code blocker remains. Numerical safeguards take priority over the
measured kernel savings; their criteria and precision are unchanged.
