# S4-W: public-controller attempt ledger

SOURCE/EVIDENCE ONLY at c013d8d / master0eb75c3. No Julia, module load, macro execution,
native-library call, compilation, hook, production/test/environment change, new LP arithmetic
or prior diagnostic/numerical/cost rerun. The ledger has26 operation/stage rows with source
locations, local conditional limits and ownership/work notes. Complete aggregate attempt
caps remain UNKNOWN, not zero, and no instrumentation or numerical plan is approved.

## Scope and dispatch

The frozen S4-T two-row/three-column LP, bits, exact witness and conditional three-pivot
Dantzig path are reused unchanged. Options are T's prospective Float64/native HH/primal/
legacy/Dantzig, presolve=false, scaling=off, interval1, iteration_limit4 and time30; they
are not a captured or launch-ready payload. S's seven root substitutions plus one candidate
HH keyword remain frozen. V's bootstrap investigation is not reopened.

Public solve calls _solve_diagnosed(problem,nothing). Adding diagnostics or an observer
through the internal entry is explicitly a different entry. Automatic native/legacy policy
has checked refinement/recovery/incremental/crash/phase_one/precision/LP switches false;
max_refinements nevertheless defaults to3 and bounds native helper work. Native safeguards
are not disabled by those false switches. Dantzig excludes steepest/devex updates and the
auto-edge recursion branch. No controls, tolerances, arithmetic precision or safeguards
are altered to make a bound easier to derive.

Model validation and the owned continuous model precede identity presolve/scaling. They
still scan/copy model data. Direct workspace initialization creates the -I HH factor and
then recomputes primal and dual state. A successful recompute contributes ordinary F+B,
with optional refactor before them. The refactorizations scalar does not count initial
factor construction; cleanup may overwrite that scalar with inherited prior totals while
retaining the real initialization work. This matters even when iteration allowance is zero.

Legacy primal phase construction is separate from the policy.phase_one flag. Its scan can
construct artificial columns on violations; on T's conditional initial-feasible path it
returns the initial workspace. No runtime absence is proved here. Later export/phase routes
remain in the ledger as conditional branches rather than being silently assigned zero.

## New concrete work boundaries

The source establishes two omissions from any budget based only on ordinary timers and
successful simplex iterations:

1. _original_dual_witness in dual_simplex.jl1683 calls transpose_solve directly, outside
   _timed_simplex. An OPTIMAL internal result reaching that witness incurs one additional
   BTRAN. A failed original witness can invoke one native correction BTRAN and another
   complete certificate. Thus T's four reconstruction BTRAN plus three pivot-row BTRAN
   require at least the terminal witness as a separate conditional category. This is a
   source count, not an observed eight-call total or complete execution bound.
2. _project_postsolve_basis! in solver.jl86 loops over a fixed displaced structural-column
   vector, length<=n=3. It can attempt up to3 prepared FTRAN/update pairs, up to3 interval
   refactors plus one final refactor/recompute. Those direct update/refactor sites are not
   wrapped by the ordinary timers and do not increment workspace.iterations. Partial work
   survives a failed projection. With presolve off, failed original primal feasibility can
   still reach cleanup, so the branch cannot be excluded merely by option spelling.

These findings do not require or justify production changes. Existing counters correctly
serve their documented scoped purpose; they are not a complete public work ledger.

## Local limits that can be stated without a trial solve

See results/S4-W/attempt-ledger.json for26 rows. These limits apply PER INVOCATION that
reaches the relevant source sites; they are not additive without caller multiplicities.
Exceptions/guards can stop earlier, and attempted work remains work.

- A legacy candidate pass starts with m+n=5 attempts, but refresh and successful price
  correction reset attempts_left. A price-recovery flag permits at most one such helper
  call across the enclosing iteration. We do not label5 a whole-iteration cap.
- A native pivot-row call has one initial unit-metadata BTRAN and at most3 correction
  BTRAN through _try_native_dual_correction!. Unit metadata is an argument specialization,
  not another solve. A tiny-direction sensitivity helper adds at most one ordinary FTRAN.
- Price recovery has one fresh cost-RHS BTRAN and at most one correction with ordinary
  local_reconstruction=false. Point recovery can add one FTRAN, then joint repair with
  at most8 sweeps and at most row-nnz+1 local passes per row. These also scan/copy vectors.
- _native_cleanup_solve! has two correction sites only when local reconstruction is
  enabled; therefore a private primal-then-dual cleanup recompute has at most2F+2B
  correction solves. It short-circuits on primal failure. Local-row reconstruction and
  residual/certificate checks have separate costs; this is not a total quality-call bound.
- One HH constructor/refactor reaching its backend has at most one numeric entry and
  one extraction. Extraction has at most one native scaling-orientation ldiv. A successful
  update invokes one internal HH unit transpose after prechecks; it is additional to the
  public BTRAN ledger. These are source-derived bounds, not native instrumentation.
- cleanup_original can call itself once without target_primal. That second invocation
  cannot set projected/preserve_primal through the omitted target block and cannot recur
  through the same condition. An outer cleanup-or-retry may then make one original-core
  retry. All keep the original clock/consumed iteration allowance, yet perform new setup.
- The original-objective driver has three cleanup passes, and its forced-feasibility loop
  caps nonprogress rounds at min(2,max_recovery_rounds), resetting after progress and
  permitting a final verification. This is not three total factorizations or verifications.

## What prevents a complete aggregate cap

The alternate phase selected inside original cleanup can be dual despite the public primal
request. _solve_continuous_dual! temporarily installs dual options. make_dual_feasible!,
auxiliary construction, native price/direction/pivot repairs, original-cost restoration
and possible return to primal must be composed with retry offsets. _auxiliary_workspace
actually copy_basis_factorization's the factor and recomputes F+B. HH shares extracted
base/history prefix but owns new solve scratch and no native refactor workspace. A claim
of zero factor copies on the complete public path would be wrong.

The ledger marks aggregate native-dual/auxiliary caller multiplicities and associated
certificate/quality/exception counts UNKNOWN. Source bounds on one helper, or a shared
clock, do not derive them. There is no proof of an unbounded loop here either. The exact
remaining dependency is a branch/rank composition for the original-cleanup dual route,
including legacy recursive numerical repairs and auxiliary ownership. W therefore does
not enumerate source insertions/inverses for executable counters: the plan makes that
conditional on a finite complete prospective budget, which has not been established.

A future design must count attempts before forwarding, distinguish wrappers from actual
kernels to avoid double counting, account all constructor/extraction/internal-unit work,
and preserve caller exception provenance. Existing enabled timers increment in finally,
so they count covered throws but cannot enforce a PRE-forward stop and miss the direct
sites above. Public diagnostics=nothing records no event ring; optional diagnostics have
fixed64 event history but cumulative counters, not a complete ordered trajectory. Additional
serialization/capture is driver work with its own budget, not another proof solve.

Original primal/objective/complementarity certificates remain intact. A mathematical T
witness does not certify a future rounded output. Native correction helpers sometimes use
compensated quality directly; general quality and row-certificate fallbacks can have wider
internal evaluation. No such unchanged existing work is suppressed, and no new precision
promotion is introduced. All quality/certificate calls and their scans belong in a future
budget even when no factor solve occurs.

## Representation, cost and disposition

For the T workspace/public basis assembly, Float64 values and Int64 indices supply the
matching CSC representation. Only this matching-type conversion has the identity argument.
The candidate S keyword evaluates the conversion in its O(m+nnz(B)) pattern guard and at
lu! input; other input types may allocate twice. The source route does not prove actual
future type/control/pattern dispatch or symbolic reuse. Native failure preservation is
not whole-workspace rollback. S4-G/I/K/Q lifecycle evidence is reused without any rerun.

No production computational work, allocations or retained memory were added. Offline
source reads,26 ledger rows,22 literal checks and556 read-time hashes are the new evidence;
source-excerpts.json preserves16 exact line ranges. These checks are not a complete static
call graph or execution oracle. Prospective instrumentation and its scans/copies/retained
records remain undesigned; benchmark claims would be inappropriate. Actual refactor,
update-chain and certificate work is described with its stage/frequency, not optimized away.

ONE next source-only task is the original-cleanup dual/auxiliary composition just identified:
2026-10-12-hh-postsolve-dual-work-contract.md. Reuse W/T/S without repeating their audits,
do not reopen bootstrap, and do not create a numerical plan. Any remaining unqualified
multiplicity must stay explicit rather than being assigned a large guessed cap. V's
bootstrap/cache/init gates, native retention and broaderS4/S6/fullsuite remain OPEN;
HH reuse disabled, CI off, master/production/test/env and Q evidence/rejections unchanged.
