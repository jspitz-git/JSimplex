# S5-J independent numerical and work review

Verdict: PASS for this bounded source/evidence reconciliation after one offline
wording clarification. No unresolved Critical, Important or Minor findings.
Separate successful closure and fail-fast diagnostic publication remain required;
this review does not claim that either has occurred.

Fresh reviewer s5j_review independently inspected the actual source/tests, six
excerpts, collector source, evidence, host-before record, author-independent result,
S5-J report, updated STATUS/roadmap and S5-K offline-only continuation. No Julia,
import/compilation probe, numerical calculation, fixture, old collector/auditor
rerun, or production/test/environment edit was performed. Only this new review
file was written by the reviewer. Local refs were diagnostic5a2c523 and master513c053;
`git diff master -- src test .github` was empty.

## Evidence and coverage

All97 recorded SHA-256 identities independently matched on fresh reads, covering
771,250,119 bytes, including48 runtime/library files. These are read-time identities,
not launch pins or new runtime observations. Evidence SHA-256 is
`eeafc6d1501cc6840dd49dbefd1f61fe2e377b764f8588c9802954375041d290`.
The21 recorded checks were read with their source context rather than accepted
as a substitute for semantic review.

Both failed CI logs were independently checked against metadata, original raw
lines and ANSI-only normalization: eight rows/237 passing assertions separately
for38142752357 (headb720674) and38149970679 (head4914cbb). All16 named test blocks
and their whole files match historical Git bytes. All18 source comparisons match
the recorded hashes:16 equal, and only simplex_perturbation.jl differs twice.
The actual diff is the already reviewed S5-C restoration-copy guard, not a new
handoff change. All six excerpt byte ranges and starting lines match actual files.
Both CI conclusions remain failure; this is no current-master/full-suite success.

The78-assertion handoff test uses logger/refactor-entry-driven interruption and
resumed success, without a diagnostic observer. The19-assertion adaptive-pricing
test throws on refactor_other, which recompute! emits before reconstruction and
publication (simplex.jl:434 versus448). Its deadline is a callback predicate, not
a measured clock expiry. Existing generic observer/callback and cancelled-candidate
pricing-event tests do not assert the selected post-publication exception/state
composition. Their accepted coverage is reused, not described as absent execution.

## Numerical ownership and remaining scope

Source dual_simplex.jl:2052 onward restores live perturbations before auxiliary
construction, consumes auxiliary work in finally, maps states against live bounds,
and prepares the private original-bound trial. Candidate state initially shares
factor/policy references; the handoff explicitly installs a factor copy and policy
deep copy before trial preparation. Required refactor/recompute, bound flips,
finiteness, dual feasibility and final stop checks remain. Private rejection is
not whole-function rollback: earlier live restoration, shared diagnostics, consumed
work and cached stage storage can change.

Publication invalidates live checkpoints/cache, copies state, clears stagnation
and installs the trial factor before replaying queued events. StageObserver buffers
pricing_phase_reset but forwards other events with candidate state; diagnostics
record an ordinary event before wrapping an observer exception. Thus a throwing
pending observer sees already published live state and can prevent later pending
events from being delivered. Original-model certification and recession ambiguity
safeguards remain separate; auxiliary certificates are not transferred.

One wording finding was fixed once offline: reviewer severity Minor, conservatively
tracked by the author as Important to avoid an overbroad original-model contract.
“Original-bound” now explicitly means live working bounds after entry restoration,
relative to the auxiliary box. phase_one=false need not normalize arbitrary unowned
cost/bound changes to authoritative problem data. Both report and S5-K plan state
this limit and preserve separate certification. I independently checked the exact
additions, both before-copy hashes and both amended hashes in review-fix.json;
RED2/GREEN5 is textual evidence, not a numerical test. Original independent.json
and evidence.json were preserved, with prior report/plan bindings recoverable from
the before-review copies.

The ONE remaining unqualified composition is an observer throwing during pending
pricing_phase_reset replay after successful publication. It is not a demonstrated
defect or a claim that the path has never executed. S5-K appropriately requires an
existing live/auxiliary/trial discriminator, pricing state and diagnostics, selected
ownership/cause/work/event-prefix oracles, and bounded capture. It authorizes only
offline source/oracle work, no runtime plan or instrumentation. If source identity
cannot establish reachability without hooks or extra numerical work, that route
must close rather than expand.

## Computational work and memory

No unnecessary NEW production computation, allocation or retained memory was found:
production is unchanged. No performance benchmark or speedup claim is warranted.
The report correctly treats existing work as auxiliary setup/private handoff costs
and does not imply that documentation adds work to ordinary iterations.

I counted18 direct copyto! sites in _copy_pivot_state!:17 fixed-shape destinations
plus the resized rejection list. The helper runs at candidate initialization and
successful publication; its helper copies/cache operations are additional. These
are source sites, not measured execution/allocation counts. The two conditional
factor-copy sites and two policy deep copies are not two new LU calls. Backend
base/history sharing remains backend-specific; prior HH qualification is reused.

Existing array/basis/staging copies and scans scale with m and m+n, sparse metadata
with nonzeros, mutable support with support size, and factor/history retention with
update history and scalar storage. First-use candidate scratch is cached; live
invalidation recursively clears stage sparse/hypersparse caches. Pricing reset can
rebuild invalid weights; recomputes, conditional flip recomputes and policy solve
refinement retain their existing costs. No tolerance, coefficient, arithmetic
precision or numerical safeguard changed. Complete observed native work, full
retention release, broader precision/backend coverage and controller caps remain
unqualified; no new optimization is justified by this inspection alone.

The six protected user hashes matched. All55 unchanged I closure entries matched;
its two evolving continuation entries match the saved before-J files exactly.
Updated STATUS and roadmap preserve these boundaries. CI remains off, HH reuse
remains disabled, and prior historical/x64/full-suite, Q GC/outlier, bootstrap,
cache/init, native-retention and rejected-route limits remain unchanged.
