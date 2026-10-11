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

Ruling (continued execution): the user explicitly revoked stopping at calibration
failures. Preserve failed evidence, diagnose and continue until acceptance or a
true external blocker. Keep the 5% budget, all numerical/memory constraints and
long-reference prerequisites. Next owned ablation adds the specialized sink to
the original four-mode same-module comparison, so owned-noop versus recorder
separates remaining callback bookkeeping from recorder body cost.

owned-ablation-1 (exit0/pins unchanged): no diagnostics 1.4330ms, generic counts
1.490801ms, owned noop1.4645ms (+2.20%), recorder1.5157ms (+5.77%) per64 kernels.
State/steps/operation counts equal, compile0. New hypothesis: separate the cold
phase/output body and inline scalar observer filtering. This targets the measured
noop/recorder difference without dropping counters or changing the interval.
The existing failed overhead gate is the regression; rerun boundary/staging
semantics and a revised paired calibration after this code change.

window-pilot-3 completed with identical traces but failed sparse +12.49%;
dense +2.99%. Cold/hot splitting did not meet the gate; do not claim a speedup.
Next narrow change: replace the three/five generic pricing dictionary updates
with owned fixed counters, preserving public diagnostics and staged ownership.
Add cold committed-recovery and discarded-metadata counters simultaneously to
close review coverage. No new scans, solves, tolerances or numerical policy.

metadata-red-1 failed on absent counters; metadata-green-1 passed16. Fixed pricing
counts include staged/discarded work; cold direct recovery counts distinguish
committed checkpoint/repair/restore/pricing reset. Discarded metadata event total
is separate from accepted steps. Public diagnostic bodies remain the fallback.
window-pilot-4 passed sparse4.69%, dense2.62%, compile0 and full recorder+trace
agreement. Continue full-solve sparse/dense and bounded-medium calibration for
both algorithms, with final flush inside timing and retained recorder size.

Review correction plan: derive phase I/II from _report_simplex_phase before
verbose early return; derive actual algorithm from optimizer entry (covers
legacy reduced-LP primal cleanup); mark original cleanup at cleanup_original
entry, including its dual fallback. phase_* callbacks alone are insufficient.
Use a fixed bounded region stack plus base section so phase changes cannot erase
nested refactor/recovery/certification attribution; cleanup_entry ends when its
optimizer starts. Test nested transitions and exclusive totals before a new
calibration. Remove four redundant copies of already-copied metric columns.
solve-sparse-1 reached identical OPTIMAL dual traces but failed serialization
because TOML cannot encode the section-label tuple. Convert it to a vector;
the attempt is incomplete and has no accepted timed pairs.

Review fixes verified: phase RED1/3 -> GREEN19; actual phase/optimizer entry and
interrupted recovery publication16 pass. Five serial regression attempts pass
39/19/14/16/19. Follow-up static review has no blocker or unnecessary numerical
work/retention finding. Recalibrate current snapshot (old pilot is not transferable).
Ruling: reuse compilation across sparse,dense,medium within one numerical process,
fresh state each solve; this reduces repeated compilation without reusing solver
state or weakening per-case gates. Exact diagnostic source copies now accompany
each new attempt. All previous attempts remain preserved.

window-pilot-5: corrected chronology, exact fingerprints, compile0, exit0/pins
unchanged. Sparse5.1285% narrowly fails, dense1.8986% passes. Keep the threshold.
Ruling: run the already required full-solve/both-algorithm calibration to locate
cold/setup/output overhead and obtain independent medium-prefix coverage before
another density change. This does not accept the failed kernel or authorize a
long reference. No unchanged kernel rerun merely to seek a passing sample.

solve-suite-1 completed exit0/pins unchanged, all6 case/algorithm gates pass,
compile0 and matching traces. Sparse dual/primal3.41%/4.48%, dense-1.89%/3.63%,
medium3.24%/-4.27%. Recorder retained size2983B is constant. Medium64 prefixes
remain ITERATION_LIMIT, not solved models. Kernelpilot5 alone is still5.1285%.
Next narrowly scoped cost fix: remove per-increment bounds checks from the
internally owned fixed counter vector, after validating its shape at installation
and reset. This does not remove any numerical data check. Every index is a
validated schema literal or a literal plus Bool direction. No resize occurs
during a measured solve. Run shape regression and recalibrate changed snapshot.

Counter-shape RED39/1 -> GREEN40; metadata16 and phase19 remain green.
Review proves indices within H+23 fixed slots. Pricing previous[2:4] is also
inside @inbounds; the sole production caller supplies a fixed four-tuple.
window-pilot-6 passes sparse0.2608%/dense2.2118%, compile0 and exact traces.
solve-suite-2 is the current-snapshot full calibration; do not transfer suite1
numbers across the bounds-check change. Long driver preparation is outside pinned
files while the one guarded numerical process runs.

Full suite2: two rejected overhead gates (sparse primal15.70%, medium dual5.47%);
traces/compile0/retention pass. Next reviewed fix streams numeric TOML fields
without dictionaries/slices. Test full parsed-schema equality, escaped symbols,
input immutability, final-window continuity and output allocations. Six balanced
pairs are fixed before the new run, same5% limit, all earlier attempts preserved.
L3 driver review corrected the counter snapshot before untimed feasibility and
added a baseline path failfast. Post-exit audit tests10GREEN; smoke still pending.

Streaming RED fails on missing writer; GREEN10 preserves parsed schema, escapes,
input metadata and final continuity. First cost reporter failed on Dict inference
(String mode into Dict{String,Real}); corrected to Dict{String,Any}. Six isolated
writer pairs x256 windows, compile0: old6.8623ms/5537792B/116992alloc versus
stream1.88675ms/2445312B/71936alloc. No inference about solver speed from this.
Window19/nested-phase19 regressions pass; kernelpilot7 now calibrates streaming.

L3 execution detail (after current L2 acceptance): use long_measure.jl through
the same guard and baseline project; the driver rejects any other pathof(JS).
First validate counted sparse smoke and post-exit audit (normal exit, unchanged
pins, final marker/count, all window counter sums, actual phaseII steps, internal
OPTIMAL certificate plus independent final primal feasibility). Smoke cannot
qualify medium coverage. Only then freeze medium dual counted with1000000 steps,
time_limit=Inf and an external43200-second guard, keeping every memory constraint.
This budget allows the historical seven-hour trajectory plus warmup; expiration
still means incomplete. Plain elapsed and primal-origin reference remain separate
serial attempts, not inferred from the counted run. Do not start any long job
while a calibration or smoke gate is unresolved.

window-pilot-7: sparse2.13% passes, dense5.3384% fails despite lower output
allocations (19168 extraB/566 events for two writes). Dense samples range23–26ms;
within-pair differences are -3.84%,-0.84%,+13.62%,+0.52%,+2.85%, indicating noise
and order imbalance. Do not call this accepted. Ruling: improve measurement
resolution once with a predeclared128-kernel batch and6 balanced pairs (formerly
32/five). No instrumentation change, same5% gate, no discarded samples; this is
a concrete sampling-method correction, not repeated unchanged runs until pass.
The larger sparse batch also exercises its first periodic write (1152 steps),
closing the former no-output sparse kernel regime. Full six-pair solve gate and
smoke remain independent requirements. If this fails, diagnose/reduce probe
density; do not keep increasing repeat counts to seek acceptance.

Pilot8 completed: sparse6.5645% rejects, dense1.9616% passes, exact states and
compile0. Larger sampling did not resolve the gate. Ruling: follow protocol's
reduced-density path; omit8 entry probes for iteration/dispatch/auto-edge wrappers
and pricing selectors, while retaining pricing work metadata, actual ratio/DSE
kernels, finite visits, reconstruction, residual checks, pipeline roles, support,
candidate copies, all cold regions and certification/recovery. No numerical body
or check is removed. Reports list omitted entries, which must not be read as zero
calls. Counter tests and fresh kernel/full gates are required; keep batch/pairs
and threshold unchanged. Also move full-calibration count snapshot before the
untimed final primal check, matching the already reviewed L3 driver fix.
