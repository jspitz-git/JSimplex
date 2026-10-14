# Current-master short time breakdown

Date: 2026-10-14. Master: `6f68e24e8ddac42b948da8fcc2d636c010751194`.
Diagnostic source was byte-identical to all514 master source/test/CI/project files.
This is new current-master characterization, not an old-baseline speed comparison.
No production/test/environment/master change was made.

## Decision

Prioritize a **private-scratch BigFloat native DenseLU triangular-solve design**
for `_backend_forward_solve!` / `_backend_transpose_solve!` in `src/factorization.jl`.
On sc50a, BigFloat256 ordinary solve median is68.150ms and120.21MB aggregate
allocation traffic. Diagnosed FTRAN alone has median25.81ms/79calls and BTRAN
12.13ms/44calls, against69.405ms diagnosed full solve. These are existing inclusive
kernel counters, not a complete PREforward backend budget; do not add all timers.
Stack samples separately identify LinearAlgebra.generic_trimatdiv! under the
native dense backend. This is repeated work rather than just a cold presolve cost.

The next bounded design should preserve native LU factors and pivot permutations,
all coefficient visits (including zeros), exact multiply-then-subtract/divide order,
stored/ambient precision and rounding, and exception/partial-write behavior.
Evaluate MA only with private scalar destinations and buffers; never mutate
factor entries, RHS leaves, retained published values or shared scalar owners.
A constant number of temporary scalars may remove intermediate results; replacing
array elements with one reused mutable number is unsafe. Publication copies and
scratch creation must be included in full-forward AND full-transpose cost.
No persistent global cache, full-vector eligibility scan or zero-row omission is
admitted by this recommendation. Unsupported precision/alias/nonfinite/exception
cases need explicit unchanged fallback. Small/dense/sparse-zero and short paths
must be controls. Start with BigFloat; exact rational benefit is a separate question.

This is a proposed NEW native DenseLU route, not reopening the rejected MA
Markowitz routing candidate, HH symbolic reuse, DSE isolation or cleanup omission.
No candidate, implementation, launch or speedup is accepted here. A distinct
source/design admission must first demonstrate safe local dispatch without global
method replacement. Potential is material on this measured high-precision workload;
size of any future benefit is unknown. Float64 takes a different UMFPACK path,
so this recommendation does not promise Float64 improvement.

For Float64 alone, the next priority would instead be reducing repeated exact
coefficient conversion/work in presolver passes, especially dependent-row
elimination. `_exact_rational` is already a direct exact constructor, so merely
replacing rationalize is not an available optimization. A per-pass conversion
reuse proposal would need ownership and invalidation proof and count its retained
O(nnz) rational storage; no such cache is introduced or accepted here.

## Ordinary full-solve measurements

Three measured calls per case in one process per scalar; median and complete range.
Parsing, setup of diagnostic objects, token comparisons and profile export are
outside these windows. Solver's own setup/presolve/cleanup/certification remain
inside. Default verbose logging/formatting/output-to-file is included. MB are
aggregate GC allocation traffic, not peak/live memory or a native free ledger.
Different scalar types take different trajectories; cross-type ratios are not
kernel speedups. All measured windows have zero compile/recompile time.

| Scalar | Case (rows/cols/nnz) | Median ms | Range ms | MB/call | Events/call | Iterations / refactors |
| --- | --- | ---: | --- | ---: | ---: | --- |
| Float64 | adlittle (56/97/383) | 2.889 | 2.865–2.940 | 4.067 | 84,040 | 89 / 6 |
| Float64 | afiro (27/32/83) | 0.584 | 0.486–0.844 | 0.920 | 17,961 | 9 / 2 |
| Float64 | primal-chain130 (130/130/259) | 4.791 | 4.745–4.847 | 6.990 | 83,543 | 118 / 7 |
| Float64 | sc50a (50/48/130) | 1.594 | 1.579–4.084 | 3.143 | 66,652 | 34 / 3 |
| BigFloat | afiro (27/32/83) | 5.183 | 5.105–5.354 | 9.974 | 189,222 | 7 / 2 |
| BigFloat | sc50a (50/48/130) | 68.150 | 68.094–70.424 | 120.206 | 2,196,300 | 35 / 3 |
| Rational{BigInt} | afiro (27/32/83) | 8.284 | 7.181–14.935 | 27.125 | 678,485 | 9 / 1 |
| Rational{BigInt} | sc50a (50/48/130) | 130.626 | 96.548–144.792 | 191.287 | 4,770,133 | 25 / 2 |

BigFloat sc50a measured GC is6.96–7.18ms/call; rational sc50a30.01–44.78ms/call.
All GC/outliers remain; e.g. Float64 sc50a4.084ms and rational afiro14.935ms are
retained. There is no historical baseline pair, independent-process replication
per case, universal-speedup claim, or statistical confidence guarantee.

## Sampled decomposition

Exclusive ancestry categories were frozen before execution. Presolve has first
priority, then cleanup/certification, factorization, basis solves, pricing,
model/setup, other. Work inside cleanup is charged to cleanup even when its leaf
is LU or a triangular solve. Native/GC/runtime work inherits its captured ancestor
where available. `other` must not be read as zero-cost or entirely solver overhead.
These are shares of captured stack samples, NOT exact fractions of ordinary wall
time. Sampling slowed full batches by3.99–8.93x versus ordinary-call medians and
retained64/8solution outputs per batch; this perturbation precludes transferring
sample percentages directly to unprofiled milliseconds. Kernel timers provide a
separate, less intrusive cross-check. Low31/45sample cases are particularly coarse.

| Scalar / case | Samples | Presolve % | Cleanup/certification % | Factorization % | Basis solves % | Pricing % | Setup % | Other % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Float64 / adlittle | 162 | 50.0 | 6.8 | 0.6 | 13.0 | 0.0 | 0.0 | 29.6 |
| Float64 / afiro | 31 | 61.3 | 3.2 | 0.0 | 19.4 | 0.0 | 0.0 | 16.1 |
| Float64 / primal-chain130 | 240 | 61.3 | 2.9 | 0.4 | 15.4 | 0.0 | 0.4 | 19.6 |
| Float64 / sc50a | 103 | 58.3 | 2.9 | 1.9 | 10.7 | 0.0 | 0.0 | 26.2 |
| BigFloat / afiro | 45 | 13.3 | 44.4 | 2.2 | 20.0 | 2.2 | 0.0 | 17.8 |
| BigFloat / sc50a | 577 | 2.3 | 21.5 | 14.9 | 48.7 | 4.0 | 0.5 | 8.1 |
| Rational{BigInt} / afiro | 101 | 4.0 | 61.4 | 3.0 | 19.8 | 0.0 | 0.0 | 11.9 |
| Rational{BigInt} / sc50a | 950 | 1.5 | 30.9 | 5.8 | 31.9 | 1.1 | 0.3 | 28.5 |

Float64 presolve accounts for50–61% of captured samples. Its nearest source frames
include `_exact_rational` (5/31 afiro,27/162 adlittle,14/103 sc50a,30/240 chain),
`reduce_dependent_rows`, `_subtract_scaled!`, and `_row_entries`. These are sampled
ancestry attributions, not counted conversions or exclusive line CPU timings.
BigFloat sc50a nearest source frames are native forward190/577, transpose109/577,
and dense factorization182/577. Rational sc50a has239/950,88/950,317/950 respectively.
Source-frame build paths in Julia stack metadata are retained verbatim; installed
LinearAlgebra source was pinned/read, not retroactively claimed as new runtime
code capture. Exact raw stacks and overlapping inclusive function counts are in
`results/MASTER-PROFILE/run-*/` and `summary.json`.

## Execution and validation

Three exit0 guarded processes:59.805461,33.766699,41.779532s; total135.351692s.
These inclusive durations include loading/JIT/diagnostics and are NOT benchmarks.
Import-to-main observations3.124270/2.802077/2.742252s and individual cold/parse
records are separate. Compilation before timed entry into driver functions is
not fully attributed by those records; only ordinary and sampled windows are
verified compile/recompile zero. Fixed schedule376solver entries across8cases,
48measured calls,288sampled calls; no retry, no additional solver/certificate
calls during analysis. All cases OPTIMAL with repository objective oracle and
exact endpoint/precision/input-value agreement across plain/diagnosed/sampled
calls. This reuses production certification, not a new independent primal/dual
certificate for every result. Input-token checks do not prove arbitrary alias
ownership or observer neutrality.

Each process passed12audit gates. Full3772launch hashes/75trees and514master paths
verified; postcheck10PASS. Lowest sampled available RAM21350036KiB, swap0.
Complete158old/new groups ANDsessions absent and noJulia after completion.
Initial relative-path launcher invocation was rejected before any reservation or
Julia process; `sequence.log` preserves it. Exact absolute invocation then ran the
single admitted sequence without changing driver/manifest. No numerical retry.
All old MA-P/O evidence and rejections remain frozen. Six exact current MA-P
closure/publication/result-review continuation bindings map only to the new
beforecopies; older mappings unchanged.

## Work and memory assessment

No unnecessary NEW production work or retained memory was introduced: production
is unchanged. Diagnostic costs include input-token snapshots, existing bounded
kernel/event dictionaries, one unused outside-window diagnostic object even in
plain calls, a16MB profiling buffer, profile solution vectors (64/8), and portable
stack serialization. They are explicit cold/observational overhead, not a benefit
or allocation-neutral measurement. Neighboring diagnostic allocation can affect
GC scheduling; all observed GC is retained. Per solve arrays and backend arithmetic
still allocate substantially in high precision. The proposal would add private
scalar initialization and publication copies, so qualification must establish
net benefit including these costs and no avoidable full scans/extra basis solves.
All tolerances, numerical safeguards and precision policies remain unchanged.

Independent admission: `results/MASTER-PROFILE/admission-review.md`.
Independent result review: `results/MASTER-PROFILE/result-review.md`.
Full-suite/large-model/current-HH performance and the broader S2–S6 plan remain open.
CI remains disabled and automatic continuation paused.
