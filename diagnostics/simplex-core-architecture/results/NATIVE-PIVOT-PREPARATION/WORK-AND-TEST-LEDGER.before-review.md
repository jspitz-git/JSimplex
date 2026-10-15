# Offline candidate work and regression ledger

Scope: Task1 of the accepted native pivot policy plan. All Julia text is UNEXECUTED.
No runtime correctness, dispatch, allocation or speedup acceptance is claimed.

## Production frequencies and costs

| Site | Frequency | Added work / retention |
| --- | --- | --- |
| SolverOptions keyword/validation/conversion | setup, remaining budget, recovery/reconstruction | validate two symbols and allowed manager/backend combination, append one Symbol; constant work |
| Positional compatibility wrapper | old16-field construction | append default Symbol; no scan, solve or conversion beyond old field construction |
| Phase/auxiliary/precision copies | existing reconstruction | one field load/store; prior arithmetic/conversion unchanged |
| Options factor factory | each fresh managed setup/recovery | map Symbol to UInt8 enum once; no lookup on solve/update paths |
| Native Float64 fresh factor | initial setup or no-spare refactor | default literal lu(B); selected policy obtains default control, two scalar stores, one lu(B;control); wrapper's existing control copy remains |
| Private spare refactor | existing refactor | same pattern scan O(n+nnz), same lu! and failure publication; no new scan/control mutation/LU |
| Backend copy | existing manager copy | append one enum to new slot container, active remains shared, spare remains private |
| Empty reset | existing refactor | enum retained, no new factor/control/scratch allocation |
| Non-Float64 factor | setup/refactor | original Float32/dense arithmetic and storage; enum dispatch consumes intent only at setup |
| Markowitz/HH nondefault | attempted setup | reject before factorization; default old dispatch |
| FTRAN/BTRAN, candidate scoring, updates | hot loops | source byte-identical; zero new policy reads, scans, copies, conversions, solves or cache |

One Symbol per options object and one enum per native backend may add padding.
No extra native owner or growing cache is retained. Policy changes pivot choices,
fill and numerical work; constant metadata is not a zero-allocation or speedup
claim. Raw auxiliary LU safeguards in the unchanged dual_simplex.jl keep their
old controls. Managed threshold-one and default auxiliary factors can coexist.

## Prospective test groups and mutation sensitivity

- options_and_copy_intent: resetting the symbol in any of six reconstruction
  routes fails; changing unrelated fields fails. Six scalar types, four ordinary
  managers, both policies, legacy16-field compatibility, invalid symbol and
  nondefault HH/Markowitz rejection. MOI default remains unchanged.
- backend_owned_policy: resetting controls, sharing independently built control
  owners or allowing policy mutation fails. All20 settings, initial empty and
  both singular raw-factor wrappers are covered. No control poisoning.
- private_spare_copy_and_failure: wrong fresh/spare publication, loss of copied
  history or loss of selected policy fails. All four managers and both policies;
  pattern/dimension/empty transitions, independent copy reset, separate fresh and
  spare singular failures, preserved solves and subsequent valid refactor.
- precision_and_factory_dispatch: accidentally applying UMFPACK to non-Float64,
  losing intent on return, or changing default HH/Markowitz dispatch fails.
  Literal diagonal solutions [1,2] avoid a self-derived oracle. Other generic
  supported types retain source dispatch but have no new runtime coverage here.

RED text has exactly four named missing-interface predicates and no factor/solve
calls. It will import through an admitted loader later; this document does not
claim import is work-free. Reference RED, candidate GREEN and all cost/public
runs remain UNEXECUTED, with their own concrete attempt budget/admission needed.

Test-only snapshots copy tiny matrix/RHS/control/history values and inspect
owners. These allocations are outside production and must be excluded from
kernel timing, while included in complete driver retention/work accounting.
No observer or production counter was added. The ordinary overlay contains73
original source/environment files; candidate substitutes7source files and adds2
focused test files (75total). Builder is UNEXECUTED, write-once, hash-checked,
confined to a new dedicated ignored staging directory; no existing stage reuse.

Task2 must derive exact assertion/setup/refactor/copy/update/F/B counts from this
specific text, including negative cases and post-failure solves, before launch.
Pinned neighboring test files alone do not constitute execution coverage. There
is no numerical driver, launcher, measured cost, full solver/recovery trial or
new direct prototype in Task1. Task3 owns public/recovery integration.

## Source verification interpretation

prepare.py inverses28edits in7whole files exactly. source-check.json records15
text/hash checks and99bindings, including all70source files and user environment
copies. Baseline514hashes match. Its no_hot_policy_reads predicate uses a filtered
edit set and is not by itself a non-vacuous hot-path proof; author-check.json
separately compares the complete original/candidate solve/update ranges and
refactor body after reversing its sole fresh-LU call change. Runtime syntax,
inference and exception types still require admitted Julia tests.
