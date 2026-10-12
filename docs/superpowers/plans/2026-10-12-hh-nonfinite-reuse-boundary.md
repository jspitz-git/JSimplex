# S4-K: bounded nonfinite same-pattern HH refactor boundary

NEW diagnostic qualification after accepted S4-J review. No production/test changes
or old driver/auditor rerun. This is not a public-model input test: LinearProblem
rejects nonfinite coefficients before this internal factor boundary. No workspace,
public solve, pivot/update/copy, observer, extra quality/certificate/recovery calls.

## Fixed four cases and strict stop

Order: +Inf reference, +Inf candidate, quiet-NaN reference, quiet-NaN candidate.
Each is an independent fresh Float64/Int64 native HH factor of
B0=[4 1;1 3], canonical CSC colptr[1,3,5],rowval[1,2,1,2],nzval[4,1,1,3].
One target per factor has identical shape/indices and nzval[v,1,1,3], v bit pattern
7ff0000000000000 or7ff8000000000000. Precreate exact bits without floating arithmetic
on NaN. RHS for retained-old-factor solves is [1,2]. Inputs separately owned.

Reference calls actual refactorize!. Candidate calls a NEW exact source clone of
HH refactorize/backend/Float64lu!, only distinct routing names and the already
qualified pattern-guard keyword differ. Offline inverse-source equality mandatory;
no production method overwrite, no new finite guard, no control/tolerance/precision
change. Native defaults/q=nothing/IRSTEP0 preserved. No warmup or additional cases.

Per case: constructor once; capture old extracted base/history/prepared storage/
values/pools, native symbolic/numeric owners and controls; one attempted refactor.
Require a rejected attempt before publication, discarded f.refactor_workspace,
unchanged old extracted base/history/prepared values/identities/pools. Histories are
empty; this does not requalify G. Ignore disposable work/auxiliary/extraction scratch
for old-state equality, but record bounded post-failure metadata for failure scope.
Capture raw exception type/message and native status. Accept only SingularException,
_UnreliableBasisSolve, or ArgumentError with exact installed-wrapper message
"invalid matrix"; no blanket catch-all acceptance (BoundsError/UndefVar/OOM are
failures). Do not require identical status/class across sides; require both qualified
rejection and old-factor preservation, report any class/stage difference explicitly.

If exception/oracle/ownership differs unexpectedly or refactor returns, mark case
and whole gate FAILED, preserve raw/source/exit and STOP immediately. No solve with
the nonfinite target, no later case required, no retry/finite guard/oracle weakening.
A returning or different-error reference is evidence against this anticipated
rejection contract, not justification to silently change it.

After accepted failure snapshot, exactly one real FTRAN and one BTRAN on the
retained B0 with rhs[1,2]. Record output bits and independently audit exact rational
B0 residuals with fixed64eps scaled bounds. Never rationalize NaN/Inf inputs;
validate their exact binary64 bits. No component/reference solve, no native solve
on the failed backend, no retained factor update or copy.

## Full and bounded work accounting

If all cases qualify:4initialHH/4refactorattempts/8HHsolves(4F4B), zero copies or
updates/workspaces/public solves. Counters increment before all entries including
throws. Four initial native numeric constructions plus up to4target native numeric
kernel entries: a reference symbolic failure may occur before numeric, so do NOT
claim8observed numeric calls. Eight native construction/refactor entry attempts are
source-derived. Four initial successful extraction entries; up to4target extraction
entries if backend returned before extraction rejected. At most8internal orientation
solves, not an observed count. Do not claim failure stage from status alone.

Default control bits and original symbolic owners held only for identity, not memory
benchmark. Candidate guard result is true by actual shape/indices; native symbolic
should remain identical where wrapper reached reuse, but record rather than invent
whether an exception arose before a deeper native call. Numeric replacement is not
required if failure occurred before wrapper assignment. No copied growing ledgers;
one owned pre-failure and post-failure snapshot per case, reuse those for assertions
(no I-style repeated transient factorstate captures). Serialize after windows.

## Preflight, guard and acceptance

Read STATUS/ledger. Mandatory independent host absence: prior runner8770/start355367/
group8766, child8771/start355448/group8771, boot/start/command and full PGID members;
no Julia. Repeat separate host check before new Julia launch. One Julia/BLAS1,
heap2GiB/VM8GiB,availableRAM>=6GiB,swap<=1GiB,wall600s. No big/largo/AnyMOD or aliases.
Pin actual source/test/runtime/environment/driver/clones/plan/inputbits/library
loader/user files. Freeze inputs and exact B0 oracle before launch. Postexit auditor
is separately hashed, never relabelled a launch pin unless actually frozen then.
No pinned edits during execution. Verify process/exit, independent full pin hashes,
actual source/frozen clone, input/controls/options/global bits, raw/portable copies
and fresh numerical/work/memory review before acceptance or any later change plan.
Failure preserves original oracle and exit, no repeat. Native reuse remains disabled;
no fullsuite/CI, no speedup/native-retention/general-nonfinite/public-model claim.
