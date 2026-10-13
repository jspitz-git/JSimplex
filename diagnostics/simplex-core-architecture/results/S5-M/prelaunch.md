# S5-M prelaunch admission request

Only one new qualification-1 attempt is proposed. Execute the frozen S5-L 181-line
candidate directly (SHA b553d449a0db620bfae1970861806a778bbf45d36465026e8b4a540e4b4f4288),
one existing Float64 initialization and one public make_dual_feasible! case. No
old test include, check_basis_weights, success control, resume or extra solve.
No Julia query/parser/import/compile has run during preparation.

The concrete command is command.json. The outer wrapper resolves its root to
basis-update-chain-bench/JSimplex.jl, reads the export from its nested legacy
wrapper using sed, prepends memory-probe and precompiled-full depots, then execs
the pinned aarch64 Julia 1.13.0 binary with startup disabled. The nested wrapper
is read as data, not executed. Both files and the installed runtime/dependency
inventory are pinned. Existing mode is documented as disallowing new precompile
files; loading.jl compilecache is guarded by use_compiled_modules==1. Pkg automatic
precompile is additionally disabled. This admits a single Julia process; it is
not cache confinement, complete import/init work or actual loader-path capture.
No depot/cache is edited by preparation; ordinary loading may touch caches.

The unchanged guard holds the global lock, rejects existing Julia, checks pins
and RAM before the exclusive output directory, supplies one Julia/BLAS/OMP/MKL
thread, 2 GiB heap hint and 8 GiB virtual-memory limit. It enforces RAM>=6 GiB,
swap<=1 GiB, and 120 seconds from child creation including imports/compilation,
with one-second sampling. It cleans the complete child group and stores boot,
start ticks, command, process reason/exit, resources and raw stdout/stderr.
A separate fresh prior-group check is mandatory immediately before launch.
No MPS input is used; prohibited big/largo/AnyMOD files are hashed by the guard
for alias exclusion, never solved. Existing guard is reusable infrastructure,
not a rerun of any accepted exclusive diagnostic script.

The new audit checks exact command, complete pinned trees and hashes/resolved
paths, exact candidate, 40 literal boolean predicates, 15 observations with exact
key/type schema, explicit wrapper and sentinel cause identity predicate, exactly
one latch/hit, monotone work and equality to throw-time work, callback/event prefix,
resource/process gates and fresh whole-group absence. The predeclared type string
is JSimplex.DiagnosticObserverFailure{ErrorException}; cause ErrorException. Types
follow the nonexported package wrapper and Base-exported sentinel source, not a
Julia probe. A string discrepancy is a failed qualification, not a reason to
edit the oracle or rerun. Early missing/malformed raw is preserved as failed gates.

Entry-model initialization copies costs and concatenates column/row bounds for
the existing one-by-one fixture. Native policy leaves phase_one, recovery and
solve_refinement false; adaptive pricing/stalling alone are enabled. These are
source-reviewed prerequisites and runtime predicates. Cost equality remains
prospective because auxiliary numerical repairs can shift costs. Any failure
stops qualification, without repair/retry/tuning or inference of a production bug.
No certificate transfer, rollback, observer neutrality or full-suite proof.

L's selected ownership and work scope is unchanged: three vector copies/six
entries, 17 publication element pairs plus six entry comparisons, 19 pricing
fields, fixed callback metadata, no callback vector scan/copy/numerics/growing
ledger. Twenty selected identity roles do not bound retained graphs. Stage,
entry-factor and history references can retain scratch and backend histories.
No complete PREforward/backend/import count or benchmark is claimed. Production,
tests, options, precision and CI are unchanged; no unnecessary production work
is introduced. Existing 237 historical assertions per failed CI run and 78/19
scoped tests are reused and never rerun.

Review must independently inspect candidate/provenance/source, concrete launcher,
auditor/schema, wrappers/guard/loading admission and full pins. Launch requires
separate accepted prelaunch review bound to the immutable pin manifest. Closure
and final independent review follow the one attempt, with no automatic test
promotion. All prior failures and rejection gates remain unchanged.
