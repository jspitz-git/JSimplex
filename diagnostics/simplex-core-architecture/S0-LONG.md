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
