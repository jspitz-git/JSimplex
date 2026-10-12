# S3-D: frozen mixed-route DSE component preparation

SOURCE/EXACT OFFLINE ONLY. No Julia, import, compiler, native call, old driver/audit,
production/test/environment change or new LP family. Inputs reuse S3-B's m=16
identity-plus-A[2,1]=1/8 fixture, objective [-1,0,...], row upper [1,100,...].
The source preparation script is exclusive and must not be rerun.

## Inputs and scope

`results/S3-D/exact-inputs.json` freezes binary64 bits and rational references.
B0=-I. One explicit history update replaces column 1 with A[:,1], giving B1;
the target replaces column 2 with A[:,2]=e2, giving B2. Thus the frozen basis
before the target is [1,18,...,32] (Julia indices). Setup uses
`_initialize_workspace_state`, not `initialize_workspace` or the old public pivot.
It is a component workspace: no recomputation, objective solve, phase, public
iteration, checkpoint or original-model certificate is claimed.

The exact prior direction is -e1-e2/8; entering direction is -e2, pivot -1;
B1' * rho=e2 has rho=[1/8,-1,0,...]; B1*tau=rho has tau=[1/8,65/64,0,...].
Squared norm is 65/64. The frozen all-ones endpoint RHS gives B2 forward result
[1,7/8,-1,...] and transpose result [7/8,1,-1,...]. Eleven offline checks include
these equations and the source-ordered binary64 weight recurrence. No backend
arithmetic or future runtime rounding is inferred from these equations.

All weights initially equal one except the leaving basic weight 65/64 and basic
row 3's positive stress weight 2^-20. The zero coefficient at row 3 must still
raise that weight to the existing Float64 1/10000 floor. The leaving weight also
hits the floor and the entering weight becomes 65/64. This floor stress is not a
claim that such weights arise on a certified public trajectory. Compare recurrence
against captured tau/direction in their original operation order; the frozen
reference is an additional exact-input oracle, not permission to substitute
analytical tau for the real solve. Support omits either zero sign; preserve bits
separately without requiring cross-mode zero signs to match.

For every recorded equation freeze the bound before execution:
exact ||M*z-b||inf <= 64*2^-52*max(1,||M||inf*||z||inf,||b||inf).
Use independent exact rational arithmetic on captured bits after any future run.
This bound is not a production tolerance change or forward-error certificate.

## Private route seam (unexecuted text)

Three exact source extractions are stored as .txt and in source-manifest.json:
update_dual_pricing_weights!, update_dse!, _checked_basis_solve!. Rename these
three functions and their intra-clone calls with prefix _s3d_. Add exactly one
keyword, kernel_mode=_s3d_weight_mode[], to the checked wrapper's existing pipeline
call. Removing that keyword and inverse-renaming restores each original byte
exactly, including whitespace. No production method is overwritten. No pipeline,
factor manager, floor, finite check, refinement guard or numerical body is cloned
or changed. The future private module imports the referenced installed JSimplex
names explicitly; its mode Ref is local to that diagnostic module and set before
a sequence. No observer mode mutation or dynamic global method replacement.

The entering call uses the existing `_pipeline_basis_solve!` keyword directly,
with prepare_update=true. The cloned DSE wrapper uses the other requested mode.
Use original policy `NumericalPolicy(Float64;simplex_strategy=:legacy,
hypersparse=true,refactor_timing=false)` with unchanged native defaults; in
particular solve_refinement=false is the existing profile default, not a removed
guard. Solver options select :dual/:steepest_edge and the selected manager/native
backend for this component wrapper; the old fixture's public :primal/:dantzig
execution is NOT reused or reproduced. All tolerances remain defaults.

Ten planned sequences: five managers x two requested pairs sparse/dense and
dense/sparse. Each starts independently. PFI/FT/SS/BG can enter indexed execution;
the indexed inner kernel still has its own occupancy fallback. Therefore outer
last_mode=:sparse alone does not prove a wholly indexed numerical path. Record
factor sparse dense_fallbacks as well as outer mode and require the intended
non-HH sparse operation to have no inner dense fallback. If unavailable, preserve
that failed qualification; do not tune inputs after runtime. HH necessarily uses
dense fallback for both nonempty calls; its two requested pairs are controls,
not two different numerical routes.

## Conditional component attempt budget

Per sequence, in order:

1. One `_initialize_workspace_state` -> one manager constructor/native LU of -I.
   It allocates the usual model/workspace scratch and configures refactor metrics;
   no finish-initialization/recompute and no setup FTRAN/BTRAN are hidden here.
2. One original pipeline dense FTRAN of A[:,1], one direct replace_column!(...,1),
   then explicit basis/state bookkeeping for structural column 1.
3. One direct unit-RHS BTRAN into rho, invalidate its pipeline support; fill owned
   entering RHS and stress weights. No solve occurs in the snapshot helpers.
4. One requested-mode entering pipeline FTRAN into row_solution; retain its identity.
5. One cloned weight wrapper -> one checked weight pipeline FTRAN into tau; native
   policy's existing false refinement flag gives zero correction solves. Preserve
   the finite-workspace check and fail if recovery/Devex fallback is observed.
6. One direct replace_column!(original_direction,2), then basis/state bookkeeping.
7. One direct forward and one direct transpose endpoint solve for B2.

Thus ten constructors, 20 updates, 60 outer factor-solve entries (40 F/20 B),
zero refactors, factor copies, public iterations or certificate calls. These are
planned maxima on complete successful sequences; an exception aborts that sequence
before the next call, with no implicit retry. Counters increment before every outer
entry, so a throwing call remains counted; snapshots occur after return only.

Additional internal work is separately SOURCE-DERIVED, not an observed counter:
HH's two updates each invoke `_hh_unit_transpose!`, four total across its two
sequences. Each non-HH sequence needs at most one lazy base-view extraction (8),
and each HH constructor one HH extraction (2). Each of these ten extraction
entries has at most one native orientation-validation solve. Unit scaling may
skip it; do not record ten observed solves. Triangular constructors use identity
upper storage and do NOT perform an extra native extraction. Updates do not
refactor or rebuild the native base. Scalar bounds are therefore 60 outer solves
+4 HH internal unit operations +at most10 orientation solves, with nesting explicit;
this sum is not a count of 74 identical backend solves. Native numerical LU is
at most10; native ldiv entries and indexed triangular work are distinct.

These bounds cover the proposed component call sequence only. They do not cover
package loading/JIT/initializers, do not reopen S4 bootstrap analysis, and do not
justify a claim that every native internal attempt was instrumented. Runtime
pre-forward accounting of internal extraction/orientation entries has not been
implemented by these three wrapper clones. A later driver must either supply a
reviewed non-overwriting counter seam or retain those values as source bounds;
it must never relabel inferred entries as measured counts. Complete observed
internal-attempt accounting remains a precise qualification limitation.

## Ownership, work and next action

Retain three bounded owned capture groups per sequence: before weight solve,
before replacement, after replacement. Store rho/tau/direction, weight/basis bits,
prepared identities and owned payloads, update count/contents and actual route
counters. Preserve original direction through the interposed solve. Triangular
reuse follows identity+isequal; HH may replace its prepared payload and reconstruct.
Neither mode is required to retain a reusable cache. Never retain live old native
owners for a memory claim. No growing per-solve ledger or observer callbacks.

Source costs remain those in S3-C: six O(m)-scale vectors/metadata owners, m DSE
row evaluations including zero rows, finite checks up to four length32 scans,
manager/history traversals and optional preparation copies/graph setup. Captures
copy small O(m+history payload) state and serialization happens after the sequence;
these are added diagnostic work, not allocation-free or neutral timing. New
production work/memory is zero; no performance benchmark is warranted.

Preparation is accepted only after independent numerical/work review and a
separate closure. The concrete next action is one bounded driver/counter-seam
implementation review, WITHOUT Julia execution. Freeze explicit imports, all
counters and snapshot schema, inverse-check against this manifest, and settle the
internal-attempt observation limitation. If that requires global method overwrite,
reject that counter design rather than broadening into S4 isolation/bootstrap.
No executable launcher or numerical authorization is produced here. All standing
resource guards and source/user/host pins remain mandatory before any later run.
CI off, HH native reuse disabled; S4/S6 gates, old evidence and rejections unchanged.
