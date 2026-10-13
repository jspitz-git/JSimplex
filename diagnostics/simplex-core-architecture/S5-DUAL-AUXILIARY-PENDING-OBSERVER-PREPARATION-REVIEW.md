# S5-L independent numerical and work review

Verdict: PASS for the bounded offline preparation of one unexecuted candidate.
Critical: none. Important: none. Minor: none. No unnecessary NEW production work,
allocation or retained memory was found. This review does not establish Julia
syntax validity, runtime reachability, qualification, successful closure or publication.
A separate PASS closure and fail-fast publication remain required.

Fresh reviewer s5l_review read STATUS, the current L preparation plan, frozen K
oracle/review and J ownership review, the actual relevant source and original
adaptive-pricing handoff fixture, L candidate/provenance/fixture text, preparation
and checking scripts, evidence/independent/host-before records, L report and the
proposed M admission plan. The newly prepared closure.py was read as text only;
it is outside the 141-entry preparation inventory and remains unexecuted by this
reviewer. No Julia, parser, import, compilation, native operation, LP arithmetic,
numerical attempt, old collector/auditor rerun, test, source/environment/cache
change or launcher was performed. Only this new review file was written. A source
search initially named nonexistent numerical_policy.jl/basis.jl; the actual
simplex_numerics.jl/simplex.jl definitions were then located and read.

## Independent evidence and provenance

All 141 recorded SHA-256 identities matched independent 1 MiB streaming reads,
covering 771,852,990 bytes. All eight independent.json artifact bindings also
matched. Evidence SHA-256 is
`338e5ddc41063f0df2271036cac591c522c0db18d27ce94bd5731c14e928c3e3`.
Candidate SHA-256 is
`b553d449a0db620bfae1970861806a778bbf45d36465026e8b4a540e4b4f4288`.
The recorded 20 source checks and nine author-independent checks are literal true;
their source was read, not executed or substituted for this semantic review.
These are fresh read-time identities, not numerical observations or launch pins.

Current HEAD was 36f67d5324d1011bdb277eff90b74ba02d4f05c7 and master was
513c05388a82531e4d8fbcfb383e8897fad14ba2. The current diff against master for src,
test and .github was empty. Protected user/runtime identities are covered by the
full successful rehash. Recorded host/process checks do not replace the author's
fresh closure-time process/group and publication checks.

Independent text checks reconstructed all three helper blocks from their recorded
source starting lines and verified their exact bytes/hashes and unique candidate
occurrence. Both setup blocks match current source and preserved fixture text;
adding back exactly four leading spaces reproduces each original block. The whole
fixture-source.txt matches the current testset with the documented trailing-newline
normalization. Candidate length is 181 lines with 40 unique predicates and 15 unique
observations. No old testset or check_basis_weights call is imported or executed.
The native NumericalPolicy defaults in simplex_numerics.jl:43 and the exact helper
preserve the intended Float64 scope: adaptive pricing/stalling enabled, phase_one,
checked recovery and solve_refinement disabled. No options, coefficients,
tolerances or precision were retuned.

Frozen J/K's historical 237 passing assertions separately in each failed CI run,
and existing 78 interruption/resume and 19 phase-publication assertions, remain
reused historical evidence. I read their scoped review and the current selected
fixture; I did not rerun those tests or reconstruct all historical logs/Git blocks.
No historical failure becomes current-master or full-suite success here.

## Candidate semantics and false reachability

By reading the concrete candidate, its 13-field probe constructor matches four
reference roles and nine Bool/Int fields. The named workspace, scratch, policy,
pricing, diagnostic and exception fields exist in the current source. The try/
catch/finally structure disarms after the public call unwinds, captures the actual
exception object, and uses direct DiagnosticObserverFailure and sentinel cause
identity. The concrete code has no obvious textual mismatch, but it has deliberately
not been parsed, imported, compiled or executed; this is not a syntax check.

The refactor latch requires a non-LIVE state whose actual _StageObserver.live is
LIVE. _candidate_workspace clears pending-factor/post-iteration flags
(simplex_pivot.jl:118), and _StageObserver forwards refactor_other with the actual
candidate while buffering pricing_phase_reset (lines 20-28). The handoff's root
trial is created at dual_simplex.jl:2113. Auxiliary notifications carry auxiliary
state, and its nested candidates are rooted at auxiliary, so shared diagnostics
alone cannot satisfy the selected identity. The scoped native recovery setting
excludes the checked recovery route. Missing or duplicate latches fail; only the
first candidate reference is retained.

The refactor event occurs before reconstruction at simplex.jl:434. The retained
trial is consequently mutable until unwind, exactly as the report states; no
pre-reconstruction snapshot is claimed. Pending throw additionally requires LIVE
state and its adopted trial factor, different from the saved entry factor. An
auxiliary pricing reset, early LIVE reset or forwarded candidate reset cannot
satisfy this full predicate. The later publication explicitly invalidates LIVE
checkpoints, copies trial state, clears LIVE history and adopts the factor before
pending replay (dual_simplex.jl:2148-2153). Source order supports the discriminator
conditionally; it does not prove this fixture reaches it on a future runtime.

Ordinary diagnostics record the event before invoking the observer and wrap the
thrown sentinel once (simplex_diagnostics.jl:87). Pending replay uses that ordinary
LIVE path; staged dispatch does not add another wrapper. Public make_dual_feasible!
rethrows this nonnumerical wrapper rather than converting it into a numerical
termination. Factor/state publication has already occurred. There is no rollback
or subsequent pending replay after this throw. The selected direct cause test,
throw count, work scalars and event-prefix predicates fit this boundary.

## Ownership and numerical oracle

_copy_pivot_state! preserves the nine LIVE array owners while copying trial values
in place (simplex_pivot.jl:73). The mapped Basis constructor copies its index/state
arrays (simplex.jl:7). Trial owns separate factor/policy storage before preparation;
publication adopts its factor and refactor policy. Pricing copies into the existing
LIVE object, preserving its owner but keeping it distinct from trial pricing.
All 19 declared PricingState fields are compared. Phase reset clears last_monitor,
temporary status and history and sets last_transition=:phase; trial recompute and
bound-flip recompute do not advance pricing history. Thus the selected phase and
pricing comparisons are consistent with source. The old history object is retained
without mutation and its window_count=2 is appropriate for this exact setup.

Initialization copies structural costs and appends zero slack costs, and concatenates
structural and row bounds (simplex.jl:487). The six direct entry model comparisons
bind that ordering for this one-by-one fixture. Scope/model preconditions are
recorded acceptance predicates, not a new general model validator. Fresh frozen
source/fixture pins at M admission remain necessary. The absent journal and exact
fixture setup prevent confusing LIVE working bounds with arbitrary caller-modified
model data. Original-bound still means LIVE postrestoration working bounds.

Entry cost equality is only prospective. Auxiliary numerical repairs may shift
costs even with perturb_degenerate=false; this review does not establish numerical
trajectory equality. A future false entry-cost predicate must preserve the failed
result and stop qualification without retuning, rerunning or inferring a solver
defect. No auxiliary certificate transfer or original optimality follows from
publication equality. Earlier LIVE restoration/recompute/flips, cached stage
mutations and shared diagnostic/consumed work are not rolled back.

Checkpoint clearing and phase-generation advancement follow explicit publication
invalidation. Iteration/refactorization monotonicity, trial equality and throw-time
identity are selected scalar observations, not complete backend kernel accounting.
The ring's direct last-event indexing correctly handles both fewer than 64 events
and wraparound without calling allocating recent_events. The selected event is
recorded before callback; a throw can leave later pending events undelivered.

The raw TOML write precedes the aggregate all(values(checks)) failure. Missing
reachability, duplicate identification, wrong outcome/cause and cost drift remain
false predicates rather than retrospective acceptance changes. Initialization,
parser/import, post-call inspection or serialization errors can prevent complete
raw output; future guarded stdout/stderr/process evidence must preserve such
failures. Neither an exit code nor a type string alone establishes acceptance.

## Computational work and retained memory

No unnecessary NEW production computation, allocation or retention was found:
production/tests are unchanged. No hot path was modified, so a before/after
sparse/dense kernel benchmark is unwarranted for this offline preparation; there
is no measured performance or observer-neutrality claim. Numerical safeguards
remain intact. Existing initialization, auxiliary setup/iterations, factor copies,
refactor/reconstruction and publication costs are unchanged source behavior, not
newly measured or exhaustively counted by this candidate.

The observer adds fixed scalar/identity metadata work per delivered notification,
with no array scan/copy, numerical solve, conversion or growing ledger. Setup adds
three explicit vector copies covering 3(m+n) elements, six here. Post-unwind
publication equality covers at most m+8(m+n) element pairs, 17 here, and entry
equality adds 3(m+n), six. Owner preservation/distinction adds at most 18 identity
comparisons. Pricing comparison covers 19 fields. The two trial-owner comparisons
can each construct nine small nine-reference tuples, at most 18 temporary tuples;
these are cold source-level containers, not vector copies or proven heap allocations.
No new full sparse matrix/nonzero scan occurs in the observer or selected oracle.

The 14-field entry NamedTuple contains one nine-owner tuple, three copy references,
seven identity roles and three scalar values. Together with four probe roles it
implements K's 20 selected identity roles; the three owned vectors, containers,
closure environment and local aliases are additional. The report correctly avoids
treating 20 roles as a retained-graph or byte cap. LIVE/trial/entry-factor/history
roots can keep stage scratch, model metadata and backend/update-chain graphs alive;
retention scales with dimensions, nonzeros, update history and scalar storage,
not just reference count. General precisions and large cases remain unqualified.

After unwind, fixed 40-field and 15-field result tuples plus two corresponding
keyed dictionaries and one outer dictionary add serialization work/retention and
bounded strings/TOML machinery. They do not capture full numerical vectors or
copy diagnostics dictionaries. No measured allocation total, native-free/GC
claim, import-work count or broader precision/backend result is justified.

## Next gate

The proposed M plan correctly requires a fresh exclusive launcher, concrete
source/test/environment/runtime/library/wrapper/report/review/plan/auditor pins
and offline auditor FIRST, then independent numerical/work/admission review BEFORE
at most one guarded exact-candidate attempt. It requires literal auditing of all
40 predicates and 15 observations and preserves early/final failures without
repair, retry or oracle tuning. Compiled-modules=existing plus disabled Pkg automatic
precompile is not presented as cache confinement or complete import-work proof.
This L review authorizes no launch and does not automatically integrate a test.
CI remains off, HH reuse disabled, and all prior broader validation, rejection,
full-suite/x64, bootstrap/cache/init and native-retention gates remain unchanged.
