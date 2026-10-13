# Prospective cost schedule (UNEXECUTED; not a launch admission)

Fixtures.json:8 matrices/storage combinations x6scalar configurations =48cases.
Dimensions8/32; star matrix diagonal2, first-row offdiagonal alternating +/-1/8;
core control diagonal2, every offdiagonal1/8. Both sparse CSC and dense storage.
RHS is exact row sum; expected solution allones. Every number is exactly
representable even at Float32. BigFloat ambient128/256/512 RoundNearest;
Rational{BigInt} exact; Float32/64 fallback controls. No random inputs, tuning or LP.

Source-derived star prediction: column1 uniquely singleton initially; its upper
row has n-1terms. Remaining diagonal block contributes singleton pivots until
remaining2 triggers dense core (2*nnz >= remaining^2). Thus sparsepivots n-2,
upperterms n-1, eligible rows1 for each target scalar. Hardware eligible count0
by dispatch even though the row shape qualifies. Fully dense control has0 sparse
pivots and0 selected work from the initial density gate. Capture actual packed
order and assert these counts; mismatch stops, no fixture substitution. No prior
runtime construction or general pivot-path proof is claimed.

## Exact process and outer-call budget to carry into MA-E

One qualification process <=120s (new tests only; separate RED may be admitted
later with its own exact budget), then20 cost processes <=60s each, all serial.
Global cost-stage wall deadline600s INCLUDING launches, gaps and failures; maximum
qualification+cost wall720s. Stop on any failure or exhausted global deadline,
no retry or process replacement. No process is started in MA-D. MA-E must bind
actual Test counts, invocations, flags, manifests and fail-closed output audit.

Ten ordered side pairs; pair1 R,C; pair2 C,R; alternate through pair10. Pairs1–3
warm,4–10 measured. Each side process runs all48 cases in the fixed JSON fixture
order then scalar order. Thus20 processes,960 case visits;288warm visits and
672measured visits. This is process-paired measurement, NOT within-process paired
alternation. Fresh processes pay import/JIT every time; first-use/setup windows
must report it. Kernel windows require compile/recompile0 for acceptance.
No automatic extension if the600s global cap is insufficient.

Per case visit:
- one ordinary backend constructor, timed separately, plus one first forward solve;
-4 complete forward solves in one timed window, each with its ordinary RHS load,
  lower/core/upper/destination work and any call-local MA scratch;
- one first-use isolated upper reduction/reset in its own window, then
  4 isolated upper reductions in a distinct steady timed window. Reset work by copyto!
  from a frozen pre-upper input before EACH reduction, inside the window, on both
  sides. Report this O(n) reset cost and do not subtract it as a pure kernel time.
- one scratch-construction measurement for each of4target scalar cases (32target
  case visits/process); reference process performs the same separately labelled
  MA scratch-construction diagnostic using a direct diagnostic dependency. It is
  outside its unchanged production code/whole-solve windows. This is attribution,
  not a baseline production requirement. Hardware controls create no MA scratch.

Totals20processes:960constructors,4800complete backend forward solves,
4800upper-only calls and4800explicitn-entry reset copies. Sum matrix dimensions
per process960 ->96000 reset scalar assignments total. Upper selected term counts
per process:4storage/size star cases x6scalars: (7+7+31+31)*6=456;
10upper executions per visit (5full+1firstupper+4steadyupper) ->91200 total upper multiply/subtract
pairs over20processes, plus unchanged lower/core work. 640 labelled scratch setup
calls. Source-derived counts are prospective and NOT complete native/GMP work.
Fresh local scratch is still allocated on every eligible target solve/reduction;
"steady" means compiled repeated calls, never retained cross-call scratch.

Freeze the pre-upper fixture input without hidden solves: star has no lower
updates; surviving core diagonal2 uses rhs2 to produce1. In backend permutation
coordinates set upper sparse entries to the original corresponding RHS and core
tail to1. Dense-core-only upper input is allones,0pivots. Bind actual permutation
and compare independently with the identical reference source prefix outside the
cost window in qualification only; no extra prefix solves in cost processes.
The isolated original loop is a diagnostic-local renamed function, NOT replacement
of a production method. Its exact textual inverse must be bound before admission.

Record every time, allocation bytes/events, compile/recompile time, GC, endpoint,
output owner retention and source path. Construction, first use, complete solve,
upper attribution and scratch construction are separate windows, never added or
subtracted into a false component estimate. ExactFraction endpoint is allones;
record actual rounded inputs and sequential per-row reference values. Retain GC
and outliers. Process/startup/cache effects limit inference even with alternating
order; report distributions/paired ratios and uncertainty, not universal speedup.

Qualification tests include large->small rational limbs and precision changes;
post-growth cost is a separate bounded qualification attribution using those
same calls, not additional cost-stage cases. MA-E must enumerate those test calls
and windows explicitly. Until then no claimed exact aggregate qualification budget.
Existing backend fields stay fixed; report Julia graph sizes separately from
native limb capacity, allocator retention and GC. No native-free proof.

Production candidate work: one mode check per BigFloat call, row eligibility
O(K), bounds/assignedness/finite checks, at most one2BigFloat/12BigInt scratch set
per eligible solve, no seed copy, same Kproducts/Ksubtractions/Sdivisions and fresh
quotient per row. Dense-core-only BigFloat adds the constant mode check but no
scratch. Generic hardware loop has no eligibility work. MA Rational arithmetic
uses integer gcd/divide/multiply steps instead of Base GMP rational operations;
equal high-level counts do NOT imply equal internal GMP work or cost.

Only accept a production route after correctness plus repeatable complete-solve
benefit with scratch and guards included, hardware/control regressions assessed.
Otherwise retain original production path. No result threshold chosen after data.

## Review corrections R1/R2 (prospective, no measurement)

The allones solution is MATHEMATICAL, not a required exact floating endpoint of
LU. Require bitwise reference/candidate output equality including precision/sign
for every process-paired case. Separately, actual stored floating A,x,b must satisfy
an independent EXACT rational residual bound:
||A*x-b||inf <= 64*eps(T)*max(1,||A||inf*||x||inf,||b||inf).
Use the current specified BigFloat precision for eps; no raised solver precision.
Rational cases require exact zero residual. Upper-reduction publication still
requires exact sequential rounded reference parity. Nonfinite/signed-zero/flags
follow their explicit reference regressions; do not apply finite residual tests
to nonfinite cases. Freeze this bound now, never choose it from future output.

Both complete-forward and upper/reset wrappers use a first-use invocation with
repeat-count1 and the SAME callable signature as repeat-count4 steady windows.
No further warmup solve/reset allowed. Reference upper helper also gets its own
counted first use, since whole forward compilation does not compile that helper.
Scratch construction is a single FIRST-USE-ONLY attribution window per target
case, allowed to include compilation and initialization; never call it warmed or
require compile0 there. Kernel steady windows still require compile/recompile0.
Cold first-use and construction costs are recorded separately, not discarded or
subtracted. The additional960upper calls/resets do not change process/wall caps.
