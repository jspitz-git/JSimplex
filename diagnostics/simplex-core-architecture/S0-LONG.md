# S0-L: long phase-II instrumentation work

Status: chronological pilot rejected by the <=5% overhead gate. Count-only
pilot passed. No long reference; further execution stopped at this problem.
Source baseline: preserved 7d6a8e1 (production fe839aa). Production changes are
not part of these diagnostic-only experiments.
Plan: [instrumentation subplan](../../docs/superpowers/plans/2026-10-11-simplex-long-instrumentation.md).

## Counters

Fixed Int64 storage counts function entries without per-call clocks or GC probes.
Executed hardware-float finite scans contribute their actual vector lengths;
short-circuited arrays do not. Pipeline requests are classified by declared
operation and direction; they are not silently equated to all raw factor solves.
Exceptional refinement calls, support rebuilds, candidate copies, certification,
HH refactorization and postsolve projection have separate labels. Counter schema
is fixed; resets keep the original vector. No solver arrays are retained.

counts-red-1 failed on the missing implementation. counts-green-1 passed 39
assertions in normal compilation, exit0/pins unchanged. Tests cover reset/storage,
Dantzig and early-return element visits, role/direction and failed-call counts.
An initial launcher error occurred before Julia because the new stage directory
was absent; the corrected launch is the first numerical RED attempt.

The count-only pilot used five interleaved pairs of 32 prepared dual HH kernels
for each sparse/dense fixture. Timed interval uses native160; independent trace
verification uses the prior helper's native320, with matching states and no
interval-triggered refactorization in these short kernels. Measured compilation
is zero, allocated bytes/counts equal, and event/state checks passed separately.

| Model | Plain median ms (range) | Counted median ms (range) | Relative median difference |
| --- | ---: | ---: | ---: |
| sparse | 0.7795 (0.7127–0.7961) | 0.7505 (0.7457–0.8249) | -3.72% |
| dense | 22.7582 (22.6691–23.7960) | 22.9582 (22.2718–23.3533) | +0.88% |

Both meet the pilot <=5% budget. The negative sparse difference is measurement
scatter, not a claim that adding probes accelerates the solver. This lower-bound
pilot does not qualify the full chronological recorder or a medium long run.

## Chronological recorder

A concrete observer owns fixed metadata/counter snapshots and streams TOML
windows on phase changes and each 1024 accepted steps. It stores no workspace,
factorization or per-pivot state hash. Existing live diagnostic dispatch preserves
candidate staging; rejected deferred completions are not accepted steps. Cold
regions use nested exclusive time/GC/allocation buckets. Recorder output costs
are charged to the next window's instrumentation bucket; finish! returns the
last output tail separately. Authoritative elapsed measurements include all work
inside their declared timed region; no estimated overhead is subtracted.

windows-red-1 failed on the missing implementation. windows-green-1 found a
parse error in generated const assignments with names ending in `!`; whitespace
fixed it. The original failed source is retained. windows-green-2 passed the
implementation check and 18 boundary/staging assertions, exit0/pins unchanged.
Real region-hook installation and elapsed cost are exercised by window-pilot-1.

All raw attempts and snapshots remain under
`.superpowers/simplex-core-architecture/S0-L/`; portable records are in
results/S0-L/. One guarded Julia process runs at a time, with unchanged baseline
environment and the established memory/swap limits. No excluded model was read
by numerical code. L2 medium/both-algorithm calibration and L3 review/reference
remain open regardless of the small-kernel pilot outcome.

## Chronological pilot: budget rejection

window-pilot-1 exited 0 with unchanged pins. The measurement ran successfully,
but its performance acceptance gate failed. Five interleaved pairs of 32 kernels
per model, zero measured compilation, HH/native160 and unchanged arithmetic:

| Model | Plain median ms (range) | Instrumented median ms (range) | Median overhead | Gate |
| --- | ---: | ---: | ---: | --- |
| sparse | 0.7443 (0.7121–0.7729) | 0.8329 (0.7634–0.8633) | +11.90% | Reject |
| dense | 23.2802 (22.6109–23.5047) | 23.7499 (22.7173–23.9241) | +2.02% | Pass |

Sparse allocation counts/bytes are equal (3424 / 180736 per 32-kernel batch).
Dense streaming allocates 3128480 bytes / 23834 events versus plain 3085568 /
22944, an extra 42912 bytes / 890 allocation events for two periodic writes
per 2048-step batch. This is allocated memory; no independent retained-memory
profile was taken. The recorder has fixed arrays and no workspace field.
The final partial-window flush is outside the kernel timer and separately
reported; periodic writes are inside it. All 24 streamed windows parse; 12 are
periodic (warm plus measured batches).

Every timed plain/instrumented final state and step count matches the reference.
Separate trace comparisons validate count/region hooks with the existing trace
observer; they do not yet exercise the new recorder and trace together. That
full observer-order comparison remains a gate before any long reference. No
medium/both-algorithm chronology calibration or independent final review ran.

The sparse overhead violates the predeclared budget despite unchanged numerical
results. Do not average it away with dense results, relax the threshold, or infer
that a larger model automatically passes. The next experiment should isolate
event bookkeeping and cold-region costs, then reduce unnecessary diagnostic
work while preserving live candidate staging. This is a hypothesis to test,
not an established attribution from separate-process pilot timings.

The user requested continuation until a problem. Execution stops here with this
concrete failed acceptance gate. No long solve was launched, no production code
changed, and no Julia/runner remains active. All seven completed attempts and
the parse-error source snapshot are retained; portable acceptance.json records
the rejection independently of the successful process exit.

## Resumed event-overhead investigation

User authorized continuation after the first failed gate. event-ablation-1 used
one instrumented baseline module, five rotated rounds of 64 sparse kernels and
four modes: no diagnostics, generic counts, noop observer, full recorder. Median
times were 1.3991 / 1.5079 / 1.527499 / 1.520899 ms. No periodic writes or cold
regions executed, measured compilation was zero, and states/operation counts
matched. Generic event bookkeeping contributed most of the measured difference
(+7.78% versus no diagnostics); this does not by itself predict the next pilot.

The diagnostic-only fix specializes record_event! for an owned observer type,
omitting unused generic dictionary/history writes. It keeps callback wrapping,
valid-event checks and separate candidate staging. Public observers retain their
original behavior. event-sink-red-1 had 9 passes / 3 expected metadata failures;
event-sink-green-1 passed all 14 checks with normal compilation and unchanged pins.
The test covers deferred/discarded completion, public history, invalid reason,
composed trace delivery and exception identity. No production source changed.

window-pilot-2 exercises the actual recorder composed with a full trace outside
timing, with native160 in both trace and timed work. Both sparse/dense entry,
completion-state, callback order/count, final-state, step and refactorization
fingerprints match exactly. Five interleaved pairs of 32 kernels have zero
measured compilation. Exit0 and unchanged pins mean the experiment completed;
the sparse acceptance gate still fails:

| Model | Plain median ms (range) | Instrumented median ms (range) | Median overhead | Gate |
| --- | ---: | ---: | ---: | --- |
| sparse | 0.7806 (0.7503–0.7978) | 0.8491 (0.8196–0.8770) | +8.78% | Reject |
| dense | 23.7074 (23.4322–24.0375) | 24.1127 (23.4495–24.2158) | +1.71% | Pass |

Sparse allocation counts/bytes remain equal (3424 / 180736 per batch); dense
again adds 42912 bytes / 890 allocation events for two periodic writes. All
26 streamed windows parse, including the two new verification final windows.
The final flush is outside kernel timing and its tail is reported. No independent
retained-memory profile has been taken. Cross-attempt timing differences are not
a measured causal speedup of the fix; the new within-attempt gate is authoritative.

### Independent review and coverage limitation

Static review found no numerical dependence on suppressed counts/history, no
changed callback ordering, and no unnecessarily added scan/solve/copy or growing
retention. Existing diagnostic dictionaries/history capacity still allocate at
setup; timed recorder storage is fixed and has no workspace field. Trace hashing
of six state arrays occurs only in verification, outside authoritative timing.

Review finding P2: direct record_event! calls in _discard_candidate! and
_record_recovery! are also dropped by the owned sink. These originally record
uncommitted-candidate work without callbacks, or committed recovery after the
observer and last stop check. The operation hooks still count their instrumented
work, but cannot establish all event reasons or committed recovery counts.
Callback-trace equality is therefore not full recovery/event coverage. This
limitation is now explicit in the script/report; a complete long-run report must
add the required fixed counters or narrow its claims, with a new acceptance gate.
No numerical tests were run by the reviewer. The final script edits after the
measured attempt only add this limitation string/comments; the exact measured
source hashes are retained in window-pilot-2-pinned-source.json.

The fix is insufficient for the <=5% budget. Next experiment, if continued:
isolate remaining cost in matched count-only, owned-noop and owned-recorder
modes in the same baseline module; then choose reduced-density or count-only
instrumentation without silently losing required phase/recovery evidence.
Do not infer that medium will pass, repeat an unchanged pilot or relax the limit.
All eleven completed attempts are preserved and no numerical process remains.
No long reference was launched; S0-L2 and subsequent gates remain incomplete.

## Continuous execution and reviewed chronology corrections

The user requested continued execution through failed calibration gates.
owned-ablation-1 measured 1.4330 / 1.490801 / 1.4645 / 1.5157 ms for none /
generic counts / owned noop / recorder (64 sparse kernels, five rounds, compile0).
Splitting the cold observer body alone did not pass (window-pilot-3 sparse12.49%,
dense2.99%). Fixed pricing metadata then passed16 tests and window-pilot-4
sparse4.69%, dense2.62%; allocation equality remained for sparse. Dense added
44288 bytes / 930 allocation events for two periodic writes. These cross-attempt
differences are not a controlled causal speedup claim.

Independent full review found three blocking diagnostic defects: callback-only
phase inference missed auxiliary-to-II return and a direct primal optimization;
dual original cleanup lacked its phase callback; the full calibration serialized
a tuple that TOML rejects. Review also found four redundant metric-column copies.
The latter full solve attempt exited1 after matching OPTIMAL dual traces and
before timed pairs. Its raw outputs are incomplete, not accepted measurements.

Corrections: hook _report_simplex_phase before verbose return, optimizer entries
for actual algorithm, and cleanup_original entry for both branches. A fixed
32-entry cold-region stack and base section preserve nested attribution; cleanup
entry ends only when its optimizer begins. Four redundant copies are removed.
Phase-hook exceptions remain DiagnosticObserverFailure. No numerical body,
tolerance or safeguard is changed. The TOML labels are now a vector.

RED phase tests had1pass/3fail; GREEN19. Actual hooked optimizer/phase entry and
interrupted recovery publication pass16: observer proposal followed by stop does
not increment committed counters; successful publication does. Regression tests
after the fixes pass39 counters,19 windows,14 sink,16 metadata,19 phases. Total123
accepted focused assertions including integration, normal compilation, all exit0
with unchanged pins. Review follow-up found no new blocker, unnecessary numerical
scan/solve/copy or growing retention. New costs are O(1) cold hooks and a bounded
stack; unchanged optimizer boundaries do not read clocks.

The new snapshot requires fresh calibration. The old4.69%/2.62% result is historical,
not acceptance of corrected chronology. Full solve calibration covers both
algorithms and final flush; sparse/dense/medium cases can reuse compilation in one
process. Generic per-reason history remains omitted, but fixed counters preserve
pricing work, committed recovery reasons and discarded metadata totals.
Future launches retain exact source snapshots alongside per-attempt hashes.
