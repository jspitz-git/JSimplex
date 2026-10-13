# S5-L: unexecuted pending observer candidate

OFFLINE preparation at diagnostic36f67d5/master513c053. candidate.jl has NOT been
parsed, imported, compiled or executed. No Julia, new LP arithmetic, numerical
probe, launcher, source/test/environment/cache/CI change or accepted audit rerun.
K's118 identities and12-check closure were verified before preparation; K's failed
first closure, replacement and separate reviews are unchanged. J's237 assertions
per failed historical run and78/19 private/phase coverage are reused, not rerun.

## Exact fixture provenance and scope

results/S5-L/prepare.py was saved before its single Python execution and is bound
in source-provenance.json. It extracts three helper functions byte-for-byte:
isolated_pricing_policy, pricing_window! and force_pricing_trial!. The existing
handoff test's problem/policy and workspace/history setup statements are copied
with exactly four indentation spaces removed. source-provenance.json retains the
original text and line/hash identities; fixture-source.txt preserves the complete
existing testset text. The different observer and one public make_dual_feasible!
call replace the old test loop, result branches and post-success weight helper.
No old testset is included or executed. check_basis_weights is excluded because it
performs additional basis solves. No source function is overwritten or cloned.

There is ONE prospective Float64 case on the original one-row/one-column model,
unchanged SolverOptions and isolated native policy (adaptive pricing/stalling,
phase_one=false, recovery/refinement disabled by native defaults). No success
control, resumed call, scalar/backend matrix or numerical oracle solution is added.
The stop callback is the always-false form for this selected observer boundary;
this is not a timeout experiment. Existing model coefficients/options are neither
retuned nor recalculated. Before arming, the candidate compares the initialized
working costs/bounds to the model under the structural/slack ordering, and records
scope predicates. These predicates are prospective and not executed here.

## Concrete observer and selected oracle

PendingObserverProbe has13 fields: four reference roles (LIVE, retained trial,
entry factor, sentinel) and nine fixed Bool/Int fields. An ordinary diagnostic
observer closure captures this probe. It is disarmed during original fixture setup.
After arming, each notification increments a bounded scalar counter. The forwarded
refactor_other latches only a _StageObserver rooted at LIVE, counts every match,
and retains only the first reference. A pending pricing_phase_reset throws the
preconstructed ErrorException only with one latch, notification state LIVE and the
adopted trial factor different from the entry factor. No callback array copy/scan,
basis solve, certificate, refactor or growing event ledger is added.

The retained trial is mutable until unwind, not a snapshot of its pre-reconstruction
refactor event. After the public call unwinds,40 fixed Boolean predicates check
K's selected publication, original model relationship, owner/cause identity,
pricing/history/checkpoint, scalar consumed work and event-prefix contract.
Direct DiagnosticObserverFailure and cause identity are required. Monotone work
and equality to throw-time scalar values are not complete backend counters.
The existing at-most64-entry event ring is indexed directly; recent_events is not
called. Fifteen fixed observations retain type names, latch/hit/callback counts,
entry/final/throw work, phase-event counts and last event. No new numerical vector
snapshot or full diagnostic dictionary copy is serialized.

Checks and observations are written to one fresh TOML output BEFORE the aggregate
failure is raised. All40 predicates must pass; missing/duplicate latch, unreached
target, wrong exception, selected-cost drift or other false condition fails
qualification. An initialization/import/parser failure may precede this output;
future guarded stdout/stderr/process evidence must preserve it. Neither zero exit
alone nor a type string alone is accepted. No silent fix, rerun or fixture tuning
is authorized. Auxiliary numerical repairs can change costs even though degenerate
perturbations are disabled: entry-cost equality remains a prospective acceptance
condition, not a proven source invariant or solver-defect oracle.

Publication precedes the selected callback. Earlier live restoration/recompute/
flips, shared diagnostic work, candidate cache mutations and charged refactors are
not rolled back. The fixture has no journal and no unowned buffer alterations;
"original-bound" means LIVE postrestoration working bounds. No auxiliary certificate
transfer or original optimality claim follows. Pending events after the throw may
remain undelivered. No hidden-trajectory, observer-neutrality or general backend
recovery claim is made.

## Concrete memory and work accounting

No new production work, allocation or retention: production/tests are unchanged.
This cold diagnostic preparation needs no benchmark and makes no speedup claim.
The candidate's explicit entry payload is three copied vectors,3(m+n) entries,
six here. selected_owners returns nine existing array references. Entry stores a
14-field NamedTuple: that nine-owner tuple, three copied arrays, seven identity
references (problem/options/progress/pricing/refactor-policy/history/journal), and
three scalar work/generation values. Together with four probe reference roles this
implements K's20 selected identity roles, excluding container/payload references.

Concrete containers additionally include one13-field mutable probe, one observer
closure, the14-field entry NamedTuple and nine-owner Tuple, and three owned vectors.
After unwind a second nine-owner tuple references LIVE arrays; the trial selector
is called up to18 times by the two short-circuit owner/value comparisons, constructing
small temporary nine-reference tuples at the source level. These are not vector
copies or measured heap allocations; compiler elision is untested. Local variable
aliases, closure environments and caller/import/runtime roots are additional to
K's selected role count. The actual retained graph is not bounded by20 slots.

Post-unwind owner checks use up to18 identity comparisons, publication checks up
to m+8(m+n) element pairs (17 here), and entry equality up to3(m+n) pairs (six).
Pricing equality examines the19 declared PricingState fields, including the monitor
reference which phase reset clears. Fixed scalar/identity predicates are additional.
Short-circuit checks can stop early; these are schema coverage counts, not physical
loads. No full sparse matrix scan, solve or new conversion is added to callbacks.
Existing helper/solver numerical work is unchanged and not exhaustively counted.

The result has one40-field check NamedTuple and one15-field observation NamedTuple.
Serialization creates two fixed-key dictionaries (40 and15 entries) and a two-entry
outer dictionary, plus bounded key/type/event strings and ordinary TOML machinery.
This occurs after the numerical call and is not zero work. Retaining LIVE/trial/
entry-factor/history roots can retain stage buffers and backend/update-chain graphs;
no GC collection/native-free or observer-neutrality claim. No growing ledger or
per-solve numerical snapshot is introduced. General precision/large-problem costs
remain unqualified. There is no unnecessary NEW production work/memory.

## Next admission boundary

A separate S5-M stage must FIRST prepare a concrete guarded launcher, full fresh
pins and an offline auditor, then obtain fresh independent numerical/work/admission
review. Only that later gate may admit at most ONE attempt of this frozen candidate.
It must reject unexpected evidence, preserve any failure without tuning/retry, and
resolve actual wrappers/compiled-modules admission without a Julia probe. This L
stage authorizes no execution. CI stays off, HH reuse disabled; all prior broad
S3/S4/S5/S6, bootstrap/retention/full-suite and rejection limits remain unchanged.
