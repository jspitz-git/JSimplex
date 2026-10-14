# MA-Y fallback cost failures: stored-result and source analysis

MA-Y remains NOT ACCEPTED. The two failed predicates are reproduced from the
unchanged data; neither an auditor defect nor a fixed new arithmetic/allocation
cost is established. The BigFloat failure is localized to variable whole-call
timings and different order statistics, with residual guard work still present.
The Rational failure is a small positive difference of separately ranked byte
medians within two-sided native-inclusive allocation variation. Its exact runtime
cause remains unresolved. No measurement, Julia query/parser/import/compilation,
profiler, disassembler, old auditor or aggregate was run again.

## Scope and provenance

The direct human request authorizes this new SOURCE/STORED-EVIDENCE investigation,
superseding MA-Y's prohibition on an *automatic* immediate allocator investigation.
It does not authorize a retry, gate waiver, modified candidate or new numerical
plan. Fresh entry12 verifies published diagnostic db4f50c and master6f68e24,
514 source identities, six protected user files, all75 prior committed blobs and
74 publication hashes. Fresh boot/start_ticks/command/full176 process groups OR
sessions finds no old process or Julia. Beforecopies preserve the six current
MA-Y closure/publication/continuation STATUS/roadmap bindings; older maps unchanged.

New analyze.py was saved before its single execution. Its20checks and36readtime
hashes cover all16 controls in all3 processes:480 total pairs,336 measured and144
warm. The960 control windows match both original journal records exactly; every
measured window retains zero compile/recompile, output equality and input/owner
preservation. All windows, GC and outliers stay in the evidence. Thirteen read files
also match original MA-X launch pins; new readtime hashes are not retroactive pins.
The existing S4-O native instructions and binary are hash-matched to the MA-Y
launch inventory, without regenerating disassembly or loading libraries.

This is a descriptive decomposition of the rejected controls. It does not run or
emulate the forbidden pooled52-case acceptance after the failed third stage.

## BigFloat BTRAN: what actually determines the failed median

The n32 scoped control sets global RoundNearest and scoped RoundUp. MA-U checks
BigFloat vector/backend types and dimensions, then reads the current scope with
an inline KeyValue.get and compares its mode against the global mode. Mismatch
returns directly to reference_transpose!. The product=BigFloat() scratch and MA
multiply/triangular loops are after this return and are not on this source path.
The reference delegates to the original ldiv! with transpose(factorization).

There is still one eligibility check and one scope lookup per call relative to
direct reference. It adds no factor scan, solve, numerical conversion, copy or
scratch on this fallback. Scope lookup traverses the current persistent map; its
work depends on scope storage, not matrix nonzeros or update-chain length. Source
cannot establish its emitted instructions or isolated timing cost. In particular,
zero extra allocation does not imply zero execution time.

All42 measured scoped BigFloat pairs (both directions, all processes,21 in each
side order) have exactly equal bytes AND event counts. The previous MA-S-2 constant
+128bytes/+8events per four-call window is absent in MA-Y. Do not reuse that older
rounding-lookup allocation explanation for the current time failure. This is a
comparison of separate saved experiments, not a new matched causal experiment.

Here are ALL seven measured BTRAN pairs in process3. Times are microseconds per
call (each window contains four calls), GC is seconds per whole window.

| Pair | Order | Reference us | Candidate us | C minus R us | Reference GC s | Candidate GC s |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 4 | C,R | 356.350 | 455.375 | 99.025 | 0 | 0 |
| 5 | R,C | 351.175 | 351.150 | -0.025 | 0 | 0 |
| 6 | C,R | 290.550 | 279.525 | -11.025 | 0 | 0 |
| 7 | R,C | 299.575 | 386.425 | 86.850 | 0 | 0 |
| 8 | C,R | 7091.650 | 360.425 | -6731.225 | 0.0171974 | 0 |
| 9 | R,C | 247.675 | 249.825 | 2.150 | 0 | 0 |
| 10 | C,R | 249.250 | 251.075 | 1.825 | 0 | 0 |

Reference time ranks are pairs9,10,6,7,5,4,8; its median is pair7,299.575us.
Candidate ranks are9,10,6,5,8,7,4; its median is pair5,351.150us. The admitted
side-median difference is51.575us, above29.9575us. Candidate/reference side-median
ratio is about1.17216, whereas median of the seven matched ratios is1.007321966.
Different statistics need not agree: the median pair is NOT the same observation
on both sides. This fully explains the arithmetic of the failed predicate, not
the physical cause of the individual durations. Neither statistic replaces the
other after the fact.

Candidate excesses in pairs4 and7 have no recorded in-window GC or compilation,
and occur in opposite execution orders. The largest duration is reference pair8,
with GC; it cannot directly explain those candidate excesses as candidate GC.
The median reference observation itself has GC=0. GC can still affect allocation
history and ranking; no sample is removed or GC time subtracted. The observed
pair differences are not a constant51.575us per call; they do not isolate any
fixed guard component from variable whole-call costs. Recorded compilation is
zero throughout. A universal candidate-second-only explanation also fails because
both execution orders contain candidate excesses.

Processes1/2 have side medians244.850/247.825us and251.525/257.125us and pass. Their
matched-ratio medians1.012150296 and1.010054138 are descriptive only. Process3's
late pairs9/10 return to roughly248–251us on both sides. These observations are
consistent with time-varying measurement conditions and small residual guard
work, but do not prove scheduling, CPU frequency, cache, allocator or guard cost
as the cause. Saved resources contain elapsed time, available RAM/swap and child
memory, not per-window CPU time, frequency, scheduling events or guard profiles.
There are no absolute start/end timestamps for individual cost windows. Host
memory records cannot reconstruct which external event affected which call.

## Rational FTRAN: why equal events do not settle byte acceptance

Rational{BigInt} fails the FIRST BigFloat type test. It does not inspect matrix
dimensions, look up rounding, allocate product scratch or enter any MA loop.
It directly calls reference_forward! with the same arguments. No new rational
multiply/subtract/divide, vector traversal, conversion or copy appears in this
source path. Whether all wrapper work is optimized away is not captured.

Process3 retains74,525events per window on BOTH sides in all seven pairs:

| Pair | Order | Reference bytes | Candidate bytes | C minus R bytes |
| --- | --- | ---: | ---: | ---: |
| 4 | R,C | 3247392 | 3247440 | 48 |
| 5 | C,R | 3247312 | 3247728 | 416 |
| 6 | R,C | 3247520 | 3247568 | 48 |
| 7 | C,R | 3247312 | 3247408 | 96 |
| 8 | R,C | 3247408 | 3247360 | -48 |
| 9 | C,R | 3247376 | 3247360 | -16 |
| 10 | R,C | 3247328 | 3247344 | 16 |

No measured FTRAN pair in any process has recorded GC. In process3, the reference
byte median is pair9,3247376; the candidate median is pair7,3247408: +32bytes per
four-call window. Median of the seven paired differences is+48bytes. Neither is
a fixed per-call allocation, and the nonzero byte tolerance remains ZERO.
Processes1/2 instead have side-median deltas-16/-16bytes; process1's paired-delta
median is+64bytes despite its negative difference of side medians. Choosing a
different statistic would change the original rule, not repair its arithmetic.

Across all42 measured Rational FTRAN/BTRAN pairs,20 byte deltas are positive,
18 negative and4 zero, ranging from-22448 to+416bytes; all event deltas are zero.
There are21pairs of each side order. The large negative delta occurs with reference
GC in process2 BTRAN pair4. Even the41 pairs with no recorded GC span-560 to+416;
that descriptive observation rejects a GC-only explanation and is not a filtered
acceptance result. All42 remain included. Float64's42 and small BigFloat's210
control pairs have zero byte/event differences throughout.

Installed timing.jl records byte deltas from allocd+deferred_alloc+total_allocd;
events sum malloc+realloc+poolalloc+bigalloc. They are different aggregates, not
requested payload bytes and not a live-memory ledger. gmp.jl builds fresh BigInt
numerator/denominator owners for rational arithmetic on both sides and attempts
to install counted malloc/realloc/free callbacks. Its initialization catches
errors, so installed source alone does not prove historical callback state.

The already stored, exact-binary-matched instructions show counted malloc charging
malloc_usable_size for a successful allocation with a current task. Counted
realloc-with-old-size increments an event separately from charging nonnegative
new usable size minus supplied old size. Thus equal aggregate event counts can
coexist with different charged bytes. The old size is the callback argument, not
proof of the prior block's usable size. The observed16byte multiples are compatible
with this mechanism but do not identify any size class or actual request.

Both arms use separately deepcopied bundles with equal values, not identical
object addresses or allocator histories. Every window resets destination
references outside timing, then performs four original solves; each solve still
has its original ldiv! copies/arithmetic. Tokens, ownership scans and two flushed
journal records per window occur outside timing and may influence later GC or
allocator state. No emitted-code, allocation-site/category, GMP request/pointer,
old/new usable-size or actual callback trace is saved. The variable +32byte median
cannot be assigned to a specific wrapper allocation, arithmetic operation, GMP
size class or physical memory increase from these data.

## Decision and next useful boundary

The accounting mechanism is a source-supported explanation for how the Rational
observation is possible; the particular runtime cause is unproved. Likewise the
BigFloat rank decomposition localizes the failed statistic but does not establish
a performance defect in the guard. Do not delete checks, change scoped semantics,
add a byte tolerance, subtract GC, swap statistics or promote the rejected result.
No justified production fix follows from the available evidence alone.

If further work is requested, its useful question is causal attribution, with a
separately reviewed design for separating guard work from whole-call timing and
for distinguishing requested/native-usable bytes from aggregate events. A plain
repeat of the unchanged52-case measurement would not provide the missing traces.
No driver, candidate, numerical admission or automatic rerun is created here.

No new production work, allocations or retained memory were introduced. Existing
fallback guard work is bounded as above; whether it explains material elapsed cost
is unresolved. Existing diagnostic copies/scans/serialization may perturb later
state and are not neutral. This offline analysis stores scalar summaries for480
pairs and reads fixed existing files; it adds no solver scans, basis solves,
conversions, caches or retained native objects. No native-free, observer-neutrality,
public-solver speedup or complete backend-work claim is made. Master/source/test/
environment/CI remain unchanged, HH reuse disabled, automation paused. Broader
performance work stays open. All previous raw, scripts, reviews and failed gates
remain frozen and their decisions unchanged.
