# S6-V: controlled price-recovery boundary qualification

Diagnostic-only, accepted by fresh independent gpt-6-astra review without findings. Production and permanent tests
are unchanged. Twelve new Float64 iterations (three cases × four managers), four
additional negative component invocations,124/124 assertions,exit0,21 offline audit
gates,616 independently checked launch pins. No old census/corpus/full-file rerun.

## Fixture, contracts and scope

The new basis is I6, followed by e3..e6,-e3..-e6 and a zero structural column.
Basic costs are [1,1,0,0,0,0]; all other structural costs zero. Equality row bounds
are ones(6), nonbasic structural lower bounds zero, last column upper one. Basic
primal is ones(6), other structural values zero, row variables one. Matrix, costs,
point and exact residuals are audited rationally. This is a changed fixture, not
an equivalent model or a repair of the original native roundoff path.

Original manager/default options/policy match saved S6-U for all four managers.
The original `_primal_iteration!(ws,()->false,0.0)` call and post-publication
reduced_costs[7]=-1 injection remain. All five original assertion lines are
extracted without rewriting and run for each subject (20 original assertions).
No callbacks call a solve/refactor/certificate or new mutator; the existing
injection remains their sole workspace write. Owned snapshots are nonworkspace-safe.

Setup initializes/recomputes using real factors. Seed cases then use production
reduced-cost reconstruction from declared rho=[1,1,2^-40,0,0,0] before wrapping.
The subject factor forwards the real fresh cost-RHS BTRAN before replacing its
first output with declared rho. Every call is counted even after replacement is
consumed. All actual residual-correction BTRANs and FTRANs forward unchanged.
Fresh basis cost RHS [1,1,0,0,0,0] differs from correction RHS [0,0,-2^-40,0,0,0].
Raw identity solves equal their RHS exactly; corrected rho=[1,1,0,0,0,0]. Declared
cB-B' rho residual is [0,0,-2^-40,0,0,0], and corrected residual is exactly zero.
No quality result, recovery decision, event, publication or second disagreement
is fabricated. Snapshot/call arrays own data; the adapter owns the original factor,
and the abandoned workspace shell is not independently used.

Forwarding definitions also cover invalidation, finite checks, copy, replacement
and refactor, following the existing test adapter interface. Copy/update/refactor
branches are not exercised by these zero-pivot iterations and are not qualified
as a general factor wrapper. Hypersparse is explicitly excluded; Float64 only.

## Observed outcomes (identical for all four managers)

| Case | Result | Fresh cost BTRAN | Correction BTRAN | FTRAN | Publications/corrections |
| --- | --- | ---: | ---: | ---: | ---: |
| Exact prices, forwarded real factor | OPTIMAL |0|0|0|0/0|
| Seeded prices, forwarded real factor | NUMERICAL_ERROR |1|0|1|0/0|
| Seeded prices + declared first fresh output | NUMERICAL_ERROR |1|1|2|1/1|

The subject publishes corrected prices, then the original callback corrupts price7.
A second direction/price disagreement is rejected; zero iterations, unchanged
selected primal/cost/basis/states/refactorizations/update count, exclusions empty.
Counts exclude initialization. No phase transfer, public Solution certificate,
cancellation or exception behavior is newly established.

After freezing each subject result, the negative component check directly invokes
`_try_native_primal_price_recovery!` once on the exhausted workspace. The real fresh
BTRAN is exact and returns false before a correction event. It adds no event and
leaves the recorded selected state unchanged. All five old oracle booleans remain
true, but the new budget oracle is FALSE:2 fresh cost BTRAN+1 correction=3total,
while the replacement hit count is still1. Each expected false result is preserved
explicitly in portable audit/report; the overall diagnostic acceptance gate checks
that this false result was detected. It is not mislabeled as a passing budget.

This demonstrates sensitivity to an extra boundary call. It does not run a mutated
production loop or prove a historical CI control-flow bug. The current production
loop itself performs exactly the one allowed fresh recovery in the subject.

## Evidence and work/memory

Raw `.superpowers/simplex-core-architecture/S6-V/qualification-1`;
portable `results/S6-V/qualification-1-*`. Runtime Julia1.13.0 aarch64,Julia/BLAS1,
existing memory guard. Original test/source hash, exact five assertions, all options/
policies, pins/membership, process exit, rational matrix/point/price/residuals,
forwarded raw outputs and negative sensitivity audited. No unobserved control was
rerun; all three cases are new changed-fixture controls/subjects.

No production work/allocation/retention changes. Diagnostic call-ledger copies
are O(calls*6) and snapshots O(events*(6+21)), plus12 small6x15matrix snapshots;
negative checks reuse four subjects only after immutable copies of their results.
They add four actual BTRANs outside the twelve iterations, explicitly accounted.
They are necessary to expose the event-count blind spot. No performance comparison,
speedup, overhead estimate or benchmark follows from these instrumented tiny runs.
A permanent test adapter should keep only bounded counters/declared vectors, not
retain this diagnostic call ledger or recorder; no new production dependency.

Next: separate S6-W minimal test-only RED/GREEN plan. Keep native
roundoff helper and adjacent native integration tests unchanged. Full-suite/x64,
original CI cause, observer neutrality and general wrapper lifecycle remain open.
