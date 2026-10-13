# S5-K independent numerical and work review

Verdict: PASS for the bounded offline observer/oracle specification. Critical: none.
Important: none. Minor: none. This does not qualify a runtime attempt, a concrete
Julia implementation, successful closure or publication. Separate PASS closure
and fail-fast diagnostic publication remain the author's next gates.

Reviewer s5k_review read the actual source, the existing native adaptive-pricing
handoff fixture and the interruption test, frozen J report/review/evidence/closure,
K report, both K collector sources, K evidence/independent/host-before records,
the current K plan and proposed L offline preparation plan. No Julia, parser,
import, compilation, numerical calculation, old collector/auditor rerun, test run,
source/test/environment/cache change or launch was performed. Only this new review
file was written. A read-only search for guessed stagnation filenames returned no
match; the actual simplex_stalling.jl was then found with rg and read.

## Fresh evidence checks

All 118 evidence SHA-256 entries independently matched using 1 MiB streaming
reads, totaling 771,572,094 bytes, including the frozen historical records,
protected user files and runtime/library files. K evidence SHA-256 is
`45639751d59d80985dd28f97d4bd9ddd84a1d357c6e291ee4e67be3f521d1a4d`.
All five independent.json bindings also matched. The 20 source checks and eight
independent checks are literal true, but were not treated as semantic proof:
their collector code and the relevant source were read independently. No accepted
collector was executed. These are fresh read-time identities, not launch pins.

Local HEAD was 17f5cab5da542c929607e0b179690dde1f79d418 and master was
513c05388a82531e4d8fbcfb383e8897fad14ba2, matching host-before. The current
`git diff master -- src test .github` was empty. Host-before's process and remote
observations remain recorded observations, not a substitute for the author's
fresh closure-time checks. The six protected user files are included in the
successfully rehashed inventory.

Frozen J records retain 237 passing assertions separately in each failed historical
CI run, including the existing 78 interruption/resume and 19 phase-publication
assertions. The 16 source-block comparisons remain frozen evidence. I read those
records and the relevant current test sources; I did not rerun tests or independently
repeat J's full historical Git/log reconstruction. Neither failed run becomes a
current-master or full-suite success through this review.

## Discriminator and exception boundary

The scoped discriminator is source-supported. _candidate_workspace clears pending
factor-update/post-iteration flags (simplex_pivot.jl:118), and its observer is made
with the actual root workspace (line 55). For the handoff's sole root candidate
site (dual_simplex.jl:2113), trial reset buffers pricing_phase_reset before the
refactor. refactor_other is forwarded with the actual trial (simplex_pivot.jl:28),
whose observer.live is the retained LIVE root. Auxiliary notifications use auxiliary
state; auxiliary pivot candidates are rooted at that auxiliary workspace. Sharing
progress/diagnostic dictionaries does not make those workspace identities equal.
The existing native policy disables checked recovery, so that mechanism does not
introduce a second root candidate in this scoped call.

The refactor callback runs before reconstruction (simplex.jl:434 versus the solves
below line 460). Retaining its mutable trial reference is valid; interpreting that
callback's numerical values as a completed snapshot would not be. The proposed
observer only latches identity and counts that notification, then waits.

The target predicate additionally requires the callback state to be LIVE, one
identified trial, and LIVE.factorization identical to trial.factorization but
different from the saved entry factor. Publication invalidates LIVE checkpoints,
copies pivot state, clears LIVE history and adopts the factor before pending replay
(dual_simplex.jl:2148-2153). An earlier LIVE/auxiliary pricing reset cannot satisfy
the full predicate. A missing or duplicate latch or an unreached target must fail
later qualification; source order is not a demonstrated future trajectory.

Pending replay calls ordinary diagnostics directly on LIVE. Recording precedes the
observer invocation (simplex_diagnostics.jl:87), which wraps the thrown sentinel
once in DiagnosticObserverFailure with the same cause. The staged specialized
method does not add a wrapper here. Public make_dual_feasible! rethrows this
nonnumerical failure; its numerical classification only includes SingularException,
ZeroPivotException and _UnreliableBasisSolve. Publication is already complete and
there is no rollback or later pending replay after the selected throw. Therefore
post-unwind factor adoption and selected vector equality are the appropriate oracle.

## Selected state and numerical limits

The nine selected destination arrays are copied in place by _copy_pivot_state!
(simplex_pivot.jl:73); their owners remain LIVE's existing owners. The handoff's
mapped Basis constructor owns its own index/state arrays, distinct from LIVE.
Factor and refactor policy are separately copied before preparation, and publication
adopts the trial policy reference. The retained trial remains mutable until unwind;
LIVE cache invalidation can clear cached stage scratch, which the oracle correctly
excludes from an all-state-preserved claim.

force_pricing_trial! establishes the pricing state before arming. Auxiliary and trial
copy helpers own distinct PricingState objects, and publication copies fields into
the existing LIVE object. _reset_auto_pricing! clears temporary status, last_monitor
and history, and writes last_transition=:phase. Native trial recompute and its
optional flip recompute do not call next_pricing!; even a Devex framework reset
does not overwrite last_transition. The selected equality and phase assertions are
consistent with that source order. The old LIVE stagnation object is neither copied
into auxiliary scratch nor reset in place. Its saved window_count=2 assertion is
appropriate; no numerical weights helper should be called.

Initialization explicitly copies structural objective values, appends zero slack
costs, and concatenates structural/row bounds (simplex.jl:487). The exact fixture
adds pricing/history only and has no journal. This supports the entry relationship
to its model; it is not a general statement about arbitrary altered callers.
The entry-cost/bound copies and post-unwind comparisons are prospective acceptance
conditions, not new execution evidence. In particular, perturb_degenerate=false
alone does not prove all auxiliary costs stay unchanged: numerical repairs in
update_duals! (dual_simplex.jl:579) and backward-step adjustment (line 1423) can still
change costs. The exact fixture's selected equality must be checked if execution is
ever separately admitted; no new arithmetic or trajectory proof was performed here.
Failure of this prospective equality must preserve the observed outcome and stop
qualification, without tuning the fixture or inferring a solver defect. No wording
correction is required for K's expressly prospective contract.
Trial recompute itself reads the copied costs and bounds rather than changing them.
No auxiliary certificate or selected-buffer equality proves original optimality.

Checkpoint clearing and phase-generation advancement follow explicit publication
invalidation. The absent journal slot is not replaced by the copy helper. Auxiliary
work reaches LIVE in finally; trial refactor work is charged before publication,
and scalar iterations/refactorizations are copied during publication. Fixed
throw-time values and equality after unwind can detect later work without asserting
whole-backend counts. The recorded pricing_phase_reset count and total observer
notification count must include the selected callback. The last chronological ring
entry can be read through its existing index; recent_events would allocate a copy.
No complete pending replay, neutral observer, whole-function rollback or zero-work
claim is justified, and K makes none.

## Computational work and retained memory

No unnecessary NEW production work, allocation or retained memory was found.
Production and tests are unchanged, so no before/after kernel benchmark is warranted
and no speedup is claimed. Required numerical safeguards, coefficients, tolerances
and precision are untouched. Existing refactor/copy/reconstruction costs remain
those of J; this review does not reopen HH, DSE or controller audits.

The prospective schema recount is correct: three entry vector copies retain
3(m+n) elements, six in the existing one-row/one-column fixture. Nine publication
comparisons cover eight vectors of length m+n and one of length m, hence
m+8(m+n), or 17 selected element pairs here. Three entry comparisons add 3(m+n)
element pairs. These are logical comparison/copy coverage, not physical memory-load
counts, allocation totals or measured native work. Fixed pricing scalar checks and
identity checks need no added solves, conversions or full model/matrix scan.

The 20 enumerated retained reference slots are 11 named references (LIVE, trial,
entry factor, problem, options, progress, pricing, policy, history, journal,
sentinel) plus nine entry array owners; the three owned copies are additional
payload. Concrete closure/record/container fields must still be counted in L.
Callbacks require constant metadata work per delivered notification and no array
copy, scan or growing event ledger. Setup copies and post-unwind comparisons are
O(m+n), not added per-iteration work. The fixed slot count is not a byte cap:
trial, factor and history roots can keep workspace, sparse metadata, cached scratch
and backend/update-chain graphs alive. Wider precisions and large sparse/dense
problems are not qualified by this tiny Float64-only prospective schema.

The proposed ONE next L gate remains offline preparation of an unexecuted candidate,
with exact source provenance, concrete field/schema accounting and a fresh review.
It authorizes no parser/import/compile/runtime probe, new fixture, success control,
resume, extra solve or scalar/backend matrix. Frozen evidence and the prior broader
S5/S6, CI, HH, x64/full-suite and native-retention limits remain unchanged.
