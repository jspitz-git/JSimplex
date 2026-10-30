# Production preparation: dual-recovery Devex fallback

**OFFLINE SOURCE PREPARATION ONLY.** This is the concrete production payload for the already accepted design/plan and qualified isolated candidate. No Julia executable, query, parser, import, compilation, numerical test or launcher ran. No production commit, actual src/test change, master integration or new numerical allowance is created. Independent source/work-memory review remains required.

The user requested production integration preparation with permanent tests and independent review, explicitly without Julia. We reuse the existing linked worktree on codex/native-quality-finite. The deliverable is an exact11-file prepared payload and apply-ready production.patch against master c0fa748ffa61ccb7c1caaf248c40324f60bc737b / diagnostic HEAD2d226b84e79e8afeff3ec8d8961b15af44b12085. Future actual production commit and integration/master verification remain separate.

## Production behavior and exact source

prepared/src/{simplex_numerics.jl,simplex_recovery.jl,simplex_pivot.jl} are complete byte-exact copies of the three source files used by accepted GREEN2 and both cost processes. They are not a revised numerical candidate. All other production files, workspace/scratch layouts, dependencies, env, precision, tolerances, arithmetic order, safeguards, cleanup and certification stay at baseline.

The ordinary refine_basis_solve! contract still returns SolveQuality. Its shared kernel specializes Val(false); a private Val(true) entry retains fixed-size cause/nonfinite provenance. Only an explicit actual dual transactional retry can propose the new fallback, and only Float32/Float64 maintained steepest-edge state with a finite inconclusive unchanged/not-improved/limit result, no nonfinite provenance and finite positive self-dot. Default/unspecified/primal/precision-transfer/feasibility-driver routes stay strict. No returned unreliable DSE norm is accepted as a weight.

The failed-row handling stops the DSE loop, retains charged work, rechecks actual scope after the existing stop, revalidates basis/primal/basic-price core, and resets the whole private Devex framework. Its pending result remains private until existing transactional publication. Existing observers see the proposed mode in unchanged order. Commit-only pricing_weight_rejected/pricing_devex records add no observer/logger callback. Stop/throw preserves live solver-owned payload under the stated ownership contract; diagnostics/consumed work and arbitrary callback mutations are not rolled back.

## Exact permanent test wiring

The patch adds five ordered includes immediately before the existing basis_recovery_tests.jl include. Removing precisely those five lines restores the entire original test/runtests.jl bytes. No old test file or assertion is edited.

1. test/refinement_outcome_tests.jl: the qualified outcome/provenance, nonfinite cleanup, stop/throw identity, alias/dimension guard and generic API smoke tests. Only its obsolete prospective-preparation comment changes.
2. test/refinement_reference_comparison_tests.jl: identical numeric/work/owner/event comparisons against the frozen legacy function. Only comment/include path/file name changes.
3. test/recovery_weight_tests.jl: identical reason/scope/norm/prefix rejection, owned state reset, fixed/auto/temporary modes and strict legacy comparisons. Only comments and helper include path change.
4. test/recovery_devex_fallback_tests.jl: identical actual-algorithm forwarding, private constructor/publication, late callback invalidation, stop/exception/no-publication and strict primal/legacy/generic route controls. Only comments change.
5. test/recovery_devex_pivot_tests.jl: adapts the qualified endpoint into ordinary permanent Test for both Float32/Float64. It retains the actual Devex update/pivot, original primal/optimality certificates, bad witness/row/basis rejection and all23 original assertion sites. Profiling @timed wrappers, timing-result accesses, output dictionaries, summarysize, ENV/path/TOML serialization are removed. One additional assertion directly carries the former raw-record auditor's core1F3B/final2F4B oracle. There are24 explicit sites per type (48 prospective assertions), not an executed result.

Two test-only helpers under test/support are byte-exact legacy refinement and strict weight-loop references. They have no production include/export/call path and use current unchanged numerical helpers; they are not a whole solver clone or method overwrite. All added factor dispatch is on declared private test types after genuine delegated solves. Existing six cold Base.invokelatest test entry barriers remain, preserving the qualified loading boundary. Ordinary Test is used; there is no custom recorder/manual Test stack.

The endpoint keeps one tiny workspace fixture, one genuine private recovery construction, one component clone and two actual dual_iteration! entries per type. It retains all original validation/certificate calls. Removing timing/serialization adds no solve, factorization, model or extra case; the final work check reads existing fixed counters. This is source-derived call budgeting, not a new runtime count. Existing diagnostics in the fixtures remain unchanged. All other four prepared test bodies, loops, options and assertions exactly replay the qualified originals after listed comment/path transforms. These tests add cold test-suite work and bounded owned snapshots/reference helpers; they add no production per-iteration ledger or persistent state.

## Work and memory review basis

| Frequency | Required work/storage | Evidence and limits |
|---|---|---|
| Ordinary refinement | Scalar result-mode plumbing; original dimension/alias guards, assembly, RHS copy, finite/residual/refinement checks | Exact qualified3-file source; both8-case normal-API measurements. No extra full scan, solve, mutable sink or retained array. |
| Eligible failed weight | Fixed-size outcome/reason and one original finite-positive self-dot | No second finite-direction scan. Retain k attempted rows and correction solves; never claim they were avoided. |
| One fallback | Existing core revalidation: O(N+nnzA) RHS and O(N+m+nnzB) basis/quality work; O(N+m) framework reset/pool retirement | Required correctness after callbacks; no additional basis solve/factorization at revalidation. Bounded scratch allocations are real. |
| Cold constructor/publication | One genuine factor factory in existing charge/finally boundary, private fixed-size result, two commit-only records | No Any field, persistent vector or new callback/logger. Missing auto state may create one existing PricingState. |
| Later iterations | Existing Devex maintenance and potentially changed pivots/refactors | No end-to-end trajectory speedup promise. |
| Permanent tests | Same four qualified test modules and two tiny endpoint cases, frozen test-only references, bounded snapshots/counters | Removed profiling/serialization/graph scans; no growing numerical recorder or extra endpoint solve. New assembled tests remain UNEXECUTED. |

N=m+n. Existing weight rebuild cost and all retained numerical safeguards remain as in the accepted design. Generic precision smoke tests remain; fallback scope stays exactly Float32/Float64. Cached storage does not imply zero validation/assembly work.

Accepted GREEN2 was5774/5774 with source-matched ordinary regressions and an actual post-fallback certified Devex pivot. Reference/candidate normal-API costs each passed272/272, eight cases, three warm/seven measured calls,80 whole entries/40 correctionBTRAN/40 stop/eightGCs. All56 measured windows per side have zero bytes/events/compile/recompile/GC. Fixture graphs match each pair. Timings are mixed; no speedup conclusion follows. Candidate whole-process peak RSS was8064KiB higher, including startup/compilation/setup; equal fixture graphs are not unchanged native/process-memory proof. Recovery-only revalidation/reset costs were recorded separately in GREEN2 and lie outside normal-API timing.

No new performance rerun is needed for byte-identical production source in this no-Julia preparation. The assembled permanent files and new include layout still require ordinary integration/regression execution under their own accepted concrete conditions. Prior success is not retroactively relabeled a run of this new layout.

## Offline evidence and preservation

Fresh host preflight confirmed boot781795f4-f7af-4c3b-9ce9-45c7cae76ecb, complete742 prior/current groups ANDsessions absent, no Julia, actual old boot/start_ticks/commands retired, local/remote refs and resources safe. host.json stores exact details; this is not a future launch preflight. Existing untracked Manifest.toml/LocalPreferences.toml and other worktrees are preserved. SSH transport previously failed; this preparation only uses existing gh HTTPS credentials via process-local options, without stored-config changes.

The payload manifest records all11names/SHA hashes, four exact before files, copies, six explicit full-file transform replays and five include positions. production.patch exactly reconstructs these files and a direct git apply --check returned0 without applying it. Initial source-check has22/23 true checks; one selector incorrectly counted @testset as @test. Its original source/false JSON remain preserved. A separate six-check source-check-endpoint corrects only the selector, proves23 original assertions+one work oracle and all353 original bindings unchanged. No candidate/test change or Julia rerun resulted. This is not an erased failure or a retroactive23/23 pass.

All264 reference/candidate diagnostic publication files still match actual committed blobs; both runtime trees retain exact accepted closed membership. No old checker/auditor/launcher main or accepted Julia driver was rerun. Raw/failures/reviews/old plans and their mappings stay frozen. The original plan remains an immutable historical plan; this document records the current production-preparation scope.

## Next gate (not performed)

After accepted independent source review/publication, prepare the actual production commit from exactly production.patch/payload on the unchanged baseline. Then prepare fresh ordinary focused integration and unchanged regressions, with concrete load paths, full required fixture availability, fresh host identities/resources/refs, admitted source hashes and explicit time/accounting. Candidate/post-fallback cost measurements are already consumed and are not rerun or tuned here. Existing shared Task4 numerical use is1108.3747013349202/1800s, with691.6252986650798s remaining; this is neither a new1800s allowance nor an automatic production verification launch.

The future focused entry should include these five permanent tests in their listed order, then unchanged simplex_numerics_tests, basis_recovery_tests, dual_weight_validation_tests, adaptive_pricing_tests before adaptive_pricing_lifecycle_tests, partial_pricing_tests and partial_pricing_edge_tests. Both existing fixture files test/fixtures/solver/netlib/adlittle.mps and test/fixtures/solver/generated/wide-bound129.mps must be available at the actual load paths. Keep ordinary Test, no diagnostic recorder or manual stack. New prepared tests have no MPS/ENV/output dependency. Future master verification and push require their separate prepared review/verification steps. CI remains off and HH reuse disabled.
