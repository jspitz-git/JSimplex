# Long medium phase-II coverage protocol (not yet executed)

## Purpose and prerequisite

Prefixes and replayed original-model cleanup do not explain the long reduced-LP
phase II. Acquire this reference before accepting an S2 whole-medium claim.
No sampling profiler is used: prefix sampling overhead and the preserved cleanup
stall already establish why the old method is unsuitable here.

The allowed input is `/home/jspitz/mps/medium.mps`, SHA-256
`79c374a584b1463305cf4b0faee8920d0364df2dd5d0468a44ab58d9e9d49dc0`.
Use one guarded Julia process, one Julia/BLAS thread, heap hint 2G, 8 GiB virtual
memory, at least 6 GiB available RAM and at most 1 GiB used swap. Start with the
unchanged source baseline and copied local environment. A timeout is incomplete
coverage, even if it emitted many useful windows. Keep test.mps certificate
failure explicitly separate; no claim that these changes fix it.

## Preserve live solver state

Start a fresh solve from the MPS using the historical HH/native160 configuration
for comparison with the long historical run; record every option and numerical
policy field as executed. Use legacy strategy with performance-adaptive functions
disabled, keeping all corresponding numerical safeguards. Cover both algorithms
in separate serialized attempts. Native320 prefixes remain a separate comparison,
not a substitute for native160. Do not restore event snapshots as checkpoints.

Keep the same live workspace, factors, pricing state/pool, weights, perturbation
journal, recovery history, offsets and budget across phase transitions. Observe
phases and counters in place. If a warm steady-state window is used, continue the
same solve; do not rebuild only a basis and call its trajectory equivalent.

## Minimal chronological instrumentation

Before the long run, implement a separate diagnostic script, not production
fields. Use fixed-size scalar counter arrays, with no per-pivot vector copy or
full-state hash. At each phase transition and every 1024 completed steps, append
one bounded JSONL/TOML-compatible window to disk, then flush. Keep only the current
window in memory. Include effective phase/algorithm, dimensions, nonzeros,
iteration plus offset, elapsed/GC/allocated bytes, accepted steps, rejected
candidates, recovery/refactor counts and operation deltas. Split initialization,
ordinary steps, recovery, cleanup entry, cleanup steps and final certification.
Use direct hooks for refactorization and projection; events alone missed these.

Count `_finite_workspace` plus actual per-vector elements visited (distinguish
Dantzig and early returns), recomputations, FTRAN/BTRAN by role, pricing/support
rebuilds, candidate copies and final certificate calls. Use existing diagnostic
counts where their meaning is sufficient. Function call counts must not be
silently converted into full scans. Record nested work once: chronological phase
windows and exclusive function counters answer different questions.

## Calibration acceptance

1. New short attempts must test this *new instrumentation*, not repeat the four
   completed time-budget experiments. Warm compilation separately on small owned
   sparse/dense inputs and a bounded medium prefix. Record compilation explicitly.
2. Interleave at least three plain/counted short pairs with identical inputs,
   options and launch settings. Compare event/state hashes using a separate
   verification mode, outside authoritative timing regions. Preserve callbacks'
   order and arithmetic; a mismatch blocks use of the instrumentation.
3. Measure probe allocations and elapsed spread. Predeclare at most 5% median
   overhead and no material accumulating retention as the diagnostic budget;
   if exceeded, reduce hook density or use count-only runs. Never subtract an
   estimated overhead and present the result as measured production time.
4. Only calibrated count/chronology mode qualifies for the long reference.
   A separate plain solve is authoritative for elapsed performance. If the guard
   stops either one, record the completed windows and incomplete outcome.

## Completion gate

Require a final report, normal process exit, unchanged pins, actual phase-II
coverage and original-model feasibility/certificate for a successful solve.
Record the exact exit reason otherwise. Capture Julia/BLAS versions, launch and
resource logs. Each attempt gets a new directory and separate expected-pins file.
Source, options, scripts and inputs are immutable while the runner is active.

Status: method specified; instrumentation implementation, calibration and long
reference pending. It is deliberate that S1's static ownership inventory does not
wait for several hours of numerical work.
