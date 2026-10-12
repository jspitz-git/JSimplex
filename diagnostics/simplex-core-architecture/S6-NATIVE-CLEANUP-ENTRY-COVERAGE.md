# S6-AO: permanent native owned-bound entry interruption coverage

The new test-only extension appends native_bound_entry_interruption and its two
mode testset to test/primal_perturbation_integration_tests.jl. The ENTIRE old file
remains a byte-identical prefix: original shifted helper, six native successful
cleanup assertions, and all other testsets are preserved. Production, options,
tolerances, arithmetic, safeguards and CI are unchanged.

This closes the scoped permanent entry-interruption coverage gap documented in
AM and qualified by AN. It does not repair or explain the three old CI failures,
prove real deadline expiry, or make the old native-success test pass on x64.

## New source and work

Each of exactly two modes(:stop,:throw) creates the actual shifted Float64/PFI
workspace, runs the initial optimizer, installs default native policy, constructs
one shared budget and invokes public run_from_basis! once. The original helper
assertion and initial OPTIMAL check are retained in both. No successful control,
old testset, neighbor, component/certificate/quality/basis call, factor adapter,
observer, private retry or microcase is added or executed by the target driver.

The callback owns a bounded Ref count and a precreated SingularException(29).
It counts before returningtrue or throwing; caught outside public driver. New
runtime assertions require exactly1 callback per mode. Expiry short-circuiting
to0 fails the test; it is not reclassified as valid callback coverage.

Initial endpoint bits beae32f0ee144531/basis[2]/AT_LOWER,BASIC and initial work
2FTRAN/3BTRAN/2pricing/0refactor are required. Kernel timing enables only after real
helper setup. Driver assertions require all existing kernel counters unchanged,
no extra iteration/refactor, owned journal identity/owner/active bounds/storage
aliases preserved, and owned selected point/prices/rho/costs/basis/states/model/
scaling values unchanged. Mutable identities are paired with owned value copies.
Options/native policy/clock/offsets/budget remain unchanged or synchronized.
Stop requires exact TIME_LIMIT recovery message,no primal/objective/basis and
one checkpoint; throw requires the identical sentinel,no result and no event.
Complete event counter deltas and next_event enforce the declared event boundary.

Per mode there is one small owned predriver snapshot of the tiny1x1 model and
2-coordinate workspace, plus copied kernel/event dictionaries. The snapshot
retains vector copies including original journal values and model arrays; these
are once per cold test, not per solve/candidate/iteration. Post-state compares
live values directly and is not snapshotted again. No permanent diagnostic
ledgers, serialization, rationalization, timing reports or extra lifecycle calls.
This adds two cold test lifecycles, no production scans/allocations/retention.
Existing original-cost/bound scans before the first guard remain: zero counted
kernels is not zero total work. No speedup/neutral-observation claim or benchmark.

The original time30/iter20/tolerances and natural workspace clocks are retained.
No explicit warmup, clockreset, sleeping, removed/extended limit, backend or
precision change. The sentinel is qualified through JSimplex.LinearAlgebra so
this appended test does not depend on unrelated testset imports.

## Evidence

Structural RED: NEW Python source-only analysis records four missing coverage
predicates, zero numerical calls. Python exits normally after confirming intended
absence; this is NOT a failing Julia test or historical reproduction.

GREEN-1 evaluates the actual new source plus only required original monitor/helper
definitions:72/72 assertions (68 permanent incl.helper assertions +4 driver-only
source/global assertions), exit0,20audit gates630pins,6independent checks. Exactly
two new lifecycles; original/native neighbor evidence is reused only by source
identity, not rerun.628 AN pins still match and its sole changed pin is this test.
Actual runtime source/metadata hashes match the saved candidate and unchanged
helper. The audit binds passing runtime assertions to actual source/log; it is
not a new per-case state/option/start-clock census like AN.

26 guard samples: minavailable21238252KiB,maxswap0. Fresh host runner432221
(start24979946),child432226(start24980029),launchgroup432213 absent afterexit,
boot20de7dde-704e-41c8-bee7-b8511c0a86b0. Actualsource/pins/rawportable/user files
independently checked; exit0 alone is not acceptance.

Fresh gpt-6-astra numerical/work/memory review accepted without findings or
unnecessary production work/memory. Test7706c1a integrates as master0eb75c3.
Actual-master gate72/72,exit0,20auditgates630pins,6independent checks,26resource
samples(minavailable21234984KiB,maxswap0). Actualmain source equals GREEN and
allproduction/test/workflow sources equal the integrated master. Four new
lifecycles total across GREEN/master; no additional numerical runs.
Runner433429(start25019798),child433431(start25019880),group433420 separately
verified absent, sameboot. See review and master evidence.

User requested automatic continuation be paused after this step. No following
stage is launched. S4-E source-only plan is prepared for explicit later resumption;
historical cause is deferred without claiming its resolution.
Do not rerun accepted AN/AL/AM/AK/AJ/S5-C/H/I/J/X-AI drivers/auditors/corpus/costs.
S2-A/S6-J/wholeAF rejection and historical failures remain preserved. CI disabled;
fullsuite/x64, real deadline expiry and broader S2/S3/S4/S5/S6 remain open.
