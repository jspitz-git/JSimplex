# S5-E: active-journal final interruption oracle preparation

OFFLINE ONLY; this freezes two prospective cases, not an executable driver or
numerical launch. No production/test/environment/CI change, new LP arithmetic,
precision/tolerance change, old numerical run or exclusive audit rerun.

## Evidence reconciliation

S5-D evidence preserves the two failed CI runs' active-journal success (21 each)
and separate no-journal interruption group (19 each). Its source comparisons and
raw rows are reused, not recollected. A new text search of test and diagnostic .jl
files finds transfer_precision only in the three precision test files and the HH
scalar integration test. The former split active success from failure, while HH
checks scalar integration without an active journal. None of those test bodies
implements detached active buffers plus final observer interruption. This scoped
search is not a proof that the composition has never run anywhere. File equality
and pin presence do not add execution coverage. No defect is demonstrated.

## Exactly two prospective cases

Use the first testset in test/simplex_precision_state_tests.jl, through its explicit
source checkpoint push, verbatim in numerical construction: m=1,n=2,N=3; Float64
model [1 1], objective [1,2], row lower [1], basis [1]/[BASIC,AT_LOWER,AT_LOWER].
Retain SolverOptions(verbose=false), PFI/native, dual steepest-edge, default
iteration/time limits (100000/Inf) and tolerances. Retain NumericalPolicy(Float64;
simplex_strategy=:adaptive,sparse_pricing=true). Its profile is NATIVE, not checked:
solve_refinement=false,recovery=false,max_refinements=3. Do not change these flags.
The existing journal has costs 1.125/2.25, lower[2]=-0.125/lower[3]=0.75,
active cost and bounds, levels 2/1, cooldowns 11/13, observations 9/8 and shared
source monitor. Preserve all other existing fixture fields.

Install diagnostics through the existing SimplexProgressContext argument to
initialize_from_basis; keep the observer disarmed throughout original setup.
After setup, detach ONLY ws.costs, ws.lower, ws.upper with three ordinary copies.
They must equal their journal active vectors by values and differ by identity;
source journal retains its original owner and active storage. Take the source
baseline only after detachment. Do not recompute after detachment. Create one
SimplexRunBudget(ws); no reset of its start or counters. Arm the observer immediately
before ONE transfer_precision(ws,BigFloat,128,budget,policy;stop=...) per case.

| Case | Observer at armed :refactor_other | Expected outer outcome |
| --- | --- | --- |
| stop | Increment fixed hit count; retain trial reference; set stop flag true | nothing, final guard observes flag |
| throw | Increment fixed hit count; retain trial reference; throw the precreated SingularException(7) | DiagnosticObserverFailure with cause === sentinel |

At other reasons the observer returns without action. Assert the retained trial
is not source and has BigFloat storage, and hit count is exactly one; do not filter
away a wrong-type hit. The stop closure only reads the flag and records a fixed
counter of calls observing true; at least one such call is required for stop.
Throw uses a permanently false stop flag; no assertion of a final post-event stop
call (the observer exception skips it). Record event before invoking observer, as
production does. No callback solves, source mutation, new snapshots, certificates,
I/O or growing event ledger. A single trial Ref retains the fresh graph per case.
If an earlier failure prevents this point, preserve failure; no fixture tuning,
extra success control, retry, warmup or alternative basis is authorized.

## Frozen oracle and observation boundary

Source before/after: compare identity and values of the three detached working
vectors, all six journal vectors, primal/reduced costs/pricing weights, basis
indices/states and devex mask. Journal and bound objects/owner, activity,
original_perturbed, levels, cooldowns, monitor identities and observations are
unchanged; source perturbed flag, factor identity and update-list length unchanged.
This is not a capture of every private backend byte. Preserve source model/progress
values, stored scalar precisions, policy/options, start and offsets, sparse-pricing
cache identity/model binding, stagnation identity and the one manually pushed
checkpoint's identity, vectors and model/phase keys. Capture immutable values and
identity tokens; references alone are not a value snapshot.

Fresh retained object: journal.workspace_id == objectid(fresh), new journal/bounds;
all six journal vector containers distinct from source, corresponding values
converted exactly from stored Float64 values. fresh.costs/lower/upper are identical
to its active journal vectors (not to the source detached vectors). Cost original
and active vectors are distinct; all four bound containers remain distinct even
where values equal. Preserve activity/original_perturbed/levels/cooldowns; both
last_monitor are nothing and observations zero. Fresh stagnation is nothing.
Fresh basis values match, containers and model CSC arrays are owned and distinct;
new factor has no source update history. Copy model/objective/bounds and progress
scaling exactly, preserve policy/options by typed value and flags, shared diagnostics
identity and budget.start_ns. No old numeric weights/pricing cache are transplanted.

With this native policy, recompute does NOT remember a verified checkpoint:
assert fresh.checkpoints is empty, separately from source's one saved checkpoint.
Require fresh.scratch.sparse_pricing === nothing: ordinary recompute reduced-cost
pricing does not construct that cache. The old success test calls the lazy cache
helper to establish fresh-model binding; do NOT repeat that cache-creating call
in this observation-only oracle. Source keeps its existing source-model cache.
Record reconstructed primal/reduced costs/weights as observations; do not prescribe
analytical replacements or claim public feasibility/optimality/original certificate.
The final event follows finite/basis-quality/weight checks. Read private ordinary
fields only; no global method replacement or production hooks are needed.

Source iteration/refactor counters and shared diagnostics/budget are allowed to
advance. On reaching final event, source refactor delta is one and iteration delta
zero; budget obeys _sync_run_budget! and unchanged offsets/start. Existing kernel
counters count in finally, not PREforward; no complete internal native-work claim.
Source and fresh share diagnostics. Snapshot their final counters after return/catch,
not as unchanged state. Observer retention is intentional and is not rollback or
transactional invisibility. Snapshot only after exception identity is saved. Capture
ambient BigFloat precision/rounding before and after; require restoration. Requested
128 bits and stored input bits determine transfer precision; residual-quality scratch
may use wider internal arithmetic already present. Do not assert all scratch is 128.

## Bounded diagnostic storage and work

Three value snapshot groups per case: source before, source after, retained fresh
after return/catch. Fixed schema, no whole-workspace deepcopy or factor graph dump.
Each source group has 31 arrays/76 scalar entries: nine working/journal vectors
(27), three solution/weight vectors (9), basis indices/states plus devex (7),
model CSC/objective/four bounds (8 arrays/15), progress objective/two scaling arrays
(3/5), and the one checkpoint's basis/states/costs/lower/upper (5/13).
Fresh has 26 arrays/63 entries (no checkpoint). Total per case 88 arrays/215 scalar
entries, two cases 176/430. Snapshot bound tags, finite scalar values and stored
precision/bit representation; source Float64 bit identity includes signed zero.
BigFloat values must be independently copied/encoded, not retained mutable scalar
references. Array counts describe schema outputs, not runtime allocation events or
exact bytes. Identity tokens/flags/counters/options/history scalars are a fixed named
record; no length-proportional native metadata. Existing source fixture's model,
factor, cache/checkpoint and one retained fresh graph per case are additional roots;
release case roots after encoding. Neither release nor graph size proves native free.

Extra diagnostic detachment: three length-3 copies per case (six/18 entries total).
Snapshot source checkpoints by reading, not by calling checkpoint_basis again.
Checks compare small vectors/identities; no basis solves or residual recomputation
in observer/oracle. Snapshot and encoding cost consumes time; existing Inf solver
limit is retained, so this is not an expiry test. Later external wall/memory/thread
guards remain mandatory. No benchmark, observer-neutrality or speedup claim.

Existing setup is separately classified: initialize_workspace's initial factor and
reconstruction; initialize_from_basis's selected-basis refactor/reconstruction,
quality checks and devex reset; explicit journal fixture recompute; explicit cache
request and checkpoint construction. Do not label setup zero or merge its counters
into transfer. Transfer adds stored-bit/active-value scans, model/options/progress
conversion, three working plus six journal vector conversions (27 entries here),
selected-basis assembly/new factor, two reconstruction pipeline entries (FTRAN and
BTRAN), pricing/finite scans, up to two basis-quality checks, devex reset, and one
ordinary unit BTRAN for the single steepest-edge row. _maybe_refine_basis_solve!
returns early in reconstruction because solve_refinement=false. In contrast weight
rebuilding directly calls refine_basis_solve!: its quality check and up to THREE
correction BTRANs remain possible even with that flag false. BigFloat quality may
use wider arithmetic and owned scratch. Thus three base transfer solve entries
plus up to three weight corrections are source-derived, not observed native backend
counts; extraction/internal backend work is not instrumented. No copied histories,
certificates, optimization of equal vectors or safeguards removed.

No unnecessary NEW production computational work or memory is introduced. The
small prospective diagnostic retention/scans are explicit and scoped to ownership
oracles. Runtime reachability, outcomes, allocation bytes and exact kernel counters
are unexecuted. Next step may build and independently review one bounded diagnostic
driver for these two cases; it must not launch yet or expand the case matrix.
All prior rejections, CI-off/HH-disabled, S4 gates, native retention and fullsuite
limitations remain unchanged.
