# MA-V offline preparation admission

Scope: prepare one NEW two-process qualification of the frozen MA-U Bool rounding
guard, under MA-T Task2. This document and its preparation review do not launch
Julia. No Julia query, parser, import, compilation, numerical or guard/launcher main
has run during preparation. All runtime/compiler/cost statements below are gates,
not observations. MA-S-2 remains rejected48/52; Rational controls remain unresolved.
No production/test/environment/CI/master change or automatic promotion.

## Exact loading and runtime

commands.json contains exactly two commands, process1/run-1 and process2/run-2.
The existing pinned shell wrapper loads Julia1.13.0 aarch64, installed MA SaQfc,
and the unchanged MA-R diagnostic environment, compiled-modules=existing,
threads1/gcthreads1,0/heap2GiB. Guard enforces VM8GiB, availableRAM>=6GiB,
swap<=1GiB and single Julia. No package install, precompile request or import probe.
Runtime VERSION and JSimplex/MA loaded paths are refused on mismatch; all actual
loaded module paths must belong to fresh pins. This is ordinary-loader admission,
not cache confinement, complete import-work or native allocation/free proof.

Both diagnostic modules are defined at top level before main(), so calls cannot
see a partially loaded candidate. OldArm contains exact MA-R reference/candidate;
NewArm contains exact MA-U reference/candidate/instrumented entries. No production
method is overwritten. The two new test copies change ONLY diagnostic recording
and the fixture include path; source-check.json gives exact inverse edits.
The original MA-U test functions/assertions/setup/order remain intact. No old
160-case qualification or frozen launcher/auditor is rerun.

## Prospective schedule and raw gates

schedule.json fixes 12 whole-call cases, two old-arm RED cases and six micro cases.
Process1: generated-code gate, ten timer baselines, two RED cases, complete MA-U
correctness, six micro cases, twelve whole-call cases. Process2: generated-code
gate, ten timer baselines, six micro cases, twelve whole-call cases. No other
numerical calls or retry. All costs use3warm+7measured alternating pairs; index,
case and pair determine order. Whole windows4calls; micro windows256calls.
Correctness270predicate+25transition+optional1no-scope,840whole cases,844calls per
original/new/instrumented arm. Exact descriptors, expected modes, exceptions,
output token shapes, route/scratch/fallback counters and test success are checked
by audit.py, not inferred from exit0. See work-ledger.md for full named-entry budget.

RED requires old-candidate-minus-direct-reference side-median bytes OR events >0
in EACH of two dense32 scopedUp F/B cases. Both numerical/owner and compile0 checks
must pass. Unexpected absence of this regression stops before correctness/new
cost; import failure is never RED. No old numerical failure or heap-object cause
is inferred. All old recorded evidence remains unchanged.

Micro batch consists of256 explicit calls to a monomorphic @noinline probe.
The tag is specialized in microwindow BEFORE its timer. Both probes use the same
static call boundary and Int accumulation; no invokelatest, dynamic invocation,
precomputed Bool or effects promise. Before any measured work, code_llvm captures
both batch and probe bodies (four files/process). Batch IR must contain exactly256
direct j_probe calls and no indirect/generic apply call; failure stops without
alternative micro strategy or investigation. File size is bounded1MiB each and
probe IR sizes are reported for local code-growth review, not native-code bytes.
Compiler specialization is performed outside windows; measuredcompile/recompile0
is still mandatory. Ten empty-timer samples/process characterize timer scaffolding;
measured bytes/events must be0. They do not estimate/subtract probe call overhead.
Micro time is descriptive only; whole-call timings decide performance acceptance.
Every new-helper measured micro window must independently have0bytes/0events.
No baseline subtraction. This finite IR/source gate remains UNEXECUTED.

Whole-call setup, contexts, copies, resets and snapshots are outside windows;
all eligibility checks and private MA product scratch are inside each candidate
call. All output finite exact tokens, signs, precision, NaN/Inf class and input
values/owners are compared outside windows. Allocation bytes/events are raw
aggregate GC counters, potentially including native traffic, not live memory.
All GC and outliers are retained. No profiler or explicit GC in timed windows.

Reducers are EXACTLY MA-T: each window time/4; per-process side median7 samples;
pooled side median14 samples, always per individual case. Positive reference time.
Byte/event side medians7 raw window totals, never median paired differences.
Mismatch/n15: candidate-reference bytes/events <=0 in EACH process; time delta
<=max(10% reference,0.4microseconds) EACH process and <=max(5%,0.2microseconds)
pooled. Absent/equal32: bytes AND events strictly less EACH process, candidate/
reference side-median time ratio <1 EACH process and pooled. Paired ratios/deltas
are reported separately. Every per-process cost gate is audited before process2;
pooled gate remains final. No pooling away one direction, size, mode or layout.
These are engineering budgets, not statistical significance or solver speedup.

## Failure preservation and ceilings

The new append-only partial-windows.toml journal flushes completed window metrics
before output comparisons, then enriched whole-call value/owner results before
assertion. It also records micro checksums, baseline windows and correctness
records. It lives outside timed windows, has bounded fixed schedule cost and is
checked against final raw on success. A killed process may leave a final partial
TOML tail; preserve it and logs verbatim, never repair into an accepted result.
Completed flushes survive process termination, not an fsync/power-loss guarantee.
An exception inside @timed before return has no completed sample; progress/errors
and process logs identify it. Early load failure may have no raw or journal.
Final raw is written in finally when possible; fail-closed schema refuses missing
or incomplete records. Partial correctness records stay available on test failure.

One exclusive sequence reservation, two serial processes, no retry. Inner guard
absolute deadline84s includes its prelaunch hashing; supervisor independently waits
only to84s then sends identity-checked TERM, to88s then KILLs verified child members
and guard, and waits at most to90s. Any timeout, incomplete cleanup, exit error,
90s overrun or180s cumulative guard invocation overrun rejects and stops. The
supervisor also bounds post-child guard hashing/housekeeping; no unbounded wait.
As with OS deadlines, scheduling latency can make the observed limit fail; no
claim of hard real-time scheduling is made. Post-run identity/PGID/session/noJulia
checks are mandatory; failure never permits another launch. Offline preflight,
review, full-pin validation and audit time are additional nonnumerical wall time.

Before a future run, fresh launch-context.json must bind actual published refs,
remote refs, boot ID, full166historical groups ANDsessions and noJulia, plus standing
short-run permission and exact2/90limits. A new independent numerical-review.json
must accept the exact manifest, preparation review and context with mandatory
membership and exact hashes. Those files, sequence/reservations/outputs do not yet
exist. launcher.py refuses their absence. Preserve currently pinned continuation
bytes before any subsequent change; current MA-V review/publication mappings must
be handled explicitly. A new runtime/input drift requires a separate amendment,
never silent repinning of this admission. No hours-long job is authorized.

## Review and result boundary

Review mathematical/numerical equivalence, aliases/exceptions, private API drift,
whole-call work and memory, diagnostic retention and actual guard attempt caps.
Fresh gpt-6-astra preparation review follows the manifest. Later independent
numerical seal precedes launch; independent result review follows it. Even a local
PASS only qualifies this guard strategy, not all DenseLU controls or production.
MA-S-2 Rational no-increase gates remain open. Master6f68e24 unchanged; broader
plan OPEN, CI disabled, HH reuse disabled, automation paused.
