# Remaining numerical-kernel performance probes

This diagnostic-only investigation follows `primal-certificate-work` at baseline
`21a3fae8fe15107b6f09475d1acd03a9f986b9c8`. No production source file or solver
option is changed. All prototypes below are experiments, not deployed fixes.

The subsequent [basis-kernel savings](../basis-kernel-savings/README.md) work
evaluates safer production eta traversal and diagonal-last upper solve loops.
The measurements and experimental status recorded below describe this earlier
diagnostic commit.

The three questions were whether native correction data movement, initial
interval row activities, and the actual late-state solves of all five production
basis managers offer useful savings while preserving numerical operations.

## Findings

1. Native correction vector housekeeping is cheap in the full runtime solve.
   Fusing addition with result-finiteness checking wins locally, but has a very
   small whole-solve ceiling. Keep post-callback validation and numerical tests.
2. A stable row index preserves interval arithmetic, but does not justify its
   extra retained memory. Do not deploy this prototype.
3. Eta traversal and triangular upper factors are substantially more expensive
   than vector handoffs on the recorded long chains. A diagnostic PFI FTRAN
   prototype is promising; production integration still needs invariant and
   precision/aliasing coverage. HH remains worth investigating, particularly its
   reverse update traversal, but is not uniformly fastest on both histories.

## Native correction attribution

`correction-census.jl` times disjoint sections inside the original correction
body, with its arithmetic, acceptance tests, and callback order retained.
The complete HH/native320 legacy dual runtime solve finished **OPTIMAL** at
54,591 iterations and 194 refactorizations, objective 51,425,691.76210138,
with original primal feasibility. Its event and sampled-state SHA-256 hashes
match the established reference exactly:

- Events: `6330422d394b22e155e2ecd58fb96fd3a89035a8d86ed6b07722c348bd59ccdb`
- States: `1af4c4c85c63a500a038b6101718f969d8a0ab11fb5a978ee2ba77e1621eb743`

Instrumented solve time was 170.399 s, including 0.0446 s reported compilation.
This one full solve is a correctness/attribution check, not a speedup claim.
The 11,225 correction calls performed 11,368 refinement attempts.

| Correction section | Total seconds |
| --- | ---: |
| RHS preparation | 0.035 |
| Basis validation/assembly | 3.715 |
| Initial trial copy | 0.052 |
| Compensated solve quality | 7.448 |
| Correction FTRAN/BTRAN | 7.703 |
| Correction finite check | 0.078 |
| Trial addition | 0.084 |
| Trial finite check | 0.077 |
| Existing acceptance checks | 2.719 |
| Publishing the accepted vector | 0.045 |

The measured sections sum to 21.956 s. Housekeeping (RHS, copies, addition,
finite checks) is only 0.371 s. The fused addition/result check addresses part
of that small total, not the expensive residual calculation or basis solve.
Instrumentation adds clocks and can inhibit compiler optimization; these
numbers are attribution evidence rather than exact uninstrumented costs.

`correction-fusion.jl` preserves the complete correction-finite check before any
trial mutation. It combines addition and result-finiteness accumulation without
changing addition order. Thirteen alternating warmed rounds compare identical
inputs; each timed call also includes an identical trial-reset copy. All 14
cases have equal results and zero steady-state allocation: 12 synthetic
Float32/Float64 sparse/dense corrections and two snapshot-derived Float64
medium BTRAN corrections. Exceptional values and overflow are also compared.

On the medium-derived vectors the measured operation takes 0.288 -> 0.208 ms
(primal origin) and 0.287 -> 0.204 ms (dual origin), about 28–29% less.
These are corrections computed from historical certification snapshots, not
proof that the current medium trajectory accepts those corrections or invokes
them frequently. They do not establish a whole-medium speedup.

## Initial interval row activities

`row-locality.jl` constructs CSR-like metadata containing the original CSC
positions and their columns, in the same order each row encounters terms in
the original CSC traversal. It then retains two scalar row accumulators.
The prototype calls the unchanged product/sum enclosure helpers and preserves
per-row operation order. It does not copy coefficient values, prune terms,
change tolerances, or use higher precision.

Eleven alternating warmed rounds cover diagonal, sparse and dense matrices in
Float32/Float64 plus the two actual medium cleanup points saved by
`primal-certificate-work`. Each case compares interval endpoints exactly,
including changed matrix values and changed points with unchanged structure.
Structural edits to `colptr`/`rowval` would require rebuilding the index.

| Case | Candidate / original time |
| --- | ---: |
| Sparse Float32 / Float64 | 1.065 / 1.082 |
| Dense Float32 / Float64 | 1.145 / 1.129 |
| Medium primal origin | 0.994 |
| Medium dual origin | 0.979 |

The two medium cases take about 6.9 ms originally. Indexing retains an extra
**27,838,696 bytes** for 586,972 rows and 1,446,423 nonzeros; its payload scales
as `8*(m+1+2*nnz)` bytes, with O(m+nnz) setup and temporary row cursors.
Warm measured setup amortizes after approximately 81/20 calls if these small
medium timing differences persist. Given their size and the clear control
regressions, there is no convincing adoption case. First construction timing,
compilation, warmed setup time/bytes, and retained metadata are reported
separately in `rows1-result.toml`. Both solve arms allocate zero after setup.

## All five production managers on common histories

`manager-parts.jl` replays the same previously recorded late column exchanges
for PFI, FT, SS, BG and HH with native Float64 factorization. It measures chain
lengths 0, 80, 320 on historical `runtime-40000` and `fast0507-1000` histories.
These labels refer to the original history capture, not the new runtime solve.
Entering-column FTRAN and unit BTRAN use the actual next exchange; dense RHS
vectors are controls. Nine warmed samples contain ten solves each.

All 120 uninstrumented kernel cells have zero steady-state allocations. The
maximum reported normwise backward error is 4.22e-14. Two separate instrumented
processes reproduce every result-vector hash (240 comparisons). The second
instrumentation also covers specialized composed-row methods and upper-factor
kernels; the first had attributed those internals to their parent calls.

Uninstrumented medians at chain length 320, in milliseconds:

| Manager | Runtime FTRAN | Runtime BTRAN | fast0507 FTRAN | fast0507 BTRAN |
| --- | ---: | ---: | ---: | ---: |
| PFI | 1.876 | 2.323 | 0.0773 | 0.0868 |
| FT | 1.548 | 1.878 | 0.0520 | 0.0427 |
| SS | 1.542 | 1.929 | 0.0518 | 0.0413 |
| BG | 1.590 | 1.886 | 0.0678 | 0.0536 |
| HH | 0.396 | 0.612 | 0.0450 | 0.0777 |

These are identical-history kernel comparisons, not full-solver rankings.
They must not be extrapolated to other trajectories, Markowitz, or experimental
Direct-LU managers, which are outside this probe.

Within the detailed instrumented runtime samples:

- PFI eta traversal consumes about 84% of FTRAN and 88% of BTRAN section time.
- FT/SS/BG upper-factor solves consume about 76% of FTRAN and 86–87% of BTRAN.
  Composed row operations and vector permutations are much smaller.
- HH FTRAN splits work across U, L and updates; reverse update traversal is
  about 66% of BTRAN. On fast0507, HH updates dominate both directions.

Section shares use exclusive timing within the same instrumented run.
Instrumentation changes timings/code generation, so its milliseconds must not
be divided by the uninstrumented medians. The raw reports retain both.
Retained `factor_bytes` is Julia object-graph `summarysize`, not total RSS or
all foreign SuiteSparse storage.

### PFI diagnostic prototype

`pfi-bounds.jl` clones the original public solve bodies under private names and
adds `@inbounds` only to the two inner eta coefficient loops. It asserts exactly
one transformed loop per method. Dimension/alias checks, eta ordering, and all
arithmetic are retained. Before benchmarking, it validates equal index/value
lengths and index ranges on the frozen factor. This validation is outside the
timed solve; no unsafe malformed-payload case is executed.

Two processes compare 24 cases each; the second uses calibrated batches of
targeting about 10 ms in the baseline arm to improve small-case timing. Eleven alternating rounds
have identical vectors and zero allocations for both arms.

In the calibrated run, actual entering-column FTRAN at chain 320 takes:

- Runtime: **1.841 -> 1.513 ms**, 17.8% lower time.
- fast0507: **0.0560 -> 0.0404 ms**, 28.0% lower time.

At chain 80 the corresponding reductions are 12.0% and 24.0%. BTRAN changes
are much smaller (about 0.7%/3.9% at chain 320); do not treat the sub-percent
runtime difference as established improvement. The first, shorter-batch process
also improved long-chain FTRAN but with different magnitudes (runtime about
13–16%). This is a promising kernel result, not a measured full-solve speedup.

Before production adoption, prove the owned payload invariant across update,
refactorization, copying/sharing, all supported precisions and aliasing paths.
Payload arrays are mutable. Revalidating every eta entry on every solve could
erase the gain. The prototype is deliberately not installed in production.

## Reproduction, review and limitations

Run one job at a time through `reproduce/run.py`; it checks for an existing
Julia process, pins source/test/environment/input/snapshot digests and verifies
those digests on completion. It uses the established 8 GiB VM limit, 6 GiB RAM
floor and 1 GiB swap ceiling, with one Julia/BLAS thread. Commands for every
attempt are retained in `results/*-process.json`; local raw output is under
`.superpowers/remaining-kernel-probes`. `reproduce/audit.py` verifies completeness,
matching hashes and numerical checks and copies compact evidence to `results`.

Eight completed measurement jobs passed. Two earlier correction instrumentation
attempts failed due to Julia local-variable scope (global loop, then try scope).
Their source and logs are preserved; neither counts as a successful solve.
No numerical failure, memory guard termination, or solver regression is inferred
from these harness errors. No production source changed, so no new full project
regression suite was run. Whole runtime correctness is verified; full medium
solves and full-solve PFI prototype speed are not measured here.

Independent review explicitly considered computational work, memory retention,
operation order, mutable invariants, and the limits of benchmark attribution;
see [review.md](results/review.md).
