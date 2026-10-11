# S3-A: support invalidation at accepted write boundaries

Two correctness defects were reproduced on unchanged production: an accepted
refinement into a view updated rho but kept its empty cached support, and an LP
witness projection copied a certified dual after a diagnostic observer populated
support for the new workspace's zero rho. Both caused subsequent sparse pricing
to omit actual nonzeros. Whole-Vector and no-metadata controls passed.

## Change and numerical scope

Keep the existing whole-Vector identity lookup body unchanged. Other AbstractVector
destinations invalidate every one of six borrowed buffers for which Base.mightalias
reports overlap. Witness projection invalidates probe.rho immediately before copy.
No arithmetic, tolerance, precision, callback order, certificate, policy default,
point publication or work-budget change. This repairs opt-in support correctness;
it is not completion of the broader sparse-pipeline optimization stage.

## Executed evidence

- boundary-red-1:27pass/5intended failures/0errors; view3 and observer2 stale
  support/pricing assertions. Dense corrected values and witness certificate pass.
- boundary-green-1: identical smoke32/32, normal compilation.
- boundary-matrix-1:1645/1645, normal compilation;250 combinations across all five
  supported precisions, all five public managers, native/Markowitz and five
  destination forms. Includes no-cache, rejected correction, model/private/RHS
  alias boundaries, all six buffers, original certification and observer provenance.
- boundary-focused-1:3214pass/0fail/3errors. The three errors were missing
  lp_recovery_fixture in the diagnostic driver's LP state group, not source failures.
  The completed groups include pipeline kernels, storage, edges, both algorithms,
  sparse/dense LPs, recovery, shared refinement, witness projection and LP limits.
- boundary-lp-state-1:70/70 after including lp_refinement_recovery_tests before
  lp_refinement_state_tests. Only this dependent group was repeated. Counts are
  per-run, not an invented unique total across overlapping files.
- boundary-cost-1: reporting-type error before output, no accepted measurement.
  Dict{String,Real} could not accept String labels. Changed only to Dict{String,Any}.
- boundary-cost-2:120 warm samples,48 interleaved whole-Vector pairs and24 separate
  view samples, each200000calls. Actual cache presence asserted before timing.
  Old body verified against the pinned RED source snapshot. Compile0/GC0 throughout.
- boundary-allocation-1:28 attribution rows distinguish generic/specialized call
  barriers and noop/real invalidation; normal exit, compilation0.

All completed attempts preserve final process reports and unchanged pins. Every
following numerical launch or pinned edit followed a separate host absence check.
Raw attempts remain in .superpowers/simplex-core-architecture/S3-A; portable logs,
process summaries, exact cost rows and allocation rows are in results/S3-A.

## Work, memory and timing limits

The ordinary whole-Vector path performs the same bounded identity search, with no
new scans, solves, copies or retained memory. All96 paired whole-Vector rows have
zero allocation bytes/events. Times include a common noinline call barrier and
are mixed by type; they do not establish a solver speedup or robust regression.
Median times below are milliseconds per200000calls (six samples per variant):

| Type | Fixture | Cache | Original | Current |
| --- | --- | --- | ---: | ---: |
| Float32 | sparse | False | 1.1874 | 1.3308 |
| Float32 | sparse | True | 1.6779 | 1.9975 |
| Float32 | dense | False | 1.1623 | 1.3431 |
| Float32 | dense | True | 1.6298 | 1.8779 |
| Float64 | sparse | False | 1.7841 | 1.1604 |
| Float64 | sparse | True | 2.2431 | 1.5837 |
| Float64 | dense | False | 1.7424 | 1.2390 |
| Float64 | dense | True | 2.2969 | 1.5866 |

Full min/max spreads are in boundary-cost-2-summary.json. Sparse512/dense64 setup
and compilation are outside timing; no numerical trajectory or iteration reduction
is used as evidence of kernel savings.

The view path performs at most six overlap checks when a cache exists; none without
one. It adds no retained storage or numerical traversal itself. A subsequent
consumer correctly rebuilds invalidated support with the existing O(buffer length)
scan (m or m+n), possibly for several conservatively overlapping buffers. That
additional scan relative to incorrect RED behavior is required for correctness.
There is no update-chain-dependent work in the invalidation helper.

Generic-barrier view samples allocate48B/1event per call. Attribution reproduced
exactly the same overhead for a noop, while an explicitly specialized noinline
barrier and direct specialized batches allocate0B/0events for200000calls, with and
without a cache, for Float32/64. A separate nonspecialized single-call measurement
with a cache reports864B/24events; it remains recorded as a calling-context limit.
Do not describe every possible view invocation as allocation-free, or attribute
generic-barrier allocation counts to the numerical leaf without this distinction.
No source change was made merely to improve this microbenchmark.

Witness projection adds at most the existing six-identity lookup per certified
candidate that successfully constructs a probe, including a probe later rejected
by final finite/recomputed checks. It does not add a basis solve, numerical scan,
copy, cache creation or retained workspace. The possible later support rebuild
is again necessary. No cold-path timing benchmark or whole-solver speedup claim
is warranted for that bounded lookup.

## Review and integration

Independent review accepted this narrow fix: no numerical blocker, unnecessary
work, allocation or retained-memory finding in the production change. It confirmed
the required support-rebuild cost and calling-context/timing limitations above.
Production cd91a1a was integrated as master d8ad4ec5651225a512d5f533f48ce7d8fc8f90cc.
Master integration passed1645/1645 normally,exit0/pins unchanged; host process
absence and user-file digests verified, then master pushed and remote checked.
Existing worktrees and local environments are preserved.
