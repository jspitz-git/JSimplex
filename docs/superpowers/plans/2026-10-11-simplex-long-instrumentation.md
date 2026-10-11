# S0 long phase-II instrumentation implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans,
> inline and sequentially. Keep numerical jobs exclusive and guarded.

**Goal:** Obtain trustworthy chronological work evidence for a live long solve.
**Architecture:** Diagnostic-only scalar counters replace per-call timers. A
bounded observer streams phase/1024-step windows; cold regions get explicit
boundaries. Calibration precedes any long reference.
**Tech Stack:** Julia Test/TOML/SHA, existing Python guarded_run.py.
**Spec:** [Long-run protocol](../../../diagnostics/simplex-core-architecture/LONG-PHASE-II.md).

## Global constraints

One numerical Julia process, one Julia/BLAS thread, heap hint 2G, 8 GiB virtual
memory, >=6 GiB available RAM, <=1 GiB used swap. Preserve all worktrees and local
environments. Baseline source is the preserved 7d6a8e1 tree (production fe839aa),
not the integrated S1 candidate. Never change pinned files while running.
HH/native160, legacy/default native numerical policy, no performance adaptation,
unchanged tolerances/safeguards. Record all effective options and policy fields.
Only the allowed frozen inputs; no forbidden model/alias parsing or factorization.

## Review focus

- Short-circuit checks: count executed vector lengths, not a calls multiplier.
- Candidate staging: use the existing live diagnostic observer so rejected or
  delayed candidate completion events cannot become accepted-step counts.
- Count coverage: distinguish pipeline solve requests by operation/direction from
  exceptional high-precision refinement calls; never label requests all raw solves.
- Streaming: fixed counters/ring history, no retained workspace or per-step hashes;
  final/incomplete windows must remain intelligible after a guard termination.
- Instrumentation exceptions and nested cold regions: preserve solver exceptions,
  count failed work and restore recorder nesting; no replacement numerical result.

## L1: count-only probes

Files: reproduce/long_counters.jl, reproduce/long_counter_tests.jl under
`diagnostics/simplex-core-architecture/`; no production edits.
Interface: `install_long_counters!(JS, source_root)`, `reset_long_counters!(JS)`,
`long_counter_rows(JS)`. Fixed Int64 counter vector is owned by each instrumented
module. Installation is single-shot and fails on missing/ambiguous source hooks.

- [x] Write diagnostic tests for zero/reset, one finite call with exact executed
  lengths (valid/Dantzig/early-return), pipeline role/direction, failed-call count
  and duplicate-install refusal. Run RED before implementing hooks.
- [x] Implement count-only AST entry probes for the existing census operations,
  direct HH refactorization/projection, support rebuilds, candidate copies and
  certificate calls. Add finite vector-length and pipeline-role counters.
  Preserve original bodies/returns/exception behavior; no per-call clocks/GC.
- [x] Run guarded normal-mode tests; require pass and stable counter storage.

## L2: streaming and calibration

Files: reproduce/long_windows.jl, reproduce/long_calibration.jl,
reproduce/long_measure.jl and named diagnostic tests.
Interfaces: `LongRecorder(io, JS)` owns only bounded metadata; its `(event, ws)`
observer writes a phase boundary or every 1024 accepted steps. `finish!(recorder)`
writes the partial window; it does not certify a solution.

- [ ] Test window boundaries, offsets/phase algorithms, staged rejection,
  exception unwind and constant retained storage before implementing streaming.
- [ ] Add time/GC/allocation deltas only at windows and cold section boundaries
  (presolve, initialization, refactorization, recovery, projection, cleanup entry,
  final certification). Use nesting to avoid double attribution; report window
  wall time separately from exclusive region totals.
- [ ] Verify plain/counted state+event fingerprints in separate trace mode on
  frozen sparse/dense fixtures and a bounded medium prefix. Hashes are excluded
  from authoritative timing; no snapshots used as restart state.
- [ ] Warm independently, interleave >=3 plain/counted pairs for each calibration
  case and both algorithms. Require zero measured compilation, <=5% median
  overhead and no accumulating retention. Report ranges/allocations/GC, including
  failed calibration. Reduce density or use count-only if the budget fails.

## L3: serial live references

- [ ] Independent diagnostic correctness/work/memory review before long launch.
- [ ] Freeze each exact command/input/source/env; stream a fresh medium dual live
  solve then primal in separate guarded attempts. Preserve all phase/recovery
  state. Use the calibrated mode; separate plain solve is authoritative for time.
- [ ] Audit actual phase-II coverage, original feasibility/certificate, normal
  exit and unchanged pins. A resource/time limit is incomplete, not success.
- [ ] Commit compact evidence and update parent roadmap/STATUS at each gate.

Ruling: L1 is a separately testable first gate. Do not launch a long solve merely
because counters pass; L2/L3 remain mandatory. The old census cannot meet the
long-run timing claim from its runtime timings (large GC-dependent overhead).
Self-review: all protocol requirements map to L1–L3; no production API or future
S2 estimator is introduced. Execution is already authorized by the parent plan.

L1: counts-red-1 failed on the missing implementation; counts-green-1 passed
39 assertions with normal compilation, exit0/pins unchanged. Counter storage
is stable across resets, early returns count only executed arrays, role/direction
and failed calls are covered.

Ruling: run a count-only pilot before L2 streaming because it is a lower bound
on instrumentation overhead. Five interleaved pairs of 32 prepared HH kernels
(sparse/dense) test the new probes with less short-sample noise. Event/state
checks are separate. A pass does not replace the full <=5% chronology/medium
calibration; failure identifies a cost problem before building more recorder work.

L2 checkpoint: windows-red-1 expected missing implementation; windows-green-1
parse failure (preserved), fixed const-assignment spacing; windows-green-2
implementation check plus 18 boundary/staging tests pass. window-pilot-1 finished
exit0/pins unchanged but fails the sparse <=5% median-overhead budget: +11.90%
sparse, +2.02% dense. Do not mark L2 calibrated. Raw logs/results preserved.

Stopped at the user's requested problem boundary. Next: isolate/reduce event
bookkeeping overhead and test recorder+trace ordering together before a new
calibration attempt. No long reference or further numerical job is active.
The threshold and numerical protections remain unchanged.

Resumed: event-ablation-1 compares four diagnostic modes in one baseline module.
Medians per 64 sparse kernels: none 1.3991 ms, counts 1.5079 ms (+7.78%), noop
1.527499 ms, recorder 1.520899 ms (+8.71%). All operation counts, states and steps
match; zero measured compilation; no periodic writes or cold regions execute.
This identifies generic diagnostic bookkeeping as the main measured cost.

Chosen diagnostic-only fix: specialize record_event! for this script's owned
observer marker. Preserve valid-event checking, existing callback wrapping and
_StageObserver buffering; omit the unused duplicate dictionary/history. Generic
public observers and bulk pricing-work counters retain their behavior. A trace
composition uses the same owned dispatch only in verification, avoiding a trace
field or branch in timed recorder calls. No production files are edited.
RED event-sink test: 9 pass / 3 expected duplicate-history/work failures.

Event-sink GREEN: 14/14 pass, exit0/pins unchanged. window-pilot-2 now verifies
the actual recorder+trace composition with native160; both fingerprints match.
Five interleaved pairs, compile0: sparse +8.78% fails, dense +1.71% passes.
L2 remains unaccepted. Independent static review found no numerical or added
work/retention defect; P2 direct-event/committed-recovery coverage is documented
in the script and report and remains a long-reference prerequisite.
Next matched-mode ablation must identify remaining cost before another pilot;
consider reduced-density/count-only mode without losing required coverage.
All eleven attempts stopped and retained. No long reference or production change.
