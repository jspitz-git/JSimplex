# S5-P: supplied-basis initialization ownership and admission

S5-P is SOURCE/EVIDENCE ONLY. No Julia, Julia parser/import/compile probe,
fixture, driver, launcher, factor, solver, certificate or numerical call was run.
Production, tests, environment, cache, CI and master remain unchanged. This closes
one inventory reconciliation, not the broader S5/S6 gates or an optimization.

## Evidence and actual callers

`results/S5-P/evidence.json` has 22 literal/source checks, 157 fresh read-time
SHA-256 bindings, six exact source excerpts and a textual caller inventory.
There are 40 references in src/test/dev: one production definition, 34 test call
sites, three dev call sites and two isdefined checks. No other literal production
caller was found. This is not proof against dynamic invocation or external users.
The three dev calls are two benchmark-helper uses and one JET target; none was run.
The non-start callers build inputs for phase-one, precision recovery, LP refinement,
HH or hypersparse tests. Their presence is not execution evidence for this stage.

The eight selected testsets have 16 original summary rows across the two failed
historical CI runs, 38142752357 and 38149970679. Each run separately records:

| Test group | Passes | Scope |
| --- | ---: | --- |
| Owned feasible structural diagonal basis | 360 | Direct initializer: five scalar types, four managers, two backends; input-basis vector nonidentity and model value preservation |
| Objective-aware nonbasic states | 7 | Direct initializer with zero rows; an additional crash-only zero-column assertion |
| Dependent and zero columns | 5 | Direct reliable reconstruction and duplicate-index rejection, with crash selection assertions |
| Existing clock and completed-step budget | 12 | Adjacent crash/public-driver coverage; not direct initializer stop coverage |
| Singular bases and illegal nonbasic bounds | 3 | Direct exception union, free-with-finite-bound and missing-upper rejection |
| Stored BigFloat precision | 4 | Direct initialization inside lower ambient precision; stored coefficient preserved |
| Fixed, upper-only and free variables with rows | 6 | Direct initializer after crash, two algorithms |
| Empty model | 3 | Direct empty initialization plus crash basis assertion |

The sum is 400 PASS in EACH failed run, not a full-suite pass. The seven groups
containing direct initializer calls sum to 388, but their assertions also cover
crash/setup; 388 is not a count of initializer-only assertions. All 16 selected
whole test files match their historical versions byte for byte. All 22 comparisons
of eleven direct supporting production files match. The two explicit differences
are simplex_perturbation.jl, already changed by S5-C; they are not hidden by the
source-match label. No full transitive backend/environment identity is inferred
from this selected source comparison. Historical source membership is stronger
than an unused pin but still does not capture hidden runtime trajectories.

Initial host verification rehashed all O827/GREEN and O1347/master inventories,
both raw9 sets and the O20 closure bindings; audits24 each, postchecks9/10 and
publication4 remain PASS. Rejected O admission, separate required-membership
correction and final accepted admission/GREEN/master reviews remain preserved.
N provenance is retained through O's saved original-test mapping and bound reviews;
no historical script was rerun. Fresh boot/start/command/full-PGID scanning found no
Julia or member of the fourteen recorded groups. Master remains 35a6a9f and the
starting diagnostic ref abdcdf3; both remote refs match. User6 hashes are unchanged.

Two new offline collection mistakes are preserved, not reclassified as passes:
`host-check-1-failure.json` records relative raw-key resolution against the wrong
base; the new corrected read uses O/run. `source_contract.py` failed before writing
evidence because a guessed refactorization filename was absent. It is preserved;
`source_contract_2.py` changes that path to the actual refactorization_policy.jl and
adds the failed artifacts to its inventory. Earlier read-only source lookups also
reported absent guessed basis-solve/scaling/numerical-policy paths; actual files
were then located with rg. None executed Julia or changed source. New collectors
are frozen after this stage, including failed versions.

## Ordered ownership and admission

1. Keyword defaults construct a NumericalPolicy and, if omitted, a progress
   context. The latter copies the objective and creates identity scaling. Supplied
   progress is initially shared. The stop wrapper records callback exception
   provenance; constructing it does not invoke stop.
2. `_with_start_precision` encloses initialization. Generic scalar types call
   through. BigFloat uses the maximum of ambient precision, policy solve-tolerance
   precision, stored matrix/objective precision and finite model-bound precision.
   The setprecision do block restores ambient precision on return/unwind. This
   neither enables precision recovery nor proves every options field has that
   precision; typed BigFloat option tolerances retain their stored values and
   time_limit is converted to Float64.
3. `initialize_workspace` first validates/converts options, allocates independent
   working costs, concatenated lower/upper arrays, slack basis, primal/prices/
   weights/scratch, and factors the default -I basis. It retains `problem` itself;
   "owned workspace" is not a deep copy of the input model. The bound arrays are
   distinct containers; this is not a deep-copy guarantee for every scalar object.
   It recomputes the default state and emits refactor_initial before examining
   the supplied basis. This phase uses the supplied progress policy, which can
   differ from the separate policy keyword. Failures here precede basis admission.
4. `_install_driver_policy!` replaces the workspace's immutable progress value,
   retaining start_ns, offsets and objective/scaling/diagnostics references. It
   does not reset the external clock or clone shared diagnostic storage. The
   caller's progress value remains intact while its referenced objects may change.
   Refactorization configuration was already initialized under the earlier policy;
   policy installation itself does not rerun that configuration.
5. `Basis(basic_indices,states)` creates two new vector containers (Int broadcast
   and collect). Shape, ranges, uniqueness and BASIC-mask consistency are checked;
   then every nonbasic state's bound legality is checked. The borrowed model is
   not copied here. Invalid input can therefore arrive AFTER default factor/solve/
   diagnostic work; it does not imply whole-function rollback or zero work.
6. Checkpoint/pricing invalidation clears local histories/rejections and advances
   phase_generation. `recompute!(refactorize=true,caller_guard=guard)` validates
   again, assembles a borrowed basis, invokes a factor refactorization, increments
   work and emits refactor_other BEFORE primal/dual reconstruction. Logger errors
   and callback errors preserve guard provenance; observer errors are wrapped by
   diagnostics. An observer may retain the otherwise unpublished workspace.
7. Reconstruction computes nonbasic values/RHS, primal solve, basic-cost RHS,
   transpose solve and reduced costs. Checked refinement/recovery can add work and
   checkpoints. Finally finite checks short-circuit into fresh basis solve-quality
   tests, then reset_devex! sets references/weights (and conditionally auto metadata).
   There is no final top-level stop check or feasibility/certificate call here.

Returned reliable equations do not establish primal or dual feasibility, forward
error, pivot safety or original-model certification. The function does not produce
a public solve status or certificate. Default/supplied basis containers differ, but
value equality alone cannot establish ownership. Arbitrary callback mutation and
retention are outside the selected ownership claim; shared diagnostics are mutable.

## Stop, policy and clock boundaries

The stop keyword is not a pre-initialization or pre-factorization admission guard.
The public body does not call it directly. `_checked_basis_solve!` always performs
its base solve before optional refinement. With default native policy both
solve_refinement and recovery are false, including when strategy is adaptive;
there is consequently no mandatory stop invocation on that uncomplicated path.
Even checked refinement can return reliable quality before reaching its conditional
stop checks. A true callback return can decline further refinement/checkpoint work;
it does not universally require initializer failure or cancellation status.

When recovery is enabled and the remaining recompute predicates hold, the
checkpoint helper calls stop before quality/copy and again after its observer,
before storing. Default recompute receives no caller guard and uses its clock-only
fallback; supplied-basis recompute receives the explicit callback guard instead.
The latter is not automatically OR-combined with the options clock. Exceptions
from that callback are rethrown unchanged by _StopCallback. No actual expiry or
runtime stop invocation is established by these source facts.

The existing clock/exception tests primarily exercise crash_basis, _crash_workspace
or full drivers. Supplied-progress tests elsewhere exercise successful setup and
later transfer/recovery. The inspected 34 direct test call sites do not supply a
stop keyword. Source equivalence and crash coverage do not qualify the composition
of a caller-owned basis, shared progress/diagnostics and an explicit throwing stop
at the supplied-basis recovery checkpoint boundary.

This is the ONE selected unqualified composition. It is not a demonstrated defect,
claim that the path never executed, or request to make native cancellation stronger.
A subsequent offline oracle stage may check whether an existing tiny fixture and
source-supported discriminator suffice. It must not silently turn this into a
numerical plan, add a new model, or assume stop is polled before factor work.

## Conditional cold work and retention

These are source entry sites and explicit storage operations, not measured
allocations or a complete PREforward/backend/import budget. Let m be rows, n
columns, v=m+n, nnzA model entries and nnzB assembled basis entries. Failure at any
step can prevent later entries. No benchmark is warranted: no production changes.

| Boundary | Source work/storage on a successful uncomplicated native path |
| --- | --- |
| Omitted progress/default metadata | One objective vector copy of n entries; identity scaling vectors; scalar options/policy conversions/checks. Supplied progress bypasses that constructor. |
| Working initialization | Costs vector (n copied plus m zeroed), two v-entry concatenations, v states and m basis indices; -I CSC construction; one factor factory invocation. Primal, prices, weights and devex v-sized buffers; scratch includes four m-sized numeric work vectors, two v-sized numeric vectors, two v-sized masks, candidate capacity and empty/lazy caches. Factor storage/metrics remain backend dependent. |
| Default and imported recompute | Two calls, each with one base FTRAN and one base BTRAN entry: four total source solve sites across this path. Imported reconstruction additionally has one refactorize! entry. Factor factory/internal backend work is additional, not counted as one equivalent solve. RHS and reduced-price scans scale O(v+nnzA); assembly O(m+nnzB). |
| Supplied admission | Two Basis container copies, m+v entries, including Int conversion; validation range/duplicate/state scans and one v-state bound loop. No factor copy or update-chain copy is explicitly requested by this function. |
| Repeated validation | Five direct _validate_basis traversals on successful native/recovery-off path: default recompute, explicit imported validation, imported recompute, refactor assembly, final quality assembly. Checked refinement/checkpoint helpers add more. This is existing safeguard work, not an optimization proposal. |
| Final quality | Up to three v-vector finite scans plus conditional positive-weight scan; fresh basis assembly, m RHS allocation with nonbasic/model scan, four m-sized initial SolveQualityScratch arrays plus two initially-empty arrays; primal m-entry gather and, only if primal quality passes, cost m-entry gather. Up to two solve_quality! entries; these are residual/error checks, not additional basis solves. Hardware-float compensated quality may resize the initially-empty arrays; BigFloat/exact costs differ. |
| Refinement/recovery additions | Each enabled refinement can allocate lazy quality buffers, copy RHS into scratch and perform up to max_refinements correction solves with repeated residual scans/copies. Each accepted checkpoint owns five vector containers (Basis two plus costs/lower/upper three), m+4v elements, in addition to reliability scratch. Both default and imported recompute can attempt checkpointing; imported invalidation clears earlier local history. Caller observers can retain objects. |
| Weight reset | Two v fills and m indexed writes at final reset, plus another such reset after imported refactor when selected dual rule is devex; auto metadata can add a v validity fill/event if state exists. No steepest-edge inverse-weight solves are explicitly performed by final reset_devex!. |

Repeated work depends on native/checked flags, early return, matrix dimensions,
nonzeros, scalar precision, factor backend and observer behavior. At this fresh
boundary update history is normally empty; retained factors, lazy scratch,
checkpoint and observer references still do not imply a native-memory bound or
collection/free proof. No unnecessary NEW production work, allocation or retained
memory is introduced by S5-P. Existing safety checks remain; no speedup, memory
saving, complete numerical budget or full-suite/x64 claim is made.

Independent review, separate PASS closure and verified diagnostic publication are
required. CI-off, HH-disabled, prior rejected candidates, Q GC/outlier evidence,
bootstrap/cache/init/whole-controller/native-retention and broader S3/S4/S5/S6
limitations remain unchanged. All O/N/M/L/K/J/I/F/G/H frozen evidence is preserved.
