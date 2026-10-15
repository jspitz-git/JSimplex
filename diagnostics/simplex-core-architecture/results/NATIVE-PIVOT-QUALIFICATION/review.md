# Independent Task2 offline preparation review

Decision: NOT ACCEPTED. One blocking source compatibility finding, R1, remains.
Scope is **offline preparation** only. No Julia query, parser, import, compilation,
solver, driver, guard.run, seal, launcher, historical script or historical auditor
was executed. No source overlay, reservation or numerical result was created.
The 842 preparation pins match current bytes; review.json binds exactly those
842 paths plus preparation-pins.json (843 bindings).

## R1 — Replace the removed Test stack API before admitting either test stage

Priority P1. File: test-driver.jl:34 and :53.
The pinned Julia 1.13 Test source contains neither `push_testset` nor
`pop_testset` in any Test/src/*.jl file. It implements CURRENT_TESTSET and
TESTSET_DEPTH as ScopedValues and provides `Test.@with_testset` instead
(Test/src/Test.jl:2117–2137). Nevertheless, the driver calls
`Test.push_testset(root)` before its try block and `Test.pop_testset()` at the
start of finally. RED and GREEN therefore cannot run their selected bodies or
emit the promised raw.toml on this runtime: the first missing binding aborts
before error capture. The guard/auditor would correctly reject the attempt, but
would consume its sole allowance without testing the missing-policy contract.

Use the pinned Test API to establish the root's dynamic scope around both
includes while keeping raw serialization in an outer finally. Remove both
unavailable calls; preserve inherited Capture testsets, the original tests,
counts and expected RED exit. Verify the corrected source offline against the
pinned Test implementation before creating any exact-stage admission. The
existing Capture record/finish methods and inherited child-testset type otherwise
match the pinned Test extension interface. This finding is established by source
inspection, not a Julia execution or historical runtime reproduction.

## Reviewed source and integrity

Read the accepted Task2 plan/spec, ADMISSION, WORK-LEDGER, REPORT and every new
Python/Julia executable. Independently verified all 842 preparation hashes,
entry/preparation bindings, the 73-file reference and 75-file candidate manifests,
all seven whole-source inverses, both full observed-test inverses, and exact
assembly of five original neighbor testsets plus their original helper. Candidate
test bodies, loops, assertions and original @inferred calls remain present.
Candidate tests add only call-site observation and helper equation capture.
The 44 saved C records are bound to their original files and output tokens;
four fixture JSON/TOML tables and the 88-window alternating schedule match.
Historical evidence was read/bound as input; no old run or auditor was repeated.

The appended option symbol survives the six reconstruction/copy paths, including
Float64/BigFloat round trips. Managed Float64 factories select an immutable enum;
other supported precisions retain their original backend route. Nondefault
Markowitz/HH selection rejects before factorization. Copy shares only the active
factor, drops the copied spare, and carries policy without control mutation.
Populated-spare copies and both failure branches retain saved factors, control
identity/value, history and subsequent F/B checks. Repeated empty and resized
states preserve selection. Four raw auxiliary dual-simplex LU safeguards remain
byte-identical and outside policy scope. Public recovery remains Task3.

The observed wrappers return the direct `f(args...; kwargs...)` result rather
than retrieving it from the Any-valued event dictionary. They have specialized
forwarding call sites and rethrow failures. No definite additional source-level
inference defect was identified. Inference and Julia syntax/dispatch remain
unexecuted: unchanged @inferred neighbors must actually pass the future GREEN,
and their failures must never be weakened to accommodate instrumentation.

## Independent budgets

Source loop/helper derivation, separately compared with budget.json:

- Options: 48 combinations × 6 copies × 17 fields + 34 round-trip fields + 12
  rejection assertions + 4 other assertions = 4946.
- Backend ownership: 2 × 15 + 4 legacy-wrapper assertions + 1 invalid symbol = 35.
- Lifecycle: 8 manager/policy pairs × (61 first/reset + 41 copy + 2 × 47 failure)
  = 1568. Precision/factory: 160 + 36 + 48 + 1 = 245.
- Five neighbors: 25 + 4 + 4 + 19 + 12 = 64. Total 6858 assertions.
- Candidate PRE-forward entries total 722; neighbors 70; total 792, including
  rejected constructors, 16 singular manager refactors, hypersparse rejects and
  singular sparse-view attempts. Every per-entry total matches budget.json.
- Helper equations: 8 × 19 × 2 lifecycle equations + 10 × 2 factory equations =
  324, including 32 empty and 292 nonempty exact residuals. Option-only tests add
  no factor work. There are no public-solve calls in these stages.
- Cost: 4 fixtures × 2 policies × 11 rounds = 88 constructions/windows,
  176 refactors and 88 × 16 × 3 = 4224 solves (2816 F/DSE, 1408 B).
  Each window starts without a spare, first refactor constructs fresh, and
  second refactor uses private lu!: 176 fresh native LU + 88 lu! entries.

These are call-site/native-entry source counts, not a complete import/native
internal operation trace or evidence of executed assertions.

## Stage gates, guard and exact analysis

Preparation, exact-stage admission and result review have separate scopes and
exact manifest membership. Seal is write-once and nonnumerical; launch consumes
one reservation; each successor requires its predecessor's passing audit and
independent accepted result review. Reference/candidate stage bytes and loaded
paths are checked. Loader uses the pinned wrapper/executable, existing compiled
modules, disabled startup/automatic precompile, and the workload preference plus
PrecompileTools verbose check. Existing cache/import work is explicitly not a
complete cache-confinement proof and stays inside the inclusive stage cap.

Reviewed full groups/sessions coverage from the 208-group baseline and newly
created groups, boot/start/command linkage, pidfd ownership checks, guard versus
supervisor deadline offsets, process cleanup, single-thread settings, 8 GiB VM,
2 GiB heap hint and RAM/swap predicates. Supervisor is byte-identical to the
accepted source; guard changes exactly expected-exit handling and its CLI option.
Failures and absent raw output fail closed. No retry/automatic stage advancement
is introduced. Runtime host freshness must still be checked at exact admission.

The exact oracle uses binary64 tokens and rational arithmetic with the unchanged
128*n*2^-52 bound, including transpose matrix infinity norm. All P residuals must
pass; C failures remain recorded. Saved C mismatches are visible and require
explanation during independent result review. Every measured compile/recompile
field must be zero, all GC/outliers survive, and eight paired ratios plus
median/MAD/range are computed for each fixture/region. The enclosing total is a
superset, not a sixth additive component. Actual controls, strategy and final
fill/native Info/graph snapshots are retained. AUTO/SYMMETRIC limitations remain
explicit; no universal full-partial-pivot or old-binary overhead claim is made.

The independent reviewer-check.py ran once: 13 checks true, 16 malformed synthetic
evidence cases refused, and R1 confirmed from the pinned Test source. Synthetic
GREEN/cost acceptance was only a validator-schema exercise on invented identity
systems, not an execution/replay of selected numerical tests. It also verified
that a default residual failure/C mismatch remains diagnostic while a selected
policy residual failure is rejected. reviewer-check.json preserves this result.

## Computational work and memory

No unnecessary NEW production computational work, allocation or retention was
found. Task2 changes no production code; the seven Task1 candidate files remain
unchanged. Their extra Symbol/enum metadata and setup/reconstruction selection
are constant sized. Default fresh LU remains literal lu(B); threshold-one obtains
private defaults, sets two slots and makes one LU call. No added per-iteration,
per-candidate, F/B/update scan, solve, conversion, cache, control rewrite or
retained factor owner appears. Existing O(n+nnz) spare-pattern work and update
chain algorithms remain. Metadata padding/allocations and pivot-induced fill
cost are unmeasured, and no speedup or universal zero-overhead claim follows.

Diagnostic overhead is real and bounded: GREEN reserves 2048 event slots and 400
equation slots, fills 792/324, creates small dictionaries/control/output tokens,
and copies tiny equation inputs outside production kernels. Records hold owner
IDs, not factors; simultaneous ownership is also checked by original assertions.
Cost reserves 2,162,688 output payload bytes plus 135,168 Info bytes = 2,297,856
numeric bytes before timing, with headers and fixed input/serialization overhead
additional. Each timed solve incurs a pre-forward scalar counter and four Info
stores in both arms; no added vector scan/copy or auxiliary solve is inside the
solve region. Production controls/CSC/workspace/private candidate allocation is
inside the appropriate measured regions. Eight final fill/graph snapshots are
outside timers. Old timed factor references are cleared between windows.

Native Info, Julia summarysize, GC counters and RSS measure different things;
none is treated as a native live-allocation/free ledger. Sparse/dense fixtures,
separate initialization/warm/measured regions and all eight matched samples are
specified, but timing/allocation/native-fill effects cannot be measured during
this expressly offline review. No runtime admission is granted.

## Additional publication source inspection

Read continue.py, continuation-text.md, closure.py and publication.py without
executing them. They remain outside the 842 frozen preparation pins and are not
launcher dependencies. Their hashes are separately recorded in reviewer-check.json
for later publication closure. Continuation requires accepted offline review;
closure checks current/preserved continuation mappings and fixed publication
names; publication checks staged membership/blobs and does not commit/push.
No additional actionable publication finding was identified. R1 prevents the
accepted-review prerequisite from being met, so no acceptance-based continuation,
seal or launch should proceed with this review.
