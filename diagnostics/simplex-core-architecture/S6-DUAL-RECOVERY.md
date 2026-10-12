# S6-H: dual recovery reachability census

The original recovery oracle passes locally, but its historical CI failures
require events that are not guaranteed by an exact duplicate column alone.
This census makes no production or test change and does not establish CI repair.

## Existing evidence reconciled

The historical focused851/851 included all216 assertions in this file; broader
semantic/corpus checks remain accepted and were not repeated. Both preserved CI
runs fail48 assertions:44 in bounded recovery and4 after-refresh cancellation.
The failed state tuples retain identical numerical arrays, basis and iteration0;
only refactorizations change1 ->2. Rejection count is0, cancelled cases return
NUMERICAL_ERROR instead of TIME_LIMIT, and expected observer exceptions are absent.
The actual CI numerical row/direction is not recorded, so its cause is unknown.

Current test content is unchanged since commit2f959b9. Current dual_simplex.jl,
simplex_pivot.jl, legacy_dual_correction.jl and the test have no diff from failed
CI ref4914cbb. This excludes a change in these files, not runtime or order effects.

## Source contract

The public ordinary dual iteration validates the BTRAN row before ratio selection,
then the FTRAN direction before comparing the two pivot estimates. Row/direction
residual rejection or ratio uncertainty can terminate or refactor before the
agreement branch ever enters transactional retry. Such a refactor need not emit
refactor_pivot. Mathematical duplicate-column safety is therefore distinct from
reaching pivot_rejected/refactor_pivot callbacks.

Retry stages candidates, converts unsuccessful NUMERICAL_ERROR attempts into
rejections, emits pivot_rejected, and uses refactor_pivot on a scheduled candidate
refresh. Observer failures retain DiagnosticObserverFailure wrapping; cancellation
and numerical failure discard candidate publication. Consumed refactor work is
retained and temporary rejection sets are cleared in finally. No safeguard was
removed or changed in this diagnostic.

## Current-source evidence

census-1 executes20 control/observed pairs (four native managers, five modes).
Both retain the same behavior-driving callback; observed adds passive event names.
Julia isequal checks all recorded fields except that event list. Fresh independent
fixtures perform the row/direction/ratio probes after each pair, so probe scratch
cannot influence the recorded attempts. Original AST nodes for the two failing
oracle groups are evaluated unchanged:108/108. Pair equality20/20,exit0,all17audit
gates, source/test hashes and whole pin inventory independently verified.

All managers select row2/entering5. Native row residual ratio is
0.013481632719732892 (accepted), and the FTRAN direction residual passes. Pivot
estimates disagree in sign: row -0.0001220703125 versus direction
0.00013465030964079536. This explains local entry into retry. Recorded events show
one pivot_rejected for every case, one correction_attempt in the staged attempt,
and refactor_pivot only for after-refresh cancellation.

- Exhausted: NUMERICAL_ERROR, one rejection, no added refactor.
- Cancelled: TIME_LIMIT after rejection, no added refactor.
- Ordinary/numerical observer errors: wrapped ErrorException/SingularException,
  unchanged published numerical state and no added refactor.
- After refresh: TIME_LIMIT before pivot application, one added refactor.

All20 retain numerical state and iteration0, empty rejection sets and zero factor
updates. The after-refresh case's local rejected counter is intentionally unused;
its diagnostic event count, not that counter, records the one rejection.
Source/runtime: Julia1.13.0 AArch64, Julia/BLAS1. Raw evidence remains in
.superpowers/simplex-core-architecture/S6-H/census-1 and portable results/S6-H.
Runner376596/child376597/driver376588 separately absent, no Julia on boot
20de7dde-704e-41c8-bee7-b8511c0a86b0 after completion.

## Work, limits and next action

No production work/allocation/retention changes. Diagnostic snapshots copy selected
vectors O(n+m), retain bounded20case records, and add a passive event append.
Each of20 separate probe fixtures incurs initialization plus BTRAN/pricing and
one FTRAN; residual work scales with basis nonzeros/dimensions. These costs isolate
measurement from the attempts and support path attribution, not timing evidence.
No performance benchmark or speedup claim follows. Equality is recorded fields,
not all workspace bytes; exception records check wrapper/type/message, not object
identity across separately created twins. Actual CI path remains unknown.

Next qualify a test-only direct retry-boundary invocation while preserving the
separate public dual-iteration duplicate-column safety test. Its suitability is
unproven: it must retain budgets, callback wrapping, candidate checks and publication
rules, and document the narrower contract. See the separate S6-I plan. No permanent
test change before qualification and a RED/GREEN subplan. Full S6 remains open;
CI remains manually disabled. Fresh independent review accepts diagnostic closure
without findings; see S6-DUAL-RECOVERY-REVIEW.md. S6-I is qualified for bounded
experimentation only, not permanent test integration.
