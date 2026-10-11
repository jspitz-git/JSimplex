# S1-A: local dual entry validation experiment

Status: Integrated and pushed to master as beb161b (architecture commit 8e0a7c7).
Production baseline: fe839aa72171d7496c9c931d9393278448c7317e.
Diagnostic branch before experiment: 94442cf.

## Contract and cost model

The solver-owned deadline contains only immutable clock scalars. Hardware-float
ordinary dual iterations may reuse their successful outer finite-state check
through read-only feasibility summaries and no-op pricing preparation. The reuse
ends within that call. Arbitrary callbacks, non-hardware scalar types, adaptive
pricing, existing pricing state, auto pricing and any feasibility-repair branch
retain independent entry validation. Standalone iteration also retains its check.
No workspace generation, persistent validity bit or cached content hash is added.

Both deadline polls, pricing preparation calls, residual tests and post-step
checks remain. All candidate arithmetic and tolerances are unchanged. Eligibility
adds at most three scalar predicates per outer loop. In an eligible ordinary
step the removed scan reads 3v values with Dantzig and 4v otherwise, v=m+n.
The saving is independent of nnz and update-chain length. The measured work census below confirms the avoided visits on tested paths;
this source-level model does not assert eligibility on every iteration.

## Independent static review

The reviewer traced all paths between the two checks and found no correctness
defect or unnecessary added scans, solves, copies, conversions or retained state.
Repair clears reuse before recomputation/refinement. The deadline retains two
scalars instead of capturing SolveContext. The sparse/dense paired measurements
below found unchanged allocations; independent retained-memory profiling was
not performed. Public callback exception provenance is preserved.

Four validation gaps were reported: later deadline expiry, replacement of a
checked field, successful price repair and adaptive policy without pricing state.
Tests/probes cover these boundaries and passed; independent acceptance review
confirmed the gaps are closed.
Review also distinguished candidate owned/opaque path isolation from a true
baseline/candidate comparison, and helper-call counts from element-visit counts.
Neither incomplete measurement may be presented as a whole-run speedup.

## Attempts

Raw evidence: `.superpowers/simplex-core-architecture/S1-A/` in the active checkout.
Each attempt has immutable pins, command/process identity, resource samples and
stdout. No numerical jobs run concurrently. No excluded model is solved.

- red-1: old production code, diagnostic work-count probe. Exit 1, unchanged
  pins, 25 passes and exactly three intended failures: 9 vs expected 7 checks
  for two pivots in steepest-edge, Devex and Dantzig. State comparisons passed.
- green-1: normal-compilation focused candidate tests. Stopped by 600-second
  wall limit, exit -15, pins unchanged. Termination stack is in Julia type
  inference/backedge storage at precision-recovery-state test line 58. This
  is incomplete evidence. No test-failure output was emitted. Source patch and
  new test/script snapshots are retained in the attempt directory.
- green-2: split normal-compilation focused tests, with explicit per-file output;
  running at this record. Precision recovery will run separately. Allocation
  assertions stay in normal compilation mode.

## Remaining acceptance evidence

Semantic and broader suite results; work census including executed vector lengths;
unchanged event/state hashes; sparse/dense baseline/candidate warm repeated timings
and allocations; runtime dual and medium-prefix trajectory checks; both algorithms
and all five public managers. S0 long phase-II reference remains pending and no
whole-medium claim is made. Preserve the separate existing test.mps certificate
failure instead of treating a bounded prefix as a solution.

## Focused results (partial acceptance)

Normal mode completed 469 assertions across state validity, weights, native
residuals and primal certificate reuse, including their allocation assertions.
The second normal job was deliberately interrupted at about 280 seconds after
reaching dual-entry-phase; its termination stack is in LLVM at that file line 85.
Both incomplete jobs retain unchanged pins and their exact exit reasons.
A separate compile=min semantic job passed precision recovery (30 assertions)
and dual entry/phase (182), exit0 and unchanged pins. This is not a normal-mode
full-suite pass, and semantic timings are not performance evidence.

Work-count job count-1 passed 41 assertions with ordinary compilation and
unchanged pins. For two pivots: 9 to 7 full checks; 144 to 112 actual element visits
for steepest-edge/Devex, 108 to 84 for Dantzig. Element counts sum the vector
length at each executed non-short-circuiting hardware-float loop, rather than
multiplying helper calls. Successful price repair retains its first entry check;
auto, existing pricing state and adaptive policy retain all entry checks.

## Measurement review before corrected paired run

paired-1 was deliberately interrupted and its timings rejected: its baseline
callback returned false instead of using the original solver context clock. The
corrected script now matches each revision's actual internal deadline semantics.
Independent review accepts that correction and the separation of initialization,
preparation, GC, timing and certification, but identified two evidence gaps to fix
before paired-2: compare every plain result to its own trace, and hash all event
names/counts plus refactorization deltas. Count only events inside the measured
kernel, not its preceding preparation. Allocation bytes are not retained memory.

The model coefficients, bounds and objective follow the frozen sparse/dense
recipes. This dual-kernel experiment starts from the solver's ordinary row-variable
basis and performs normal dual-feasibility preparation outside timing. It does
not claim to replay the separate first-64-structural-columns basis recipe for
factorization microbenchmarks. Actual entry state, preparation iterations and
measured nonzero pivot counts must be compared between revisions. All repeated
timings use an infinite deadline; finite-limit semantics have separate tests,
but the cost of reading the clock at finite limits is not measured here.

Broader boundary tests under compile=min passed 780 assertions in boundaries-1:
pivot retry/application/atomicity, factorization failure, handoff atomicity and
shared driver. Exit0, unchanged pins. Together with the focused files this is
1461 semantic/allocation assertions and a separate 41-assertion work probe; it is
not a claim that the complete project suite passed.

## External correctness matrix

External-1 completed all 5 inputs × 2 algorithms × 5 public managers × 2
refactorization backends: 100 OPTIMAL, original-primal certified, matching the
independent reference objective. All 305 assertions passed, exit0, unchanged pins.
See results/S1-A/external.toml and attempts.json. These are correctness checks,
not paired whole-solver timing comparisons. All inputs matched the frozen hashes.
No excluded model was parsed or factored.

## Compilation control

A normal-compilation control on the preserved old project/source also reached
its 300-second wall limit in type inference, at precision-recovery-state line 31.
The candidate combined run reached line 58 before its 600-second limit. Both
retained unchanged pins. These differently composed/timed attempts establish
that bounded normal compilation can fail on the old source too; they do not
establish identical compilation cost or a passing full suite. The candidate's
semantic checks and external correctness matrix are reported separately above.

## Paired sparse/dense kernel results

Corrected paired-2 exited 0 with unchanged pins. Across 10 cases (two models,
five managers), all baseline/candidate entry states, completion-state hashes,
all-event name hashes/counts, step counts and refactorization deltas matched.
Every plain result also matched its corresponding trace entry/final state and
step/refactor counts. Three interleaved warm plain pairs per case reported zero
measured compilation and equal allocation bytes/counts. Trace setup is excluded
from kernel event accounting; observer timing is not used to claim a speedup.

| Model / manager | Steps | Baseline median µs (range) | Candidate median µs (range) | C/B median | Bytes / allocations per side |
| --- | ---: | ---: | ---: | ---: | ---: |
| sparse / pfi | 9 | 71.0 (69.2–74.5) | 75.9 (71.3–79.1) | 1.069 | 3584 / 49 |
| sparse / huangfu_hall | 9 | 59.6 (57.5–64.0) | 60.1 (58.9–62.3) | 1.008 | 4992 / 86 |
| sparse / forrest_tomlin | 9 | 87.9 (87.7–94.0) | 84.0 (83.8–107.1) | 0.956 | 4432 / 60 |
| sparse / suhl_suhl | 9 | 91.8 (88.0–91.9) | 90.7 (86.1–91.0) | 0.988 | 4512 / 60 |
| sparse / bartels_golub | 9 | 94.7 (93.9–114.4) | 96.2 (93.4–96.4) | 1.016 | 7760 / 115 |
| dense / pfi | 64 | 875.9 (849.8–1063.1) | 854.6 (832.1–870.2) | 0.976 | 81096 / 329 |
| dense / huangfu_hall | 64 | 800.6 (769.5–907.5) | 793.4 (771.5–811.6) | 0.991 | 92248 / 586 |
| dense / forrest_tomlin | 64 | 1679.8 (1604.2–1753.9) | 1588.6 (1577.6–1594.4) | 0.946 | 328536 / 820 |
| dense / suhl_suhl | 64 | 1641.1 (1634.7–1684.2) | 1660.6 (1617.3–1690.6) | 1.012 | 334840 / 905 |
| dense / bartels_golub | 64 | 3164.9 (3055.5–3221.2) | 3127.0 (3044.0–3187.7) | 0.988 | 525088 / 775 |

The small sparse runs contain only 9 steps and last tens of microseconds; the
dense runs contain 64 steps. Three pairs and overlapping timing ranges are not
evidence of a universal elapsed speedup. Sparse PFI is 6.9% slower by these
medians (4.9 µs); dense FT is 5.4% faster. Neither selective best-case reporting
nor aggregation across unlike kernels is justified. The established improvement
is fewer executed finite-check elements; broad wall-time effects remain uncertain.
No added retained workspace fields or cache exist. This table measures allocated
memory, not an independent retained-memory profile.

## Medium auxiliary-prefix validation

Candidate medium-dual-1 completed its 4000-step HH/native320 plain/census pair
with identical event and full-state hashes/counts, zero measured compilation,
exit0 and unchanged pins. The candidate also exactly matches the historical
baseline event/state hashes, event counts, status, iterations and input SHA-256.
It executes 12004 finite-workspace checks (historical baseline: 16004) and
26287751664 measured vector-element visits. The fresh baseline element census is recorded below; helper-call counts are
not silently treated as element counts.
Both modes end at ITERATION_LIMIT; no solved-medium or long-phase-II claim follows.

The new baseline medium-dual census completed normally within its 600-second
guard, despite slow instrumentation warm-up. Both sources are identified by
source_root and immutable pins. Baseline and candidate plain/census states,
events, iterations and input hashes all match. Actual element visits fall from
35047415664 to 26287751664: 8759664000 avoided visits (24.994% overall, including
unchanged entry/final checks). Finite-workspace calls fall from 16004 to 12004.

One fresh plain run per side took baseline 67.247 s and candidate 59.153 s;
census took 59.991 s and 57.070 s. These single sequential measurements include
setup and GC and are not statistically established elapsed gains. All four
measured regions report zero compilation. Counter warm-ups/compilation and
calibration probes are separately retained in results/S1-A/medium-dual-*/.
The work reduction and unchanged arithmetic trajectory are the accepted findings.

## Prefix timing and final review limitations

The prefix mode named `plain` retains the common trajectory observer (including
periodic state hashes); it omits the census hooks. It is not an uninstrumented
whole-solver timing. Both prefix modes include initialization and GC, unlike the
separately timed sparse/dense kernel. Runtime baseline plain/census took 2.102/5.063 s
with 0.613/3.625 s GC. This large overhead makes that census unsuitable as a
calibrated timing source; operation counts and matching trajectories remain useful.
S0 long-run low-overhead instrumentation still requires its own <=5% calibration.

Final independent review confirmed closure of the earlier test/measurement gaps
and found no additional blocking production defect or unnecessary work/retention.
It independently checked the paired and medium reports. Integration is conditional
on the remaining runtime pair and fresh source/hash/ref checks. Bounded normal
compilation remains incomplete on both revisions; no full-suite pass is claimed.

## Runtime auxiliary/main-dual prefix and acceptance

Both runtime attempts exited 0 with unchanged pins. All baseline/candidate ×
plain/census input, phase, event and state hashes/counts, status and 512 iterations
match; all measured regions report zero compilation. Finite-workspace calls
fall from 2055 to 1796. Actual element visits fall from 493758960 to 431528512,
saving 62230448 (12.60%). All other recorded operation call counts are identical.
Only 259 entry checks were eligible; no claim is made that every dual step uses
the local fast path. The prefix crosses auxiliary/main-dual entry and ends at
ITERATION_LIMIT, not an optimal solution.

Candidate trajectory-observed plain/census took 2.401/4.331 s, including
0.979/2.924 s GC. Plain baseline/candidate allocated 1807236152/1806428968 bytes
in 35585375/35585371 events. These setup-dominated single measurements are not
evidence of per-step allocation savings or elapsed speedup. Kernel allocation
equality is the stronger controlled observation for ordinary steps.

Author checked all 507 source/test files against eight candidate validation pin
sets after the final run; no mismatch. The runner and child process are absent,
and no Julia process remains. Portable attempts.json includes all 14 attempts,
including rejected/interrupted runs; validated-source.json identifies the five
production files and records the pin comparisons.

Acceptance: the local ownership/safety contract, 1807 accepted Test assertions
(1461 focused semantics/allocation, 41 work probe, 305 external), 30 interleaved
kernel timing pairs, and both real-input trajectory/work comparisons satisfy
the S1-A gate. No unnecessary added work or retained workspace state was found
by independent review. No universal elapsed gain, full normal-mode suite,
resolved test.mps failure, or whole-medium result is claimed.

Ruling: integrate this reviewed chunk using the plan's focused semantic/allocation
and broader numerical gates, with hashes proving the tested tree unchanged.
Do not repeat the known old-source normal-compilation timeout or completed
benchmarks solely for integration. Cost: the complete normal-mode project suite
remains an explicit coverage gap. Preserve all raw attempts and environments.

## Integration

Production commit `8e0a7c7def505604ccfe50cdbc2cf9cee453092d` was cherry-picked
to master as `beb161b310afd9dc7126eca98e3c15898a69efbf` and pushed. The only
post-validation edit was removal of one trailing blank line in a test helper;
validated-source.json records this exception and final hashes. Source/test/Project
trees are identical on architecture and master. integration-1 ran the 242 new
contract assertions directly from master under compile=min: all passed, exit0,
unchanged pins. This short run verifies integration rather than repeating cost
measurements. Main user settings/environment hashes are unchanged.

All 15 attempts (including rejected/interrupted runs) remain in the local raw
directory. The chronological process records are history; no Julia is active
at this integrated checkpoint. Long-run S0 and later architecture stages remain.
