# S4-M: bounded whole-HH symbolic reuse cost observations

Future execution only, after S4-L acceptance. No production/test edits, method
overwrite, CI enablement, old driver/corpus/reference/cost rerun or promotion.
Use a NEW exact-source HH clone: only three routing names and Float64 reuse keyword
become the actual `_same_umfpack_pattern` guard. Prove inverse source equality and
freeze clone/driver/inputs/this plan BEFORE Julia. Both sides use real HH constructors.

## Fixed new inputs

Two fixtures, each n=96, Float64/Int64 CSC, sorted one-based indices:
- sparse: include exactly |i-j|<=2, nnz=474;
- dense: include every entry, nnz=9216.

Indices i,j are one-based. For phase p in {0,1}, diagonal entry is
`8 + (i mod 7)/64 + p/8`. Every included off-diagonal entry is
`(-1)^(i+j) * (8+p)/8192`. No stored zero, coefficient removal or random input.
These symmetric strictly diagonally dominant matrices are new fixtures, not old
B/C/D matrices. All entries are exactly representable binary64. Build two owned
phase matrices per side per fixture: eight CSC inputs; no per-refactor construction
or value mutation. Inputs are never shared between sides and must remain bit-exact.

Precompute OFFLINE exact rational matrices and both RHS per phase. Known forward
solution zF[i]=(-1)^i and known transpose solution zB[i]=(i mod 3)-1; bF=B*zF,
bB=transpose(B)*zB. These small dyadic sums are exact binary64; assert roundtrip bits
before launch. Freeze JSON bits, rational RHS, dimensions/nnz, input hashes and
strict dominance check. No post-output selection of scale or tolerances.

For every saved finite output z and its exact M=B or transpose(B), require
`||M*z-b||inf <= 64*2^-52*max(1, ||M||inf*||z||inf, ||b||inf)`
using exact rational interpretation of captured binary64. Also require the expected
unique solution's exact residual zero offline. Never raise precision inside Julia
or add refinement/certificate calls to satisfy this diagnostic oracle.

## Order, fixed counts and timing boundary

Four factors (sparse reference/candidate, dense reference/candidate), kept in one
owned container, each constructor once on phase0. Record setup separately; each
initial factor gets exactly one direct FTRAN and one direct BTRAN for phase0.
Default controls/q=nothing/IRSTEP0; capture bitwise controls once and verify after
each batch. No updates, factor copies, workspaces, solver iterations or observers.

Use one typed batch function per route; it loops exactly16 whole HH refactor calls
on the same prebuilt phase matrix and returns nothing. Use the SAME `@timed` helper
for warmup and measured calls. Entry counters increment BEFORE constructor/refactor/
solve calls; throw attempts must not disappear. Counter increments inside the batch
are equal on both sides and are included in its measured overhead.

Warmup: fixture order sparse then dense; per fixture phase0 then phase1, each with
reference then candidate. Thus2 batches per factor,16calls each=128 warmup refactors.
After EACH batch snapshot native info scalars, then exactly one FTRAN and BTRAN
using that phase's prebuilt RHS. Keep warmup records (including compilation), never
add warmups opportunistically. Record setup/warmup elapsed and allocation totals
separately from steady measurements.

Measured: eight rounds, fixture order sparse then dense. Round r uses phase
floor((r-1)/2) mod2 (0,0,1,1,0,0,1,1). Odd rounds reference then candidate; even rounds candidate then reference.
One16-call batch per side per fixture each round:32 samples,16 paired observations,
512 measured refactors. Explicit full GC before EACH batch, outside @timed; none
explicitly inside. Natural in-window GC remains in elapsed and is recorded.
After EVERY batch copy native info scalars before further native activity, and
perform exactly one direct FTRAN and BTRAN for that phase outside the timed region.
Freeze all outputs as owned binary64 vectors, plus small current-base fingerprints
(L/U/p/q/scaling from HH-owned fields only; no native metadata extraction call).
Compare each measured pair's numerical endpoint/factor fingerprints; differences
must be retained and prohibit pure-symbolic/kernel-only speed attribution.

All-pass totals:4 constructors +640 refactors (128warmup+512measured),644 successful
HH extractions;88 direct HH solves=44F+44B (8initial+16warmup+64measured).
SOURCE-DERIVED native numeric entries644, symbolic constructions reference322
(2initial+320refactors) and candidate2initial if all actual guards match; guard
comparisons320 on candidate refactors. Up to644 additional native orientation
validation solves, NOT an instrumented count. No update-internal solves. Both
routes retain their complete default extraction and safeguard work. Four initial
input assemblies are not additional to the eight prebuilt phase CSC matrices.

Every measured sample requires compile_time==0 and recompile_time==0. Any nonzero
value invalidates the steady gate; preserve samples and stop, do not subtract,
rerun, discard first observations or add rounds. Unexpected return/error, failed
numerical/control/ownership oracle or guard-resource violation stops the whole run,
with remaining cases explicitly UNEXECUTED. Initial/warmup compilation is allowed.

## Bounded observations of memory

Outside windows after warmup, after measured round4, after round8: full GC and one
checkpoint of the container of FOUR current factors (deduplicated Julia graph),
four sets of scalar native info/control values, and process /proc status. Thus3
joint graph traversals,12 per-factor memory records. Inputs/RHS/outputs live outside
that graph and their bounded storage is separately inventoried. Info SIZE_OF_UNIT
converts Units to bytes; use constants+1, never fixed word size. Report estimates
and symbolic-origin fields separately from current numeric fields. No extra native
API calls, graph copies, factor copies or solves for these checkpoints.

All 44 endpoint records retain two length96 outputs each (8448 Float64 elements),
scalar summaries and hashes only; no native pointer owner, old HH base, factor,
prepared buffer or shallow-copy reference. Fixed-size/preallocated diagnostic
storage; snapshots do not grow with refactor count. Batch/endpoint helpers return
nothing/fixed scalar records or owned output vectors, never old factors/owners.

After the final checkpoint leave the function owning the factor container, release
all four factors and use full GC outside timing, then record one further process
status. No manual finalize/free; do not retain factors in @timed.value, errors or
closures on successful path. Exceptional path preserves failure metadata safely
and makes no memory-retention acceptance claim. This fourth process checkpoint has
no factor graph/native info access and adds no constructor/solve/refactor.

Julia bytes/events measure traffic; graph sizes exclude native heap; native Info
sizes do not count all live/retired objects; RSS/highwater mix JIT, all allocators
and runtime. Full native-retention acceptance remains OPEN regardless of results.
No leak/no-leak conclusion from RSS alone, flat graph sizes or forced GC. Held-old-
owner identity assertions from prior tiny probes are explicitly excluded.

## Gate, analysis and postexit

Report all16 pairs grouped by sparse/dense (8pairs each): paired elapsed/byte/event
ratios, side medians, range and dispersion; retain absolute totals and GC times.
No one-pair speedup claim, no inference from unchanged allocations alone. A lower
observed median is local to these fixtures/platform, not current-master/end-to-end
speedup. Small/noisy samples may be inconclusive; fixed counts stand. No production
acceptance even if timing improves: native retention and other broader gates open.

Mandatory fresh actual refs, complete previous process-group absence with boot/
start_ticks/command identity, user hashes, runtime/env/native-library pins, exact
clone inverse, inputbits/defaultcontrol source preflight. One Julia/BLAS thread,
heap2GiB, VM8GiB, availableRAM6GiB, swap<=1GiB, wall600. No big/largo/AnyMOD or aliases.
No reset clocks, environmental changes or opportunistic retry. Pin all actual
src/test/runtime/env/driver/clone/plan/input/library sources before launch and do
not edit them while running. Save raw process/resources/exit/frozen sources and
portable copies. A postexit auditor gets a separate hash, never a retroactive
launch pin. Independently rehash all pins, verify actual sources/inputs/raw copies,
exact residuals, counts and complete process closure; exit0 alone insufficient.
Fresh independent numerical/work review; update STATUS/continuation and push only
diagnostics. No old accepted L/K/J/I/H/G/F/E scripts or numerical runs repeated.
