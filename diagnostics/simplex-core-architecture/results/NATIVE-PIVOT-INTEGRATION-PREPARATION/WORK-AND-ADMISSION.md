# Task3 integration preparation: work and admission boundary

This is OFFLINE candidate/test preparation, not numerical admission. The accepted
Task1 seven production replacements and its 75-file overlay remain byte-identical.
The new ordinary overlay adds only the focused integration test (76 files).
The eventual permanent test/runtests.jl copy adds two includes after options_tests;
its exact inverse preserves every original byte. It is NOT a selected full-suite
entry. No test, source or environment in the actual checkout changes.

## Selected execution, independently checkable oracles

The future focused run includes ONLY native_pivot_integration_tests.jl once.
It must not execute Task1 tests again just because their files are in the overlay.
Eight public_case calls in literal manager-major, policy-minor order:
PFI, Forrest–Tomlin, Suhl–Suhl, Bartels–Golub, each default then threshold_one.
Each constructs one fixed 3-row/2-column LP and calls public solve once. Objective
-3x1-2x2, x1+x2<=4, x1<=2, x2<=3, nonnegative columns; expected point[2,2],
objective-10 and OPTIMAL. Defaults for tolerances, numerical safeguards and all
unspecified options remain. Explicit time5/iterations100/refactor interval2,
native/legacy/dual/steepest_edge/presolve=false/scaling=off/partial=false.
The six assertions per case check status, point, objective, selection and input
value/owner preservation. They do not themselves prove internal policy routing;
that requires the future concrete source-bound observer described below.

One recovery_case uses the exact Float64 construction from basis_recovery_tests,
"Basis checkpoints own working data and preserve consumed work", with threshold_one.
One initialize_workspace, one explicit checkpoint_basis, one _recovery_trial;
no restore/publish call, extra solve, certificate or calibration. The result must
be non-nothing, private at manager/backend/native/control boundaries, retain policy
and control bits; live factor/control, selected arrays and checkpoint values remain.
The existing live refactor counter MUST advance by one. This is selected endpoint
preservation, not whole-workspace rollback, observer neutrality or native-free proof.
The source has 29 explicit recovery assertions plus five full 17-field option
comparisons (phase, remaining budget, auxiliary, BigFloat, Float64 round-trip).
Successful total: 8*6 + 29 + 5*17 = 162 Test assertions. Early failure may reduce
that count; future auditor must fail closed on missing cases, counts or raw data.

Meaningful mutation oracles: dropping a copied option is caught by full-field
checks; losing policy in the recovery factory is caught by the new private enum;
publishing before acceptance or sharing controls is caught by owner/value checks;
wrong solver output is caught by literal optimum. Dropping policy on a public
factory without affecting this easy LP's optimum is caught ONLY by the future
instrumented-stage control oracle, not by a claim that the endpoint distinguishes it.

## Work: fixed requests, conditional internals, future guard ceilings

| Boundary | Exact explicit requested entries | Internal accounting |
| --- | ---: | --- |
| public solve | 8 | Dynamic iterations/constructors/refactors/solves; no assumed trajectory |
| separate recovery initialize_workspace | 1 | One managed construction + ordinary recompute 1F/1B |
| explicit checkpoint_basis | 1 | Five owned vector containers, nine entries (m1,n1) |
| separate _recovery_trial | 1 | One new managed construction + recompute 1F/1B + one weight BTRAN |
| option-copy comparisons | 5 | Six copy-function calls because precision round-trip uses two; no solves |
| callbacks installed by tests | 0 | Recovery's explicit false stop function only; driver probes are separate |

Successful selected recovery source total: two fresh managed constructions,
2F/3B, no manager refactorize!, copy_basis_factorization or replace_column! call.
Weight reconstruction explicitly calls refine_basis_solve! even with native
solve_refinement=false, so up to THREE extra correction BTRAN are possible.
The new driver must record actual attempts: 2F and 3..6B is the source-level range,
not a claim that all paths execute or a license for a numerical retry. Successful
non-nothing trial additionally performs both quality checks after recompute and
weight quality/refinement. These scans/copies are original work, not new optimization.
Native internal LU work, raw auxiliary LU, import/JIT and library internals are
outside these selected backend counts. Public iteration_limit is NOT their cap.

Future diagnostic ceilings, proposed before outputs and to be implemented before
admission: per public case at most64 managed Float64 constructor attempts,
64 managed Float64 backend refactor attempts,4096 managed backend F entries and
4096 managed backend B entries. Recovery case ceilings2/0/2/6 respectively.
Whole selected maxima514 constructors,512 refactors,32770F and32774B.
These are fail-closed diagnostic limits, not expected exact observations, not
mathematical complete-controller bounds, and not native-internal call counts.
A cap breach fails and preserves the attempt; no suppression, raised cap, tuning
or automatic retry. Exact observed counts must be published per case, including
attempts that throw. Any source-path bypass must be classified before admission.
The independently reviewed next driver must bind these limits, or a separately
explained tighter source-supported limit, without changing fixtures or safeguards.

## Concrete observation seams, not yet an implemented observer

observer-seams.json supplies six invertible replacements in the accepted candidate
factorization.jl. They count managed Float64 construction/refactor attempts before
work and F/B backend attempts before ldiv!/empty copy. Both refactor returns,
including empty, and factory return call a completed observer. Apply the scoped
whole-refactor-return replacement first, then function-entry additions. Reverse
all six changes to obtain the whole original accepted candidate byte-for-byte.
No global method overwrite, nested module clone or permanent production hook.

The future driver MUST define Main.NativePivotIntegrationProbe before loading the
ordinary overlay; no stage or probe executable is created here. A fixed active
case id, expected enum, once-per-case expected 20 control bit tuple and fixed
counters suffice. At each successful constructor/refactor require the expected
enum and all20 bits, including pivot1/IRSTEP0 for threshold_one. Empty factors must
be explicitly classified, never dereferenced. Count successes separately from
attempts and record at least one nonempty successful construction per public case.
Record actual refactor coverage, zero allowed and explicitly reported; never add
pivots to manufacture coverage. Missing refactor coverage relies only on Task2's
separately qualified lifecycle, not on pin presence or inferred execution.
Expected controls must be built once outside the solver call, with only declared
slots changed; do not allocate a fresh control vector per callback. Count cold
observer scans (20 per nonempty successful construction/refactor) and tuple reads.
Do not retain native owners or arrays in a growing ledger. Tests/observer failure
must propagate as a nonnumerical failure, not be swallowed as ordinary recovery.

This seam counts only selected UMFPACK backend entries. Triangular managers may
apply extracted factors without entering these backend solve methods: admission
must name that scope, observe required manager entries separately if promising
manager counts, and never present these numbers as complete FTRAN/BTRAN work.
Raw auxiliary LU safeguards remain byte-identical and outside pivot-policy scope.

## Added cold memory and retained state

Per public case six input snapshots: one CSC matrix (three numeric/index
buffers:3+4+4 entries), objective2, row bounds3+3, column bounds2+2 =23 entries,
eight buffers; six copied objects. Eight cases =184 copied entries over time,
not necessarily simultaneously live. Original inputs, options, solver allocations
and Test result storage are additional. No duplicate public solve/certificate.
Recovery snapshots: eight live vectors15entries, five checkpoint vectors9entries,
one control-bits vector20entries =14 explicit copied vectors44entries. The actual
checkpoint itself adds five containers9entries; native trial scratch/factors and
quality buffers are original costs. Array owner tuples retain selected live and
trial graph references until the function returns; no native GC/free guarantee.
One literal [2,2] expected vector per public case and [0,0] recovery expected vector,
small option keyword tuples/comparisons/Test storage are additional cold work.
BigFloat option conversions allocate only three tolerance scalars per conversion;
no BigFloat factorization/solve. No benchmark needed for this cold test preparation.

## Reused coverage and remaining gates

Task2 corrected GREEN2:6977 assertions, real factory/lifecycle/copy/failure/precision
coverage and119 diagnostic serialization regressions. Cost:2112/2112 selected-policy
residual passes,176 preserved default DSE-FTRAN failures, two GC windows and all
cost outliers preserved. These are reused results, NOT executed in this step.
Existing basis_recovery_tests source documents failure/stop/observer assertions;
this preparation pins it as SOURCE ONLY and does not claim those blocks were run
by GREEN2. New public/recovery integration remains UNEXECUTED.

Next: separate OFFLINE concrete driver/probe/guard/auditor and exact command/input/
source/runtime manifest preparation, independent gpt-6-astra review. Then a fresh
216groups ANDsessions/boot/start_ticks/command/refs/noJulia preflight and exact-stage
review before ONE<=60s inclusive integration (Julia/BLAS1,heap2GiB,VM8GiB,RAM6GiB,
swap1GiB). Raw-before-aggregate, fail-closed absent/partial output, immutable attempt
reservation and all original outcomes retained. No automatic retry or full suite.
Standing short-run permission applies; this preparation is not exact admission.
Only accepted public result plus whole-candidate/integration review can open a
separate merge/focused-master stage. Direct prototypes and old cost2 stay frozen.
