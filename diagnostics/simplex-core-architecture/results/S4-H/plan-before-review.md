# S4-I: two actual borrowed-assembly HH workspace lifecycles

NEW bounded diagnostic qualification after S4-H review. No production/test edit,
no old execution/auditor rerun. Reference calls actual recompute!; candidate adds
an exact source clone of its keyword method under a distinct name, replacing ONLY
the refactorize!(workspace.factorization,B) call with a new distinct HH clone.
HH clone matches the accepted G transformation (routing names plus conditional
Float64 lu!reuse keyword); do not execute G driver. Offline inverse source equality
must hold before launch. Initialization always uses actual initialize_workspace
and production recompute!(false), not cloned setup or fabricated factor output.

## Fixed fixture and controls

Two independent Float64/Int64 workspaces: reference then candidate. A has five
full structural columns [4,1],[1,3],[7,1],[1,2],[2,4] (10storedentries), objective
[1,2,3,4,5], column lower0/upperInf, fixed row bounds[1,2]. Exact input bits and
rational oracles stored before launch. SolverOptions(basis_update=:huangfu_hall,
verbose=false,time_limit=30,iteration_limit=20), all other defaults/native policy
unchanged. These are new bounded diagnostic inputs, not repairs to old fixtures.
No reset/warmup/limit extension/tolerance/precision/control changes. Diagnostics
observer=nothing/kernel_timing=true from construction; no logger callbacks
(NullLogger scope). Initial scalar precision/rounding and library pins verified.

Basis changes use real Basis with states AT_LOWER except BASIC indices. Capture
owned pre/post values; no alias-only value proof. Basis labels here are declared
component setup, not solver pivots or feasible/optimal certificates.

## Exactly one lifecycle per side

1. initialize_workspace once: actual HH(-I), scratch caches its input CSC;
   mandatory recompute(false)1FTRAN1BTRAN, :refactor_initial. No other setup solve.
2. Set basis[1,2], call recompute(refactorize=true) once to B1=[4 1;1 3]. This
   grows existing assembly from2to4storedentries; candidate guard false due pattern
   change. Own one public basis_matrix result, copy actual HH factor ONCE(savedB1).
3. Set basis[3,2]. Call actual _basis_matrix! ONCE explicitly, saving same scratch
   array identities and contents for B2=[7 1;1 3]. The actual assembly overwrites
   the formerly borrowed B1. Before any refactor, one direct FTRAN on liveB1 and
   one direct BTRAN on savedB1 with rhs[1,2] must still solve B1; public ownedB1 and
   model A unchanged. Then recompute(refactorize=true) once on B2, internally
   assembling again; candidate guard true on same pattern. Record old symbolic
   owner held before mutation; no pointer-reuse inference. Reference rebuilds.
4. Set basis[6,7](slacks), recompute(refactorize=true) once to -I, shrinking4to2
   storedentries in actual scratch vectors. Candidate guard false. Do not assert
   allocator/native retained-byte bounds from array identity/capacity observations.
5. Set basis[4,5](singular[1 2;2 4]), own pre-call factor and selected workspace
   state, then recompute(refactorize=true) once. Both must throw SingularException;
   candidate guard false(changed diagonal->full pattern). Existing finally counts
   the failed kernel once. No successful refactor event/increment/reconstruction.
   Factor refactor_workspace becomes nothing; extracted base/history/pools/saved
   state preserved. Workspace basis stays[4,5], basic_mask and scratch CSC reflect
   the singular candidate, so do NOT demand full-workspace rollback. No later
   recompute/recovery/solver continuation. One FTRAN+BTRAN on live -I and savedB1
   (four direct solves total), all rhs[1,2], validate retained factors only.

## Exact budget and oracles

Per side:1initialize_workspace/1initialHHconstruction,1implicit setup recompute,
4explicit recompute calls(3success+1singular),1public basis_matrix,1explicit
_basis_matrix!,4implicit _basis_matrix! calls,1HHcopy,6direct HHsolves(3F3B),
8mandatory reconstruction solves(4F4B; setup+3success). No replace_column! calls.
Total2workspaces/2initialfactors/2copies/8refactorattempts/10borrowedassemblies/
2publicassemblies/28HHsolves(14F14B). Setup -I spdiagm construction is additional
assembly work, not a borrowed-assembly call. Native numeric entries10derived:
2initial+6success+2singular;8successful extractions can add UPTO8native scaling
validation solves, source bound, not observed counter. Native policy causes no
quality/refinement/checkpoint/certificate calls; assert actual flags, no overrides.

Existing kernel window per side includes4F4B and4refactor kernels(total8/8/8),
including failed refactor. Six direct solves per side are outside workspace kernel
counters but have explicit preforward counters. Successful workspace.refactorizations
ends3, iterations0; events exactly initial+3refactor_other. No correction/restore/
checkpoint. No pricing pool/hypersparse state must be fabricated just to test
invalidation; record actual nothing and decline populated-cache coverage.

Record every reconstructed primal/dual/reduced-cost vector with actual basis and
nonbasic values. Independent exact offline RHS/dual/cost reconstruction plus fixed
64eps scaled residual bounds must bind outputs, including nonzero structural
RHS/costs. Fixed row bounds do not make the slack-basis point feasible; do not
assert feasibility/status/optimality. Direct solves use the actual retained
matrix, especially after failure when workspace.basis differs from the live factor.
Record immutable input/state/model/options/policy/shared-start/event/kernel bits,
native symbolic/numeric ownership decisions, failure state and aliases before
post-failure solves. Bounded snapshots, serialize outside operation windows;
instrumentation is not neutral. No timers interpreted as speedup.

## Guard and acceptance

Separate host absence before new driver edits and before launch: previousrunner
5238/start202699/group5234 andchild5239/start202780/group5239, boot/start/command,
all group members and any Julia. One guarded Julia/BLAS1 process,heap2GiB/VM8GiB,
RAM>=6GiB/swap<=1GiB/wall600s. Pin current source/test/runtime/env/inputs/options/
clones/driver/launcher/native libraries/user hashes. No big/largo/AnyMOD oraliases.
No pinned source edits during run. Unexpected failure preservesraw/exit/source and
STOP; second side can remain UNEXECUTED. No retry or weakened oracle without a
new bounded amendment. Count preforward attempts including throws. Verify process,
exit, full independent pins, actual source/frozen clone binding, raw/portable and
exact offline audits. Fresh independent numerical/work/memory review before any
production/permanent-test plan. No fullsuite/CI/oldcost/corpus/reference reruns.
Remaining control/empty/nonfinite/dimension/precision/native-memory/performance
obligations and all prior rejections unchanged; no production promotion here.
