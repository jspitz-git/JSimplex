# S4-T: exact public LP candidate and unresolved whole-process work contract

SOURCE/EXACT-OFFLINE ONLY at diagnostic47b0dac / master0eb75c3. No Julia, module load,
macro execution, floating factorization, native call, workspace or solver execution.
The new LP and its mathematical witness are accepted as offline evidence. The complete
public reference/candidate qualification contract is NOT established; launch_supported
is false. No numerical qualification plan or executable isolated module tree is created.

## One frozen input and exact witness

Minimize `-4*x1 -3*x2 -(7/2)*x3`, with `0 <= x <= 16`, and

```
0 <= [1    1/4  1/2] x <= 2
0 <= [1/4  1    1/2] x <= 3
```

This rectangular two-row/three-column LP is not a symmetric matrix workload; its final
square basis is nonsymmetric. All input coefficients, objective constant zero, and finite
row/column bounds are exactly representable binary64 values. exact-lp.json freezes every
scalar's bits and the Int64 CSC arrays colptr[1,3,5,7], rowval[1,2,1,2,1,2]. It also retains
the exact rational tableau states, reduced costs, directions, all competing ratios and
unique entering choices. No floating solve or search over LP candidates was performed.

Original-model optimum is x=[0,4/3,10/3], with row activities[2,3] and objective -47/3.
The row multiplier y=[-16/3,-5/3] is nonpositive, c-A'y=[7/4,0,0] is nonnegative and
complementarity holds. For every feasible x, c'x >= y'Ax >= y'b = -47/3. Equality at the
witness proves optimum for the ORIGINAL finite-bound LP. This proof is not an invocation
or acceptance of the production certificate, and does not certify a rounded future point.

The contemplated equal options are algorithm=:primal, pricing=:dantzig, basis_update=
:huangfu_hall, basis_refactorization=:native, simplex_strategy=:legacy, presolve=false,
scaling=:off, refactorization_interval=1, iteration_limit=4, time_limit=30, verbose=false;
all unlisted options retain the installed constructor defaults, including tolerances.
This is a candidate configuration, NOT a launch-ready frozen option payload. No option,
control, precision or safeguard is changed in production. Default native UMFPACK controls,
q=nothing and IRSTEP0 must remain identical on both sides; no control adapter is proposed.

## Conditional path, not a runtime trajectory

Use extended columns [A,-I] and row activity variables s1,s2. Starting at zero with basis
[s1,s2], the exact Dantzig algebra yields the following unique choices:

| Step | Enter / leave | Step size | New structural point | Ordered basis |
|---|---|---:|---|---|
| 1 | x1 / s1 at upper | 2 | [2,0,0] | [x1,s2] |
| 2 | x2 / s2 at upper | 8/3 | [4/3,8/3,0] | [x1,x2] |
| 3 | x3 / x1 at lower | 10/3 | [0,4/3,10/3] | [x3,x2] |

Improving-price magnitudes are initially[4,3,7/2], then[2,3/2], then[7/10]. Ratio minima
are strict, all pivots are nonzero, and the terminal nonbasic bound-directed prices are
nonimproving. The stored comparison includes the entering variable's finite upper bound.
The no-artificial path is source-supported conditionally: _primal_phase_one returns its
initial workspace if no activity violates a bound. The exact initial point is feasible.

The source primal loop prepares the entering FTRAN, validates the native row/point,
replaces the factor column, advances the basis and recomputes. The fixed legacy scheduler
uses update-chain length >= interval. Thus IF these numerical gates accept the algebraic
path without extra recovery, each pivot schedules a refactor. Basis CSC nnz is2,3,4,4.
The last refactor changes [[1,1/4],[1/4,1]] to [[1/2,1/4],[1/2,1]], with identical ordered
row/column-index arrays. This identifies a concrete potentially eligible same-pattern
refactor in the public controller; it does NOT prove that native binary64 follows the path.
The thirds in later states and production row/point/certificate checks matter.

On that conditional path, _basis_matrix! supplies SparseMatrixCSC{Float64,Int64}; the
workspace has the frozen two rows and Int64 structural indices. The candidate keyword
calls convert twice; both are identity only for that exact matching CSC type. The pattern
guard compares dimensions/colptr/rowval, O(m+nnz(B)) per eligible native refactor. Three
candidate refactor guard invocations would see3/4/4 entries, with only the final one true;
there is no symbolic reuse on a changed pattern. Other matrix types can allocate twice
and are outside this representation claim. Exact runtime types/control/pattern dispatch
would still need capture before accepting a numerical attempt.

## Explicit outstanding attempt ledger

The following figures are CONDITIONAL algebraic baseline entries per side, not upper
bounds on an execution. UNKNOWN means unqualified, never zero or silently excluded.

| Operation / stage | Baseline or unresolved obligation |
|---|---|
| Initial workspace / HH constructor | 1 on direct feasible legacy route |
| Prepared entering FTRAN / updates | 3 / 3 for the three algebraic pivots |
| Scheduled refactors | 3; ordinary/corrective refactors additionally UNKNOWN |
| Initial and postpivot primal/dual reconstruction | 4 ordinary FTRAN +4 BTRAN baseline |
| HH update internal unit transpose | 3 source-derived entries, additional to public BTRAN |
| Native factor/extraction | 4 baseline each; <=4 extraction orientation solves on that baseline only |
| Native pivot row BTRAN, unit metadata / quality | Required source routes; complete attempts UNKNOWN |
| Price/point corrections, rejection/recovery, copies | Complete attempts UNKNOWN; no zero-work assertion |
| Crash / artificial phase | Absent only if the specified policy/initial feasibility path holds |
| Original-objective restoration / certificate / retry | Required unchanged; complete attempts UNKNOWN |
| Events, diagnostics, serialization | No observer/counter implementation or frozen complete event budget |
| Process/import/precompile | Separate unresolved bootstrap work, described below |

Public `solve` invokes _solve_diagnosed with observer=nothing. A future observer through
_internal diagnostics would be a different explicit entry, not unmodified public solve.
Existing counters do not by themselves cover every attempted native/internal operation,
throws or setup before counters activate. No instrumentation is implemented here. Any
future instrumentation requires its own exact inverse, pre-forward counters on throws,
bounded ownership ledger, and accounting of scans/copies/JIT/Core.kwcall. S's seven root
substitutions plus one candidate keyword remain frozen; they do not authorize silent
instrumentation changes. Finite iteration_limit4 does not cap all the UNKNOWN work above.

Original acceptance remains solve -> original-model copy/transforms -> local simplex ->
internal primal and optimality certificates -> postsolve/original feasibility -> possible
original cleanup/retry -> restored original objective and final feasibility. Native
certificate recovery remains callable when the original witness check fails. There is no
working-model certificate transfer or replacement of these checks by the analytic witness.
An exact mathematical path does not justify treating any numerically selected retry as
impossible or preassigning it a zero budget.

## Concrete bootstrap blocker

S's128 ordered manifest entries and exact inverses are reused read-only. Its reference
and candidate roots require Main.JSimplex plus four pinned dependencies ALREADY resident.
The last guarded Julia process is absent; there is no qualified resident process for this
new pair. The driver cannot silently fill that gap with `using JSimplex`.

Installed production src/JSimplex.jl imports PrecompileTools and includes precompile.jl.
Installed PrecompileTools1.3.4 runs BOTH workload bodies when output generation OR
verbose[] is true. If the full workload executes and all its assertions succeed, the
source-level entries are82 public solves (2 scalar types * (5 managers *2 algorithms *
2 presolve settings *2 models +1 default solve)), four initial Markowitz factorizations,
four Markowitz refactors and16 backend solves. Internal solver work in those82 calls is
not bounded by this count. The assertions/exception path may stop earlier. These are
conditional source counts, NOT observed import work, mandatory work on every import,
or proof of what installed caches execute. They are already incompatible with silently
calling import numerically empty. Dependency initializers and cache selection/loading
are a further separate setup boundary; selected cached files/flags have not been qualified.

No cache, preference, verbose flag, environment or package is modified to evade this.
The precise open dependency is a documented pinned fresh-process bootstrap that reaches
Main.JSimplex and its four modules with an explicit numerical-work bound, without cache
creation/mutation. A cache-only startup mode may be a candidate, but it is NOT proved here.
S conditional source loading remains supported; this is not an impossibility claim.

## Disposition and cost review

Offline11 exact checks pass. Source/hash gates and separate author verification are in
results/S4-T. No production computational work, allocations or retained memory were added.
The diagnostic Fraction arithmetic/hash scans run offline only. Future loading retains two
sets of64-file type/method/regex/docs/JIT metadata plus local models/options; external
libraries and method tables are shared. Core.kwcall additions are not part of a claimed
complete runtime method count. There is no timing, speedup, free-balance or RSS proof here.

The whole qualification contract stays OPEN for BOTH bootstrap and complete controller
attempt caps. No separate numerical plan is authorized. ONE next action is a bounded
source-only bootstrap/cache-selection contract, with installed launcher/loading/dependency
init sources and fail-closed absent-cache behavior. Reuse this LP unchanged and do not
rerun its exclusive script, S inventories, Q costs or old numerical evidence. Only after
bootstrap is closed should the remaining controller attempt ledger be completed offline.
Q GC dominance/outlier, native retention OPEN, HH reuse disabled, CI off and all prior
rejections remain unchanged. Broader S4/S6 and full-suite/platform coverage stay OPEN.
