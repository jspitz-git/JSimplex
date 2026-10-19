# Fixed-GC GREEN: correctness and allocation result

One admitted `greengc300` attempt completed with exit 0, all 8,640 assertions and all three allocation nonincrease predicates passing. The saved auditor accepted this Task2 result. No retry or additional numerical process occurred. This is not Task3 timing/graph qualification or production promotion. Independent result review is recorded separately.

## Evidence and scope

The exact admission passed 7,513 checks and final fresh validation, with 2,420 primary and 10 evidence bindings. The initial independent checker failure concerned ordering of remote ref lines; the failed source/result and separate corrected exact ref-to-SHA mapping are preserved. No launcher, candidate or numerical gate changed. The successful RED predecessor remains bound; the earlier non-timeout failed red300 remains rejected.

The GREEN structural/differential/failure suites cover both source-defined backends and ownership/budget/hook boundaries. The allocation portion uses three native Float64 fixtures, ten alternating pairs each (three warm and seven observed), 60 windows, 1,440 saved outputs and 30 paired comparisons. All 42 observed windows have zero compile/recompile and zero in-window GC. Source paths, unchanged inputs, modes, paired outputs and residual gates passed. No world-age warning or test error/broken outcome was accepted.

## Allocation and observed time

| Fixture | Median events reference → candidate | Median bytes reference → candidate | Paired time ratio median | Faster pairs |
| --- | ---: | ---: | ---: | ---: |
| sparse32 | 1274 → 1263 | 295016 → 292424 | 1.057496 | 3/7 |
| dense32 | 1282 → 1263 | 755520 → 741912 | 1.032527 | 3/7 |
| sparse96 | 2513 → 2498 | 663544 → 657048 | 1.005935 | 3/7 |

Both allocation measures decreased at their medians in every fixture. The reference is packed DIRECT BG; GREEN candidate is the new specialized workspace. RED used the old workspace in a separate process, so cross-process differences are not an isolated compiler-materialization proof. No exact boxed allocation site was observed by this experiment.

All three recorded time_median_gate values are false and are preserved. Task2 accepts correctness and allocation, not those timing gates. These short noisy timings do not demonstrate a speedup. Complete Task3 eight-cell qualification (both backends, complete phase/graph/probe schedule and its separate admission) remains pending. No adjustment or sample exclusion is justified by these observations.

Recorded retained result bytes (reference/candidate) are sparse32 11,568/11,592, dense32 25,696/25,824, sparse96 32,208/32,344. These small increases remain visible; all three recorded memory gates pass. These selected retained-result measurements do not establish complete candidate peak/native memory or substitute for Task3 graph qualification.

## Preparation and process cost

Three GC preparation records have exactly 17 fields, with calls/completed both three and fixed positions after warm pair three before observed pair four. Each requested and returned a full GC. Individual expression wall times were 0.0938555, 0.0837898 and 0.080495 seconds; bytes/events were 1,152/72, 3,840/240 and 3,840/240. All preparation compile/recompile counters are zero, and each recorded one pause/full collection. These values are observations, not a requirement of exactly one actual collection.

The preparation measurement covers the GC expression. Helper-entry compilation, record construction and serialization are excluded from that inner measurement and remain in whole-process cost. GC is process-wide; heap/finalizer work is not fixture-bounded. GC/compile/wall counters overlap and must not be added or subtracted to claim savings. No generic compilation cure, finalizer drain or native-free proof follows.

Guard elapsed 29.66082003599149 seconds; supervisor elapsed 30.37684423600149 seconds; outer elapsed including immutable pre/post checks 51.04771555701154 seconds. Limit 300 seconds, inner guard 292. These nested/inclusive scopes are not benchmark speedups. Twenty-nine resource samples had minimum available RAM 21,953,920 KiB and maximum swap usage zero. External post-return closure found all 265 prior/new PGIDs AND SIDs absent and no Julia.

## Work, ownership and preservation

No production code, actual tests, environment, CI, master, candidate or accepted driver changed. The candidate source transformation retains arithmetic, safeguards, storage policy, buffer-request order and owned state layouts; it changes helper specialization boundaries. The allocation portion retains source counts of 60 constructors, 120 refactors, 480 updates, 960 FTRAN and 480 BTRAN; structural suites and backend internals are additional. These are not complete observed native-entry counts. New postchecks and independent review read saved evidence outside Julia windows. Three process-wide GC requests and their diagnostic records have explicit costs above, with no new candidate retained fields or algorithmic scans.

The saved audit and author postcheck (12/12) were each executed once. Run/outer files, preparation artifacts and all historical failures remain frozen. Separate independent result review, closure and exact publication are required before this result is used as a subsequent-stage prerequisite. Master remains 26e2291745999f485a74f643298ca997d65c7205; current diagnostic base is 3a8b393bd8bef95ec2cd3ece52129ea6ed1f5944.
