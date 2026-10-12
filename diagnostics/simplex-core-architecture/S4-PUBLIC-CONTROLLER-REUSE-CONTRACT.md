# S4-R: public-controller reuse seam

Source/evidence only at diagnostic 87ece2e / master 0eb75c3. No Julia, native calls,
hooks, compilation, factors, workspaces or public solves executed. No production,
test, environment or CI changes. Q's accepted cost records and all old scripts remain
untouched. This is a negative readiness decision, not an impossibility proof.

The existing G/I/Q routing clones are NOT a public-controller injection seam.
A bounded public qualification is currently UNSUPPORTED: the narrow clones cannot
redirect every real dispatch from public solve, and a larger isolated module has not
had its loading/method-extension boundary qualified. No numerical plan or new LP is
issued in R. Public-controller reachability and its complete work bound remain OPEN.

## Source-bound route and ownership

| Necessary boundary | Source evidence and consequence |
|---|---|
| Public entry | solver.jl447 `solve` passes the problem and `nothing` diagnostics to `_solve_diagnosed`; its keywords are relaxation/options, not a factor factory or refactor callback. |
| Option dispatch | options.jl159–183 validates five manager symbols and two backend symbols. factorization.jl431–432 maps `SolverOptions{T,M,R}` to `Val(M),Val(R)`. HH factory at huangfu_hall_factorization.jl598–604 constructs real `HuangfuHallFactorization`. A new manager symbol is not accepted by unchanged public option validation. |
| Initial owner | simplex.jl486–530 creates the -I CSC and HH factor BEFORE constructing `SimplexWorkspace{T,F,M,R,D}`. Its factorization field is concretely `F` (line194). Initialization then recomputes with no refactor: FTRAN, BTRAN, pricing and initial event, as already documented in H. |
| Real dispatch | simplex.jl427–431 calls `refactorize!(workspace.factorization,B)` through existing accounting. solver.jl163 and simplex_pivot.jl192 also call the production generic. The HH method reaches its module-local `_hh_refactor_backend` and `_hh_refactor_lu!`; Float64 remains `reuse_symbolic=false` at lines537–538. |
| Transactional state | simplex_pivot.jl45–70 constructs staged state with `ws.factorization`, shared with the live solve. Discarding a staged state does not undo factor work. This is reuse of the established AD/H contract, not new execution. |
| Recovery owner | simplex_recovery.jl90–130 initially constructs a trial with the current factor type, then assigns a FRESH `_basis_factorization(B,ws.options)` result. The attempt increments live refactorizations in `finally`. An adapter only around a previously constructed factor would need compatible construction throughout this route. Checked-policy reachability is not asserted for a particular new run. |
| Original-model gate | solver.jl494 copies the continuous original; the later route checks `_original_primal_feasible(continuous_problem,...)`, may clean up/retry on the original, checks feasibility again and restores the original objective before public OPTIMAL publication. A working-model check cannot replace any of these gates. |

H's accepted thirteen borrowed-assembly consumers and separate allocating refactor
call sites are reused read-only. No new caller census. G/I/Q qualify their explicit
call sequences, not all the public branches above. Matching source hashes establish
comparability only; they do not constitute public candidate execution or a captured
public trajectory. Q endpoint agreement does not close this gap.

## Candidate seams evaluated

1. **Call Q's named refactor clone directly:** rejected for this gate. Q changes three
   routing names and the guarded Float64 keyword; public solve still calls the original
   generic. Such a call repeats the component boundary rather than exercising the
   public controller. Q's exact inverse text remains valid for its original scope.
2. **Redefine the HH method/backend helper in the production module:** rejected.
   Reusing the same method signature is an overwrite, even if temporarily restored.
   Dispatch/global compilation state and concurrent callers are then affected.
3. **Install an adapter after initialization:** not qualified. A different wrapper type
   cannot simply be assigned to an already concrete native-HH workspace field. Rebuilding
   the workspace adds ownership/copy obligations and misses constructor/initial solves.
   Staging shares the factor and recovery creates factors via the closed factory. A full
   adapter would require explicit forwarding (ordinary/prepared FTRAN, BTRAN/unit metadata,
   updates, invalidation, copy, storage/growth and refactor), field access and new-factory
   integration. No claim that these costs are zero or that this is an unmodified path.
4. **Separate complete source module:** plausible NEXT isolation seam, not rejected as
   impossible. Loading an independent nested module named JSimplex could preserve the
   explicit `JSimplex.relax_integrality` self-reference while making model/workspace/HH
   types distinct. It would not qualify the installed production module's dispatch.
   Root JSimplex.jl also includes MOI integration and precompile.jl. The latter contains
   public solve and native factor workloads inside PrecompileTools macros. Merely quoting
   the file's cache-only comment is insufficient to budget a new loading environment.
   External method extensions, self references, include resolution and import-time work
   need an explicit source manifest and inverse before any load. R did not audit that
   larger closure and does not claim that a collision or extra solve actually occurs.

The first three alternatives fail this gate for concrete reasons. The fourth needs a
separate narrow loading-isolation audit, rather than hidden routing substitutions.
No clone, adapter, alternate control, unsafe pointer access or method overwrite was
installed. No factor constructors were invoked to explore which route might work.

## Why no public LP/work budget is frozen yet

An exact optimal witness alone cannot certify which controller branches execute.
`refactorization_interval=1` would only select a threshold; it neither guarantees an
eligible same-pattern native refactor nor bounds all setup/phase/cleanup/certificate
work. Original-basis projection exchanges explicitly do not consume the simplex
iteration budget (solver.jl public contract), and recovery can create a fresh factor.
A finite iteration limit is therefore not a complete factor/solve-call budget. H's
initial two solves and Q's direct lifecycle totals cannot be substituted for it.

Until the loading seam is closed, an alleged complete reference/candidate public call
budget would omit possible loading work or route through the wrong module. R therefore
does not choose a numerical fixture or authorize a launch. No assertion that such a
budget is fundamentally impossible: it must be derived for a particular isolated route
and exact LP, with attempted-call caps and strict abort/no-retry rules, BEFORE launch.

## Work, evidence and continuation

Production computational work, allocation and retained memory are unchanged. R performs
only text reads, hashing and offline predicates. A future candidate still adds an
O(m+nnz(B)) guard per eligible refactor, while existing native CSC copies, numerical
factorization and extraction remain. No adapter or cloned-module overhead has been
measured or represented as free. No benchmark is appropriate for these documentation
changes. Q's GC-dominated inclusive windows and unexplained dense outlier are unchanged;
mixed aggregate GC counters are not a native allocation/free ledger.

Evidence: results/S4-R/source-contract.json records literal-source gates and current
read-time hashes, separately comparing all 558 Q launch pins and selected G/I source
bindings. These are offline predicates, not a Julia parser or proof of exhaustive
call-graph closure. User files, source/test/CI versus master, boot/process identities
and whole previous groups are checked separately. Failed read-only discovery searches
for nonexistent src/workspace.jl and src/*workspace* were corrected to src/simplex.jl;
no numerical attempt or accepted evidence was affected.

ONE next action: S4-S source-only isolated-module loading contract, plan
2026-10-12-hh-isolated-module-loading-contract.md. Establish or reject a concrete
byte-invertible source manifest, external-method ownership and zero hidden numerical
loading work. Do not repeat the public path/caller census or Q measurements. This is
not yet a public numerical qualification plan. Native retention, public integration,
other consumers/control/scalar/platform/fullsuite and broader S4/S6 remain OPEN.
HH reuse remains disabled; CI stays off and all prior rejections stand.
