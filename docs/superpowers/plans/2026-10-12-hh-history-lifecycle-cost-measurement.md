# S4-Q: nonsymmetric fixed-history HH lifecycle measurement

Status: prospective numerical plan, subject to S4-P independent contract review.
No execution has occurred. This file and exact inputs must be pinned BEFORE a future
single launch. S4-P itself is SOURCE/EVIDENCE ONLY. No production promotion.

## Frozen inputs and numerical oracle

Use ONLY S4-P/exact-inputs.json, SHA256
`85874a35de281a9de4ce4d49c7f17f176d37a1597fc557ae64469202fcfd9b06`.
Two NEW Float64/Int64 CSC fixtures: sparse48 nnz142 and dense48 nnz2304, seven
stages each. Indices below are one-based. Initial diagonal is 6+(i mod5)/32.
Sparse superdiagonal is 1/64, subdiagonal -1/128. Dense upper entries are
((i+2j) mod3+1)/4096; lower entries are -((2i+j) mod5+1)/8192.
Replace columns [3,17,31,31,17,3]. First three activate a column by adding 1/8
at (j,j) and 1/256 at (j+1,j); last three restore its original complete column.
The active sets are [],[3],[3,17],[3,17,31],[3,17],[3],[]. B6 equals B0 exactly.
All stages have the same pattern, strict row diagonal dominance with margin >5,
and are nonsymmetric. No coefficients are discarded.

zF[i]=(-1)^i, zB[i]=(i mod3)-1; bF=B*zF and bB=B'*zB. Every matrix coefficient,
RHS, incoming column and known-solution bit is frozen (19,138 entries). Build 28
independent owned CSC objects (7 stages x2 fixtures x2 sides), plus independent
RHS/incoming vectors for each side BEFORE timing. No per-lifecycle matrix building
or mutation. Assert all input values/patterns and side storage independence before
launch work; recheck bits after each lifecycle outside its window.

For every retained output z use the predeclared exact rational oracle
||M*z-b||inf <= 64*2^-52*max(1,||M||inf*||z||inf,||b||inf).
M=B for ordinary FTRAN, M=B' for BTRAN. A prepared incoming-column solve uses the
OLD basis B_(k-1) and new column a_k, including step4 after the B3 refactor.
The known solutions aid input construction; equality to their bits is NOT required.
No change to production tolerances, precision, pivot safeguards or finite checks.
Dominance proves invertibility, and d[j]>=1-(1/8)/margin>39/40 for the exact incoming
direction. This is an exact-input pivot bound, not an assertion about rounded output.
Keep all nonzero residuals and pair differences; do not replace them with zero claims.

## One lifecycle and exact work

Each lifecycle creates ONE fresh factor at B0 with native default controls,
q=nothing and IRSTEP=0. Reference uses production HH. Candidate uses ONE new exact
source clone with only the same three routing-name changes and guarded Float64
reuse_symbolic keyword as G/M; inverse transformation must equal production bytes.
No production method overwrite, automatic refactor policy, copy or update adapter.

1. Constructor at B0, ordinary FTRAN(bF0), BTRAN(bB0).
2. For k=1,2,3: prepared FTRAN(a_k) on old basis; immediately replace_column! using
   that SAME destination vector and column j. Then ordinary FTRAN(bFk), BTRAN(bBk).
3. One timed refactor to B3; ordinary FTRAN(bF3), BTRAN(bB3).
4. For k=4,5,6 repeat step2 with the reverse replacements.
5. One timed refactor to B6; ordinary FTRAN(bF6), BTRAN(bB6).
6. Owning body returns nothing. Explicit full GC after that return is INSIDE the
   outer lifecycle window. Never manually free or finalize any object.

Ordinary FTRAN must call _ordinary_forward_solve!, not the preparing public helper.
BTRAN uses ordinary vector RHS. Prepared FTRAN uses forward_solve!, immediately
followed by replace_column! without intervening solve. No extra verification solve.

| Work | Per lifecycle | Warmup (8) | Measured (32) | Total (40) |
| --- | ---: | ---: | ---: | ---: |
| Constructors | 1 | 8 | 32 | 40 |
| Refactor attempts | 2 | 16 | 64 | 80 |
| Column updates | 6 | 48 | 192 | 240 |
| Prepared FTRAN | 6 | 48 | 192 | 240 |
| Ordinary FTRAN | 9 | 72 | 288 | 360 |
| BTRAN | 9 | 72 | 288 | 360 |
| All direct HH solves | 24 | 192 | 768 | 960 |
| Update-internal unit transposes (source derived) | 6 | 48 | 192 | 240 |
| _hh_apply! entries (source derived) | 30 | 240 | 960 | 1200 |
| Native numeric / HH extraction entries (source derived) | 3 | 24 | 96 | 120 |
| Native orientation validation solves (upper bound only) | <=3 | <=24 | <=96 | <=120 |

Per lifecycle _hh_apply! entries: prepared directions (0+1+2)*2=6; post-update
ordinary FTRAN (1+2+3)*2=12; BTRAN another12. Initial/post-refactor solves use empty
history. This counts entry calls, not coefficients visited or observed native calls.
Reference symbolic entries=60; candidate initial symbolic entries=20 and candidate
pattern scans=40, source derived across the entire process. Same-type CSC conversion
may be identity; the O(n+nnz) pattern guard and wrapper-owned CSC copies are not free.
No public solver/workspace/iteration/certificate/quality/observer calls, no factor
copies. All 240 history records are private; each refactor retires exactly3 records.
Pool entries/payload can be reused after first refactor; do not claim zero allocation.

## Repetition and windows

Warmup: TWO rounds; sparse then dense; odd round reference/candidate, even round
candidate/reference. Each combination executes one whole lifecycle per round,
8 lifecycles total. Measured: EXACTLY EIGHT rounds with the same fixture/order rule,
32 lifecycles, 16 side pairs (8 per fixture). Four pairs of each order per fixture.
Every lifecycle has the identical frozen history; no phase/order confounding.
Use the same typed helpers, timer expressions, counter placements and output layout
in warmup and measurement. No additional warmup, adaptive repetitions, retries,
subtraction of compilation, discarded samples or opportunistic follow-up cases.

There are 40 outer @timed calls and 80 nested ordinary-refactor @timed calls total.
Before EACH lifecycle, full GC(true) OUTSIDE the outer timer. Inside outer timer:
call a @noinline owned_history! body, then GC.gc(true), then return nothing. Thus
80 explicit GC entries (40 outside,40 inside), excluding natural GC. The body holds
all factor/native/extracted-base roots, creates the factor and never returns any
owner. Its two refactor timer helpers increment pre-call attempts, invoke refactor,
and return NOTHING rather than refactorize!'s factor return. @timed.value and all
record/closure fields must never retain any factor, native wrapper, base or history.
No saved old-owner identity references, graph snapshots or WeakRef-based free claim.

Inner windows are SUBSETS of outer windows. Report them separately, never sum them
with outer cost and never interpret outer-minus-inner as isolated GC/free cost.
Outer includes constructor, solves, updates, retirement, bounded diagnostic checks,
scalar captures, nested timer overhead and explicit final GC. Pre-GC, input building,
output-vector allocation, residual scans, hashes and serialization are excluded.
The final GC can process unrelated pending finalizers and collected timer temporaries;
completion is not successful native-free capture. Inputs and retained outputs remain
alive outside windows. This is a bounded owned-factor lifecycle experiment with GC,
not the lifetime of the whole process or a native allocation/free ledger.

Both measured outer and nested windows MUST have compile_time==recompile_time==0.
Any nonzero value: preserve the sample, STOP remaining work and report it unexecuted.
No exception retry. The first unexpected return, counter/state/finite/oracle/guard
failure stops later lifecycles. Record partial attempts even when a call throws.
Use a typed metrics record; materialize only scalar timer fields, never the value.
The same helpers must specialize on equivalent concrete factor/input types; review
code before launch and reject a design whose diagnostic roots/JIT cannot be separated.

## Bounded diagnostics and output ownership

Preallocate 960 distinct owned length48 output vectors outside timers:24 per lifecycle,
46,080 Float64 values (368,640 payload bytes, vector headers additional). Solves write
directly into these; no per-solve output copies. Prepared outputs are immediately
consumed by the update, then retained only as numeric evidence. External inputs and
outputs must not alias factor scratch. No per-step factor snapshots or growing ledgers.

Increment constructor/refactor/update/F/B attempts BEFORE calls inside outer windows;
refactor attempt increments also lie inside its inner window. All calls must finish
successfully; returns checked by identity locally and then discarded, never captured.
Within each lifecycle use bounded scalar assertions: prepared_valid true before each
update, output isequal to prepared_direction (6 additional length48 scans); false and
expected history length after each update; private shared_count=0; history3 before
and history0/preparedfalse after each refactor. Capture pool pair counts and entry
counts (four integers) after each refactor, without retaining pairs. Controls: capture
constructor default control bits and verify unchanged after both refactors (three
fixed-length traversals per lifecycle); q is constructor default, not a mutable knob.
No extra metadata extraction or native Info query. Check current wrapper/input CSC
storage independence at constructor and each refactor without retaining old owners.
All these diagnostic scans/bookkeeping are included outer overhead, not neutral.
The kernel's own _hh_direction_status adds six finite/equality scans; prepared solves
copy two length48 vectors each; updates copy prepared_partial once each; packing scans
u twice and unit support twice per update. Retirement bookkeeping scales with three
records; retained pool payload scales with packed entries. Sparse triangular work and
history applications depend on factor fill and packed support, which are not predicted
from input nnz alone. Unit transpose includes reachability traversal and sorting.

After each lifecycle, outside timing: verify 24 finite outputs and the same 64eps
formula in Float64 using preallocated residual scratch (ordinary arithmetic may round);
record the residual/scaling numbers, stop on a failed runtime check. This uses 24
matrix-vector residual evaluations per lifecycle, 960 total, no basis/native solves.
After exit, independently recompute ALL960 inequalities using exact rationals from
frozen input bits/output bits. Runtime passing does not substitute for exact audit;
a post-exit failure rejects evidence and never triggers rerun. Recheck input bits and
store scalars outside windows. Do not calculate extra floating factorizations.
Bounded pair comparisons use all24 numeric outputs per lifecycle; differences remain
in raw evidence and prohibit attributing cost differences purely to symbolic work.

Julia @timed bytes/events are aggregate GC counters, potentially including native
jl_* allocation activity (O), not exclusively Julia objects or live native memory.
GC-time is a runtime timing field, not proof that every finalizer/free completed.
RSS/high-water from guard are process descriptors only, not a retention oracle.
Native retention remains OPEN irrespective of GC completion or flat memory curves.
Report per-fixture8 pairs: ratios/median/range/MAD, absolute outer and inner times,
allocation bytes/events and GC. Short one-process fixed-history samples do not establish
end-to-end/universal speedup. No isolated native, symbolic-kernel or native-free claim.

## Preflight, single launch and closure

Fresh independent host call verifies boot/start ticks/command, last runner15915
(start670009,group15914) and child15916(start670093,group15916), BOTH FULL groups,
and any Julia absent. Verify actual refs/user hashes; source matches G and master.
Pin exact clone/inverse production, all src/test/runtime/env/native libraries/inputs,
driver/launcher/this plan BEFORE one guarded launch. Record actual loaded library paths
without extra native calls. Julia/BLAS1, heap2GiB, VM8GiB, availableRAM>=6GiB,
swap<=1GiB, wall600. Forbidden big/largo/AnyMOD and aliases. No pinned edits while active.
Keep original driver and all raw outputs after any failure; no opportunistic retries.
A post-exit auditor is separately hashed, never retroactively called a launch pin.
Verify process.json, exit, whole process groups, full independent pins/user files,
actual source/clone, exact inputs/960 residuals, counters, compile fields and raw/portable
identity. Exit0 alone is insufficient. Independent numerical/work review before any
acceptance; update STATUS/roadmap/continuation and push diagnostic branch only.
No production/test/CI/env edit, no hook experiment, no old accepted scripts/corpus/cost
reruns. Native reuse stays disabled; native retention, other consumers/controls,
other precisions/platforms, fullsuite and broader S4/S6 remain OPEN. All rejections stay.
