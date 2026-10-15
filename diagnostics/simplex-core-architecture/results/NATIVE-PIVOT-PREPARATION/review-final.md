# Independent final Task1 offline review

Decision: ACCEPTED for Task1 OFFLINE candidate/test preparation. Initial finding
R1 is resolved; no remaining actionable findings were identified in this bounded
correction review. This accepts source and test preparation only. Julia syntax,
dispatch, inference, ownership behavior and numerical results remain UNEXECUTED,
as does overlay.py. No launch, integration, promotion or oldcost2 resumption is
admitted here.

## Correction reviewed

The populated-spare copy fixture now performs a refactor before copying a
nonempty update history, observes the private spare, asserts it remains with the
original, and requires the copied slot to have no spare. It checks shared active
factor ownership, control identity/value and preserved history while the original
and saved manager are refactorized independently. This makes the former empty
spare assertion non-vacuous for all four managers and both policy values.

Both separate fresh/no-spare and private-spare failure states now hold a saved
copy. After singular failure they require unchanged active owners, controls,
history and policy, a discarded failed spare, and valid F/B residual checks on
both live and saved factors. After a valid recovery refactor they again check
the saved owner/control/history/policy and saved F/B results. Copying sets the
existing shared flag while retaining the original's private spare; source
inspection confirms the with-spare branch still reaches private lu!. No existing
production failure or publication rule was changed.

The source-derived additions are 4 managers × 2 policies = 8 refactor entries;
4 × 2 × 2 failure states = 16 manager copies; and 4 × 2 × 2 failure states ×
2 saved-solve checkpoints × 2 directions = 64 solve entries (32 F, 32 B).
These agree with the ledger. They are component-call deltas, not observations,
full driver totals, or complete native-internal work counts. Task2 must budget
them and all existing assertions/setup/history/control snapshots before launch.

## Evidence and cost assessment

The new reviewer-check-final.py ran once and wrote reviewer-check-final.json:
13/13 checks PASS. All130 required inputs are hash-bound. Ten saved binding maps
reconcile against current files or exactly the five explicitly preserved original
files; the initial rejected review and both prior checker failures remain intact.
The current correction's 10 checks/14 bindings match. All seven production
candidate files and their 28-edit inverse remain unchanged; the overlay change
is solely the amended test hash. Other test groups and source outside the
copy/failure section are unchanged. The earlier complete source review and
non-vacuous hot-range identity proof therefore remain applicable.

No unnecessary NEW production computational work or memory cost was found.
This correction changes only tests and evidence text/bindings. The underlying
candidate still adds constant Symbol/enum metadata and fresh-construction policy
selection, two control stores and one LU; it adds no per-iteration/candidate/F/B/
update scan, solve, copy, control rewrite, retained factor owner or growing cache.
Existing O(n+nnz) private-spare pattern work and update-chain algorithms remain.
Test-only copies and snapshots retain tiny extra owners/history until each test
scope ends and must be excluded from kernel timing but included in driver costs.
Production allocation/alignment/native-fill effects are unmeasured; pivot choices
may materially change fill and numerical trajectories. No speedup or universal
zero-overhead claim is made. Non-Float64 arithmetic and all four excluded raw
auxiliary LU safeguards remain unchanged.

The final review binds the130 inputs, required list, its new checker source/result
and this report. Separate exact-stage admission is still required for every
RED/GREEN/cost/public runtime stage. Public recovery qualification remains Task3.
