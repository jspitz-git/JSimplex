# MA-U: offline BigFloat rounding guard preparation

The accepted MA-T Task1 is prepared as an isolated, UNEXECUTED diagnostic candidate.
The only candidate changes are `_dense_ma_rounding_matches()::Bool` and one call
replacing the original final rounding equality. Removing the exact helper and
restoring that expression reconstructs MA-R/candidate.jl byte-for-byte. All12MA
product sites, type/backend/shape/n16 checks, numerical operations, publication,
exceptions and pre-write whole fallback remain unchanged. This is not a runtime
or zero-allocation acceptance, and production/master remain untouched.

## Source and ownership

The helper reads `Core.current_scope()` each call, handles absent scope/key as true,
and compares the present typed MPFR value to live global ROUNDING_MODE[]. A local
call-site Base.@inline exposes the existing KeyValue.get return to the optimizer.
There is no direct HAMT clone, Some return, cached scope/mode, new task, stored
scratch, global/stdlib method overwrite, effect annotation or broad solve inline.
Equal explicit scoped/global modes stay eligible; mismatching modes retain the
original whole solve before destination mutation. Errors from invalid internal
state are not caught or retried. Serialized global MPFR changes remain assumed;
concurrent global writes are not made safe by this change.

At most one persistent lookup occurs per otherwise eligible-size backend entry,
including recovery/certification callers. Trie depth depends on active scoped
storage/hash traversal, not n/nnz/history. No new matrix/vector scan, solve, copy,
conversion, factorization or arithmetic precision increase is introduced. Source
HashState/tuple values may still allocate; compiler behavior is unqualified. Code
size/compilation growth from local inlining must be assessed in the later admission.
No unsupported Julia compatibility is claimed: the prototype requires exactly the
source bindings accepted by MA-T, verified before any future Julia load.

## Tests prepared, not executed

`guard-tests.jl` defines MARoundingGuardTests and has no top-level solve, task or
measurement. It reuses byte-identical local copies of MA-R reference, tests/helpers,
fixtures, diagnostic instrumented entries and license. Original qualification()
and old cost schedule are NOT invoked. The old eligibility oracle is normalized
back to the original body by undoing function-name and P.DenseLUBackend qualification.
Instrumented correctness still counts fallback and scratch entries separately;
future cost uses only uninstrumented code.

270predicate cases cover five public global modes ×six scoped states ×three
precisions ×three unrelated storage sizes.25transition records exercise nesting,
exception unwind, inherited Up/Down child tasks with yield and nested equal-mode
scopes, and consecutive serialized global changes. A third task reports whether
an actual no-scope context is available; if not, runtime coverage is explicitly
unavailable without mutating private task state. Up to one further record is made.
All three tasks are scheduled/joined on the successful path; global writes happen
only after the two inherited children complete. No production task is created.

840whole-call cases comprise720ordinary rounding-grid,80special,20small,4other-scalar
and16mixed-precision cases. Existing compare_case checks original/new/instrumented
outputs, exact finite values/precision/sign, NaN/Inf, factor/RHS/old scalar owners,
retained prior results, aliasing, exception type/message and post-unwind state.
Four retained-output cases repeat once:844entries per side,2532total explicit
backend entries.840bundle setups include4PFI constructors/4PFI copies; these are
additional setup/native work, not complete PREforward accounting. The full named
predicate count and diagnostic allocation/retention limits are in work-ledger.md.

The test functions do not implement cost windows, raw output, launcher or guards.
MA-V must seal exact calls/process assignment/loading/raw-before-assert failure
handling and anti-hoisting code checks before a separately accepted launch. The
planned2080cost backend calls and61440micro calls are neither run nor prepared as
a driver here. Runtime expected allocation RED remains future work; this turn's
two missing-helper source markers are only a Python textual RED.

## Offline evidence and corrections

Fresh entry15checks verifies local/remote refs, the accepted plan, isolated branch,
all166historical process groups ANDsessions/noJulia, source514and protected6files.
It preserves eight direct MA-T final-review/fix/closure/publication continuation
bindings in MA-U beforecopies. All earlier MA-T original-plan and older mappings
remain unchanged. Source checks19PASS/34readtimebindings confirm exact candidate
inverse, five copied files, original eligibility inverse, prospective counts and
unchanged installed source. No Julia query/parser/import/compile/runtime ran.

Author static review corrected one inaccurate comment about the old-oracle
qualification and moved qualification's return after normal @testset completion.
The original guard-tests bytes and source-red hash remain preserved; author-fix
records two textual conditions and four passing correction checks. This was not a
Julia parser/runtime failure. A guessed MA-S-LOAD/driver-reviewed.jl read failed;
its actual frozen driver.jl was then identified, without executing anything.

Independent review is recorded in results/MA-U/review.md/json. Its verdict concerns
source preparation only, never allocation/performance acceptance. All this step's
accepted source/evidence/scripts become frozen at publication. No older file was
rewritten or rerun. Initial MA-S-2 rejection48/52 and Rational control obligations
remain; no whole-candidate promotion, tolerance change or threshold waiver.

## Next boundary

Next is MA-V admission preparation only: immutable new driver/guard/raw schema,
exact tested source and full work budget, corrected outer world-age boundary,
anti-hoisting plan and independent numerical/work/memory admission review. Standing
human short-run permission persists, but this offline step does not start a run.
Only an accepted concrete MA-V admission may use the planned two serial90second
processes/180seconds total; no automatic retry or hours-long experiment.
CI stays off, HH reuse disabled, automation paused, broader plan OPEN.
