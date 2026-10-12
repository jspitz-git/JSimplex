# S4-I: actual borrowed assembly and HH recompute qualification

Two new Float64/Int64 native HH workspace lifecycles completed55/55 runtime checks,
exit0. New exact offline audit29/29,655pins; independent author10checks including
full655rehash and four raw/portable matches. Production/test/CI/master0eb75c3
unchanged. Native HH reuse remains disabled. No old numerical driver/auditor rerun.

## Actual sequence and ownership

Actual initialize_workspace runs on each side; reference calls production
recompute, candidate calls distinct source clones. Inverse transformations recover
exact production slices: HH three routing names plus guarded Float64 reuse keyword;
recompute only its name and HH refactor routing. No production method overwrite.

A=[4 1 7 1 2;1 3 1 2 4], costs1:5, structural lower0/upperInf, fixed rows[1,2].
Native legacy/default controls and q path, time30/iter20/1e-7 tolerances unchanged.
NullLogger, observer absent, existing kernel timing enabled before actual setup.
No warmup/clock reset/precision or numerical-policy override.

Initial HH(-I) and mandatory1F1B produce setup; basis[1,2] recompute creates B1 and
one owned public matrix plus one saved HH copy. Explicit _basis_matrix! for
basis[3,2] rewrites the SAME borrowed arrays to B2 before refactor. LiveB1 forward
and savedB1 transpose remain valid, private native CSC still contains B1. After
B2 recompute, candidate preserves symbolic identity; reference rebuilds; both
replace numeric owners. Old owners held for identity checks, not retention proof.
Slacks[6,7] recompute shrink actual row/value vectors4->2 without replacing arrays.
No allocator/native-capacity bound follows. Public ownedB1 and original model
remain unchanged despite subsequent actual assembly writes.

Singular basis[4,5] throws SingularException/status1 on both sides. Factor native
workspace is discarded while extracted base/history/prepared identities and values
and saved factor remain unchanged before later direct solves. These histories and
pools are EMPTY: this does not repeat G's nonempty-history coverage. Failure leaves
workspace.basis[4,5], matching basic mask and singular borrowed CSC; old factor
still represents -I. This is deliberately NOT whole-workspace rollback. Failed
kernel is counted; success refactorization count/event/reconstruction are absent.
Only retained factors are used afterward, never inconsistent workspace continuation.

## Work and exact numerical audit

Actual entry counts2workspaces/8explicitrecomputes/2publicassemblies/
2explicitborrowedassemblies/2copies/12directsolves(6F6B). Source plus kernel counts
include2initialHH,2setuprecomputes,8implicitborrowedassemblies and16mandatory
reconstruction solves. Totals10borrowedassemblies/8refactorattempts/28HHsolves
(14F14B); initial spdiagm assembly is additional setup work. Each side records
4F4B4refactor kernels, successful workspace.refactorizations3/iterations0 and
exact events refactor_initial+3refactor_other. Reconstruction reduced-cost scans
are real work even though they are not timed pricing kernels.

Ten native numeric entries are SOURCE-DERIVED. Eight successful extraction entries
permit UPTO8additional native scaling-validation solves, not an observed count.
No updates, public solve, pivots, recovery, phase transfer, cleanup, quality,
certification or retry calls. Twelve other borrowed consumers remain excluded by
this sequence, not by assuming native policy disables them generally. Actual
pricing/hypersparse caches are absent; populated-cache behavior is not qualified.

Offline rational reconstruction binds12direct outputs and16internal reconstructed
primal/dual outputs to exact input/basis/RHS/cost state. All28fixed64eps-scaled
residual bounds pass;8direct and8reconstructed exact residuals are NONZERO. Eight
reduced-cost vectors also pass independently reconstructed fixed bounds. Initial
and final slack points are not feasible for fixed row bounds: no solver status or
optimality inference. Bound/option/policy bits, model ownership and unchanged
shared start are separately checked. Recorded side equality is not a universal
trajectory claim; no performance comparison is made.

## Resource, cost and scope

Seven resource samples: minimum available RAM22794948KiB, maximum swap0. One
Julia/BLAS1/heap2GiB/VM8GiB guarded process. Runner8770/start355367/group8766 and
child8771/start355448/group8771, bootdade7243-9103-4398-bb45-fa28fbc0be72; fullgroups
and Julia absent after exit. Loaded UMFPACK path/hash captured;13native-library
files pinned, not proof of all possible loader decisions. Raw SHA256
be5ba926ede9ac7a87fcf13132a2684171542a0df3cd7eb3b74d26b20270e8d9.

No production computational work/allocation/retained-memory increase. Candidate
adds O(m+nnz(B))pattern comparisons at eligible refactor, preserving native copies,
numeric work, extraction and reconstruction. Diagnostic14workspace snapshots,
8factor snapshots around failure,2saved-base captures and12direct records are
bounded; serializing occurs after windows. Observation overhead and held native
owners preclude native-memory or speed claims. No production enablement before
remaining controls/empty/nonfinite/dimension/scalar/other-consumer and representative
cost/native-retention obligations. Fullsuite/x64/historicalCIcause and existing
rejections remain unchanged. Plan/source/driver/auditor now pinned; do not rerun.
