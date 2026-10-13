# S5-K: pending auxiliary observer oracle, offline specification

Source/evidence only at diagnostic17f5cab and master513c053. No Julia, numerical
arithmetic, import, compilation, fixture, driver, launcher or test change. Existing
J evidence is reused:237 assertions separately in each failed historical CI run,
including78 private interruption/resume and19 phase-publication assertions. J binds
all16 test blocks and their whole files. Those runs remain failed; no current run
or full-suite success is inferred. J's97 hashes and12-check closure were freshly
verified. The present specification does not rerun that evidence.

## A source-supported discriminator

The reference is the existing handoff test in adaptive_pricing_lifecycle_tests.jl,
with its existing Float64 model, options, isolated_pricing_policy, forced temporary
pricing and stagnation history. Native numerical defaults and phase_one=false stay
unchanged. Initialization uses the model's objective and bounds; the fixture makes
no detached/unowned cost or bound alteration and installs no perturbation journal.
Thus its entry working bounds correspond to its model under the existing structural
column/slack convention. This does not generalize to arbitrary altered callers.
"Original-bound" below always means LIVE bounds after entry restoration. No
auxiliary or working-model certificate is transferred to the original problem.

An observer can use identity, without extra numerical calls or new dispatch:

1. Arm only after the existing fixture setup. Retain the LIVE workspace reference.
   On refactor_other, accept a candidate only if its diagnostics observer is an
   existing _StageObserver whose live field is identical to this LIVE workspace.
   Retain that candidate reference in one fixed slot; count matching notifications.
   Require exactly one match. Auxiliary notifications have auxiliary state or an
   observer rooted at the auxiliary workspace, so do not satisfy this identity.
2. The identified trial has its own copied factor and deep-copied refactor policy.
   Its phase reset was buffered before refactor_other. The refactor event itself
   precedes its FTRAN/BTRAN reconstruction. Do not throw there or snapshot its
   incomplete values. The observer only retains a reference, a counter and fixed
   scalar metadata. Recompute continues to mutate that referenced trial normally.
3. Throw one preconstructed sentinel only when reason is pricing_phase_reset,
   notification state is LIVE, exactly one trial was identified, and LIVE.factorization
   is identical to that trial.factorization. Require it differs from the saved entry
   factor. Capture fixed scalar identity/work flags immediately before throwing.
   A matching event name on auxiliary or trial is insufficient. A LIVE event before
   the identified trial/publication cannot satisfy the full discriminator.

Source order supplies the argument: the root handoff candidate is made with
_StageObserver(LIVE,...); its factor is privately copied; reset precedes refactor;
recompute's nonbuffered refactor_other forwards the actual candidate; after checks,
LIVE checkpoint invalidation and pivot-state copying precede the factor assignment;
only then does the loop deliver pending events with LIVE as state. There is no
other root candidate creation in this handoff function; auxiliary iterations stage
under their own auxiliary root. The scoped native policy does not enter checked
recovery. This is conditional source reachability, NOT execution qualification or
proof that a future attempt will reach the event. A missing/duplicate latch, an
unreached target or an unexpected result would fail that future qualification.

_reset_auto_pricing! can return when pricing state is absent. Here the existing
force_pricing_trial! creates it, auxiliary/trial helpers copy it, and diagnostics
are supplied. StageObserver buffers pricing_phase_reset explicitly. Nonbuffered
notifications still run earlier and are not suppressed. No production hooks,
method overwrite, module clone, clock reset or additional solve is required.

## Selected oracle (prospective, not executed)

One eventual throw case only could use the following contract. This stage does not
authorize its construction or execution. No success control, resumed solve or
manager/scalar expansion is proposed.

| Selection | Required observation if the target is reached |
| --- | --- |
| Outcome | Catch DiagnosticObserverFailure directly, with cause identical to the preconstructed sentinel; no returned terminal result. The public wrapper rethrows this nonnumerical exception. Require one selected throw and one trial latch. |
| Publication identity | At the throw LIVE has the trial factor, different from the entry factor. After unwind this identity persists. LIVE's problem/options/progress and nine selected destination array owners remain their entry identities; the trial's nine corresponding arrays are distinct owners. LIVE adopts trial refactor-policy identity, separate from the saved entry policy. |
| Published values | After unwind compare nine selected vectors between LIVE and the retained trial: costs, lower, upper, primal, reduced_costs, pricing_weights, devex_reference, basis.basic_indices and basis.states. These are publication checks, not an exact analytical solution or hidden trajectory claim. No post-return numerical solve/certificate is added. |
| Model and bounds | Three entry copies of costs/lower/upper bind this unaltered fixture. After unwind require these selected working values retained and model identity unchanged; explicitly bind the fixture's initialization relationship to the model in any later preparation. No claim of general whole-model immutability or original certification. |
| Pricing/history | Distinct LIVE/trial PricingState owners with equal copied scalar fields; temporary=false, last_transition=:phase, and no LIVE stagnation. Saved preentry stagnation monitor is not mutated by reset; its existing window_count=2 assertion is reused. Do not run check_basis_weights: it performs extra basis solves. |
| Checkpoint/journal | LIVE checkpoint list empty and phase_generation advanced from entry; journal slot remains the fixture's absent journal. Invalidation can recurse into stage scratch; no assertion that every trial cache survives. No seeded checkpoint/cache or journal is added. |
| Consumed work | Save entry and throw-time scalar iterations/refactorizations, then require monotone advancement and equality of post-return values to throw-time values. Relate final LIVE counters to retained trial as copied by publication. Shared diagnostics persist; no exact whole-backend counts or zero-work claim. |
| Event prefix | At selected throw the ordinary diagnostics already recorded pricing_phase_reset. Save its scalar event count and total observer notification count; require they do not advance after unwind and require the existing bounded event ring's last chronological event is this reason. Later pending entries need not be delivered; do not assert entire pending replay or invent a complete prepublication event list. |

Pretrial restoration, initial recompute and flips may mutate LIVE. Auxiliary work
survives through finally, and private refactor work is charged before publication.
Staging also changes cached stage storage and shared diagnostics. Consequently this
is neither whole-function rollback nor callback invisibility/observer neutrality.
The trial reference is live mutable storage until unwinding: it is deliberately
NOT an immutable snapshot at the refactor callback. Only post-unwind equality and
fixed throw-time scalar checks are claimed. Internal copy/allocation failures are
outside this selected observer exception boundary.

## Work and retention bound

No production change: no new production work, allocations or retained memory.
No benchmark is warranted for this offline document. The prospective oracle adds
three owned vector copies (costs/lower/upper):3(m+n) entries, six entries in the
existing one-row/one-column fixture. Nine preentry array references allow owner
checks. Nine post-unwind vector comparisons visit m+8(m+n) entries (17 here), plus
3(m+n) entry comparisons and fixed pricing/identity/work checks. These are source
schema counts, not measured allocations or native work. A final event-ring check
can inspect the existing ring index without copying its at-most64-symbol buffer.

Budget at most20 retained reference slots: LIVE, trial, entry factor, problem,
options, progress, pricing state, refactor policy, stagnation, journal, sentinel,
and nine selected array owners. Three copied vectors are additional owned payload.
Fixed counters/flags/tuples have no per-event growth; no callback array copy or
vector scan. One callback identity/type check per delivered notification, and constant
metadata work at the two selected boundaries. Retaining trial/entry factor/history
roots can retain their reachable workspace/backend graphs, including cached stage
storage and factor update history. Slot count is NOT a byte or native-retention
bound; no GC/free proof or negligible overhead claim. Copies/scans scale with m+n;
this specification admits only the existing tiny fixture, not a broad benchmark.
Existing production factor copies, refactor-policy deep copies, reconstructions,
weight work and invalidations remain as scoped in J/S4-X; they are not recounted as
complete observed backend caps. No unnecessary new production work/memory is found.

## Decision and next boundary

The identity route is supported by source. Runtime reachability, a concrete fixed
schema and its syntax remain unqualified. ONE next offline implementation gate may
prepare a separate candidate specification/driver for review without executing it,
using this exact existing fixture and one throw case. It must first resolve concrete
field/schema accounting and preserve all defaults; it cannot authorize a launch.
No broadened numerical experiment or new fixture is justified here. Broader S5/S6,
full-suite/x64, HH reuse, native retention and all prior rejections remain unchanged.
