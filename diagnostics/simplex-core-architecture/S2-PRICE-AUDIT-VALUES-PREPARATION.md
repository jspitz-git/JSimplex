# S2-C: unexecuted price-audit values candidate

S2-C prepares separate source and tests only. Actual production, tests, environment,
CI and master remain unchanged. No Julia query, parser, import, compilation or
numerical call was performed. Runtime behavior and performance remain unqualified.

## Candidate and numerical scope

`results/S2-C/candidate-primal-updates.jl` adds a two-owner read-only AbstractVector
and replaces exactly one existing price-audit `vcat` with its factory. Removing
the saved `adapter.jl.txt` and reversing that assignment recovers the entire
current source byte-for-byte. The private inner constructor rejects empty parents
and union element types; two explicit Float32/Float64 factory methods borrow only
nonempty vectors. Empty, mixed, union, arbitrary-precision and other storage keep
materialization. Both parents' dataids are exposed. There is no write, pointer,
workspace-cache or persistent-state interface. Concurrent mutation and arbitrary
foreign unsafe_wrap overlap are outside the contract; normal audit scratch stays
freshly allocated and independent.

All original prediction copies, recomputation, early basic-price gate, ordered
residual arithmetic, native compensation/wide fallback, tolerance and certificate
boundaries are byte-identical. This does not revive rejected S2-A or omit cleanup
reconstruction. No safety gate is removed.

## Frozen test text

`candidate-tests.jl` is UNEXECUTED and requires a future separately admitted candidate
package overlay. Including the candidate file into an already loaded production
module is explicitly prohibited. It contains:

- Indexing/axes/eltype/bounds/read-only tests; repeated owner, empty parents,
  exact constructor domain, union/mixed/view fallbacks, NaN payload and signed zero.
- Twenty dimension-compatible quality rejection calls: two hardware types,
  five nonempty scratch arrays, each borrowed through either parent. Separate
  empty compensation/error_sum checks materialize before a simulated resize.
- Twenty-eight hardware quality pairs (fourteen per type): finite, perturbed,
  tight-policy compensated candidate, signed zero, nonfinite x/matrix/RHS,
  cancellation, overflow, underflow, two transposed cases and two zero-row cases.
  Matrix/value/RHS formulas and expected finite/reliable flags are frozen in text.
- Two generic fallback quality pairs: exact rational and stored-256-bit BigFloat
  under ambient64. Thirty pairs mean sixty direct solve_quality! entries, plus
  twenty expected alias rejection entries; this excludes integration work.
- All four quality fields and all six initialized scratch arrays compared.
  Hardware scalar equality uses UInt32/UInt64 bits, including NaNs and signed zero;
  nothing and exact values have explicit equality paths. Nonfinite early returns
  require Inf residuals, unchanged zero work arrays/terms and empty compensation.
- One exact existing helper and three unchanged integration testsets copied from
  primal_update_tests.jl, covering cancellation, explicit-system residuals and
  verified corrected pivots. Byte offsets and whole-source/slice hashes are saved.
  This is prospective new candidate regression work, not a historical driver rerun.

These are prospective expectations, not observed branch coverage. In particular,
no compensated/wide route is claimed captured. A later admission must freeze total
integration/setup calls as well as these direct calls; the selected test text alone
is not a launch allowance or complete backend-work budget.

## Work and memory review boundary

The candidate targets one O(n+2m) input-vector copy per reached price audit. It
adds at most four O(1) empty checks, two exact type checks and a split/branch per
indexed value. The immutable adapter retains two existing vectors for its local
lifetime; whether it allocates or escapes is unmeasured. Parent dataids tuples
and dispatch/inlining costs also remain unmeasured. Existing scratch allocation,
finite scans, residual term visits, possible compensation/wide allocations and
all solver work remain. No added solve, full-vector scan or retained workspace
cache appears in the source difference. No speedup or allocation reduction has
been accepted; whole-audit overhead may offset the avoided copy.

Tests are cold preparation: control vcat, independent scratch, comparisons and
integration fixture/factor work are additional test work. No production benchmark
is required for this offline publication. Future numerical admission must measure
complete audits including fresh scratch, sparse/dense sizes, at least three
interleaved warm pairs, compilation-free samples, events/bytes and all outputs.

## Evidence and continuation

Initial offline check: 21 literal checks, 535 read-time hashes and 513 actual
src/test/CI comparisons to master. These prove text/hash structure, not Julia
syntax, dispatch, aliasing or numerical correctness. Independent author and fresh
gpt-6-astra review are bound separately. S2-B evidence/scripts remain frozen.
Current STATUS and roadmap are preserved as `*.before-S2-C` before continuation
updates, with exact mapping for the predecessor's 24 closure bindings.

Next permitted work after acceptance is S2-D admission preparation/review only:
concrete overlay, fixed call budgets, launcher, pins and fail-closed auditor.
No numerical allowance is granted here. S6-AQ remains independently conditional;
HH reuse stays disabled, CI off, all previous rejections and broader gates open.
