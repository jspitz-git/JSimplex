# Direct LU / Markowitz Task 3 cost preparation

Status: OFFLINE preparation only. The companion independent review decides
admission readiness; neither cost process is sealed, reserved or executed here.
The original plan/spec remain frozen. Tasks 1–2 correctness was accepted at
3006acd3d7b4873928fc62663e66c94296f4173b; master is unchanged at
6f68e24e8ddac42b948da8fcc2d636c010751194. Old RED, failed GREEN and corrected
GREEN evidence and scripts remain frozen, never replayed or rewritten.

## Exact experiment

New controls and driver: `results/DIRECT-LU-COST-PREPARATION/`. The qualified
78-file ordinary candidate overlay is reused without modifying one byte.
`cost.jl` calls the ordinary constructor or private normalized direct factory
explicitly; there is no method replacement, public solver or additional fixture.
It imports one ordinary JSimplex module, with the same pinned dependency/runtime
and `--compiled-modules=existing` loader. This is not cache confinement or a
complete import-work proof. No old installer, correctness driver or audit runs.

Four fixtures: sparse32, dense32, sparse96, dense96, each cyclic row permutation
by3 and reversed columns. Sparse diagonal4/subdiagonal-1/2/superdiagonal1/4;
dense diagonal4/offdiagonal(-1)^(i+j)/16/n. No row scaling. A sequential eight-step
schedule changes j=1+mod(7t,n), a=copy(B[:,j]), a[1+mod(j,n)]+=1/32.
Frozen IEEE tokens include all nine matrices B0..B8, eight entering/DSE/unit RHS
triples per fixture:36 matrices,32 steps,101790 scalar tokens. JSON/TOML agree.
No input construction or matrix update happens inside a measured window.
The independent offline test rebuilds every input coefficient, permutation,
replacement and RHS bit. Inputs are compared to frozen tokens after each window.

24 cells =4fixtures x FT/SS/BG x native/Markowitz. Each of two serial processes
has3 warm and7 measured alternating reference/candidate pairs per cell. Process2
reverses the first side of every pair. No extra solve warmups or probes.
Each window constructs a fresh factor, performs8 entering FTRAN +8 distinct DSE
FTRAN +8 unit BTRAN +8 replacements, then refactors after updates4 and8 using
frozen B4/B8. Entering direction is not reused as the DSE destination. Recorded
output tokens and exact residual checks detect an overwritten direction too.

## Work, instrumentation and memory

Across both processes:960 lifecycles/initial constructions,7680 updates,
15360 FTRAN,7680 BTRAN,1920 explicit refactors. Per process:480/3840/7680/3840/960.
These are driver entry budgets, not complete observed backend/native attempts.
Each direct construction/refactor performs an ordinary factorization, export,
validation, normalization, packing and new manager/scratch construction. There
are1440 such candidate constructions/exports (720 native,720 Markowitz) and1440
ordinary construction/refactor entries. Conditional native orientation solves
are additional (up to720 on the candidate side); ordinary backend internals,
Markowitz pivot/core work and triangular update work remain ordinary source work.
No numerical policy, tolerance or small coefficient is changed. No HH reuse.

An outer Base.@timed window includes the full lifecycle and its instrumentation.
Six nested time_ns totals report construction, FTRAN, BTRAN, update, first and
second refactor. These are subsets, not additive overhead corrections. No nested
@timed disables outer compile accounting. Both sides pay identical timer sites,
one six-UInt64 timing vector and three O(1) mode reads; mode acceptance is checked
after timing. All fresh manager/backend/export/scratch costs are inside. The
candidate still constructs a whole replacement manager at each refactor and
cannot exploit ordinary spare/buffer reuse; this is deliberately measured.

The harness allocates24 independent n-vector output destinations per window
outside timing on both sides (192n bytes plus headers). They retain every solve
result for detached checking; no output copy or matrix mutation is inserted in
the window. Float64 preliminary residual checks and input comparisons happen
afterwards, with no extra solves. The new Python auditor independently evaluates
all23040 residuals using exact integer-scaled binary64 tokens and the frozen
128*n*eps(Float64)*max(1,||M||inf*||x||inf,||rhs||inf) bound. It uses B-before for
both FTRANs and B-after-transposed for BTRAN. This offline audit is outside the
Julia process limit; it is not benchmark or native work.

Base.summarysize(final_factor) runs after the second refactor and outside timing.
It includes reachable Julia pools, scratch and ordinary backend spares and is
reported separately from output/input/serialization memory. It excludes hidden
native allocations and is not peak/live-native memory or a release proof. Old
factors are not explicitly retained across windows. The previous factor can
remain uncollected until GC; no assertion of collection or finalizer completion.
At most one cell's20 detached records is retained; raw tokens/serialization and
input matrices consume RAM/time outside windows and can affect process GC.
No explicit GC is inserted. Natural in-window GC remains part of total cost.

Base GC aggregate bytes/events can include native allocations routed through
Julia; they are not a pure Julia-object or live-memory ledger. Timed compile and
recompile must both be zero for every measured window. Warm records, GC and
outliers are retained. Nonzero measured compilation stops, without schedule tuning.
Time/bytes/events/GC/compile/recompile, all nested durations, final graph size,
mode triples and full detached outputs are written for every finished window;
cell-start markers survive mid-window failures. Partial records/logs are preserved.

## Fixed selection and failure behavior

Per cell report paired ratios, medians, MAD, min/max and all7 measured pairs per
process. A cell is promising only when each process total-time paired median
<=0.95, at least10 of14 pairs are faster, and median bytes AND events do not
increase in either process. Conservative clarification of the plan's memory
limit: any measured pair with candidate retained bytes >110% of reference
rejects that cell. Do not average it away. A manager/backend qualifies only if
all4 fixtures qualify; no pooled cross-manager result or default promotion.
A correct slower cell remains a recorded performance rejection, not a reason to
rerun. Numerical failure, malformed output, missing pins, changed command,
resource violation or incomplete process cleanup stops subsequent execution.
Direct native still lacks UMFPACK combined-solve refinement; residual success
cannot establish equivalent native stability, public trajectory or end-to-end speed.

## Launch admission

`seal.py cost1` and `launch.py cost1` are prospective commands, not executed here.
Only cost1/cost2 literal configurations are admitted. Each uses a new output and
exclusive reservation with a90-second inclusive process/termination limit, one
Julia, Julia/BLAS1, heap2GiB, VM8GiB, availableRAM>=6GiB, swap<=1GiB. Byte-identical
qualified guard/supervisor copies preserve global advisory ownership, live-Julia
check, PID/boot/start_ticks/command identity, group AND session cleanup, terminal
RAM and absolute deadline. Preparation host checked all202prior groups/sessions.
Fresh host refs/boot/groups are checked at each seal AND launch; no old host is
substituted. Each manifest requires fresh independent exact stage review.

Cost2 requires the immutable accepted cost1 audit and all raw/command/process/
resource/reservation pins, plus fresh closure including cost1's new groups and
sessions; independent cost2 stage admission binds those prior records. No automatic
second process, retry, alternative schedule, increased size or time limit. CI stays
off, automation paused, user environments untouched. Standing short-run human
permission remains sufficient once concrete independent stage admission is accepted.
Preparation acceptance is not that stage admission.

## Offline verification and continuation

New48 input/oracle/selection checks and61 synthetic control/syntax checks passed.
These test exact fixtures, JSON/TOML agreement, wrong residual/nonfinite tokens,
order reversal, metric/mode/compilation rejection, exact command/budget/review
membership, memory boundary and outlier preservation. They are not Julia parse,
compile, runtime or numerical coverage. `cost.jl` remains UNEXECUTED.
New independent review must cover all inputs, actual solve signatures, loaded
module, timing boundaries, output schema, exact residuals, selection predicates,
source/runtime pins and complete fail-closed launch paths. Review must explicitly
judge unnecessary work/memory. No production source/test/environment/CI changes.

Before continuation changes, current STATUS/roadmap bytes were preserved.
Four exact mappings cover the previous GREEN correctness closure/publication;
all older mappings remain unchanged. Broader architecture programme stays open.
After offline acceptance, the next step is fresh cost1 sealing and independent
stage admission, then ONE short process. Cost2 remains separately gated.
