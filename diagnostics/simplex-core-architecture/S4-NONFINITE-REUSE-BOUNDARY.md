# S4-K: nonfinite same-pattern HH refactor boundary

Four new independent native Float64/Int64 HH factors and attempted refactors:
+Inf reference/candidate, quiet-NaN reference/candidate, in that order. Runtime
49/49checks, exit0;26audit gates551launchpins and9independent author checks pass.
No production/test/master/CI edit. Native HH symbolic reuse remains disabled.

## Frozen oracle and actual outcomes

J's deferred residual-formula clarification was resolved before launch in
exact-inputs.json, not after inspecting outputs. B0=[4 1;1 3],rhs=[1,2], exact
solution[1/11,7/11] for both orientations. Bound is

`||M*z-b||inf <= 64*2^-52*max(1, ||M||inf*||z||inf, ||b||inf)`.

Runtime evaluates the same formula in Float64; offline audit and independent check
use exact rational interpretations of captured finite binary64 outputs. All eight
residuals are NONZERO and pass; no exact-solve claim. Nonfinite targets are checked
as binary64 bits only:7ff0000000000000 and7ff8000000000000 in first CSC value, same
colptr[1,3,5]/rowval[1,2,1,2]; no NaN/Inf rationalization or extra numerical oracle.

All four attempts throw SingularException with native status1. Candidate retains
old symbolic owner, reference rebuilds; all four numeric wrappers change. These are
observed identities, not proof of arbitrary controls or native internal arithmetic.
Both routes discard HH's native workspace reference, while owned extracted base,
empty history, prepared values/identities and pools remain unchanged before later
retained-B0 forward/transpose solves. Disposable native/work/auxiliary/extraction
scratch is outside the preserved-state contract; native CSC holds target bits after
failure. No native rollback or populated-history/prepared-valid qualification here.
G provides the earlier nonempty-history qualification; no generic lifecycle rerun.

Native controls remain bit-identical across cases and before/after calls; default
IRSTEP0/q=nothing route only. Caller B0 and target values/indices are preserved;
input arrays do not alias native/extracted storage. This is a narrow two-value,
one-coordinate,one-pattern result. It is not general nonfinite rejection, public
model behavior, arbitrary-control compatibility or production enablement.

## Work, memory and provenance

Actual pre-entry counts4constructors/4refactorattempts/8HHsolves(4F4B), no copies,
updates, workspaces, public solves, observers, quality/certification calls or retries.
Eight native construction/refactor entry attempts are SOURCE-DERIVED. Plan bounds
are4initial numeric constructions plus UPTO4target numeric calls;4initial successful
extractions plus UPTO4target extractions;UPTO8internal orientation solves total.
These hidden calls are not instrumented. Observed SingularException/status1 and
new numeric wrappers agree with wrapper failure before HH target extraction, but
status alone is not presented as a captured internal stage.

New exact-source clone inverses to current production slice: only three routing
names and Float64 lu! reuse keyword differ. No method overwrite or finite guard.
One owned pre/post factor snapshot per case (eight total); assertions reuse them.
Input/native/control/solve records are additional bounded diagnostic copies.
Held old native owners enable identity checks and prevent interpreting this as a
native-retention benchmark. No production work/memory added; hypothetical pattern
comparison remains O(m+nnz(B)) on refactor. No speedup/allocation claim or benchmark.

Guard:one Julia/BLAS1,heap2GiB,VM8GiB,availableRAM>=6GiB,swap<=1GiB,wall600s.
Four resource samples within limits. Runner12359/start500785/group12358 and
child12360/start500867/group12360 are absent with full groups/noJulia, boot
dade7243-9103-4398-bb45-fa28fbc0be72. Actual source/runtime/native loader path and
13library files pinned; not every possible dynamic loader choice is qualified.
Postexit Python auditor is separately hashed, NOT one of551launchpins. Author
full551rehash, raw/portable4, user6/source/test/CI/master checks separate from review.
Raw SHA256:cd2d0000c898a64908707f4d0ec4de65ada2c654eda27922103faa7d314f313c.

Fresh gpt-6-astra/high review accepts this scope with no Critical/Important/Minor
findings and no unnecessary production work/memory. Reviewer16pin samples/raw4/
all8exact residual recalculation; authorfull551 separately. See review report. Broader S4/S6, other consumers,
scalars/platforms/fullsuite and representative cost/native retention remain open.
Do not rerun frozen K driver/clone/auditor/independent check or accepted old evidence.
