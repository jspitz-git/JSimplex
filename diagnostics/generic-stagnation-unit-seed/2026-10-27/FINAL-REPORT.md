# Integrated stagnation and steepest initialization scalar savings

Production `3d3787b24c802043caf8a931b4d142b62c961940` normally pushed and remote-verified. Exactly four paths: two source files, an ordinary regression module and runtests inclusion. A adds only a concrete BigFloat metric specialization, reuses an already fresh private primal zero for comparisons and qualified free-price conditional magnitude. B adds BigFloat/RationalBigInt unit-basis predicates; BigFloat negative rounding retained by conditional magnitude followed by integer-one comparison. C adds only a BigFloat initializer, lazily checking shared row-weight cacheability once at its first original site after the first weight assignment. Initial returned zeros and row weights remain fresh per call; within-call original row sharing retained. Generic methods unchanged. No new scan, solve, copy, conversion or persistent numerical cache; O(1) private references/flags and cold method metadata. Objective/metric arithmetic order, all finite/context/history/callback/rebase checks, tolerances, precision/rounding, owners and exceptions retained. Independent production review found no unnecessary added work or retained numerical memory.

| Complete call | Median of cell paired time ratios | Median byte ratio | Median event ratio |
|---|---:|---:|---:|
| Whole stagnation metrics | 0.9546 | 0.9386 | 0.9455 |
| Whole primal observation | 0.9656 | 0.9575 | 0.9636 |
| Whole dual observation | 0.9675 | 0.9573 | 0.9637 |
| Whole BigFloat unit gate | 0.4233 | 0.3750 | 0.3750 |
| Whole RationalBigInt unit gate | 0.2857 | 0.0000 | 0.0000 |
| Whole initialization B | 0.9673 | 0.9631 | 0.9608 |
| Whole initialization C | 0.9169 | 0.9004 | 0.9099 |
| Whole composed initialization | 0.8660 | 0.8415 | 0.8501 |

Accepted comparison: 105921 ordinary checks,3415cells/61470windows,74.538s inclusive launch. BF64/128/256 x five rounding modes; sparse/dense monitor N32/128,m8/32, gate/init N8/32,m8/32. Native Float32/64 and RationalBigInt/Int64 controls. Three warm and nine alternating pairs; measured compile/recompilezero. All23GCwindows and slower/outlier cells retained. Fixture/seed/reset/cold/warm/validation/contextGC costs retained separately; import/init bounded inclusive only. BC composition measured directly. All intended event reductions retained; one A primal-observation pair has7856extra bytes despite96fewer events, allocator cause unknown. Unchanged native/exact controls also show byte variation. No universal/end-to-end speedup or native-live/free/retention proof. Unit/initializer component fixtures replace basis with structural unit columns after setup but perform no basis solves; not public-trajectory qualification. Thirteen runtime binaries are prospective readtime alias/target/hash pins, not full transitive loader/cache/import-init coverage.

Original GREEN rejected before tests: concrete method declared before SimplexWorkspace existed; separately reviewed byte-exact method relocation to simplex.jl after type definition, original stalling file restored, no candidate arithmetic/test changes. Original3.253s run and insufficient prelaunch reviews frozen.

Initial comparison104540PASS/19ERROR/exit1 rejected and frozen: diagnostic reset copied full seeds into intentionally shortened malformed arrays before the function under test. Separate reviewed keyword disables reset only for those already prepared malformed-array checks; all expected errors, candidate code and normal measured resets unchanged. Corrected comparison105921PASS, no failures/errors. No old attempt/auditor rerun.

RED30806PASS+5expected whole-call cost failures witnessed before production source stage. GREEN257423PASS/1856.548s and actualMASTER257423PASS/1842.283s, each45wholefiles. Five new fixed three-pair gates require fewer events in every pair and lower median bytes; no time assertion or GC filtering. Every previous test/threshold unchanged, including historical RationalBigInt3percent gate; no old exception reused. Ordinary Test only, no custom recorder/manual Test stack. A separate final stage removes only one trailing LF from simplex.jl (end

 to end
); accepted GREEN-2 numerical code/tests remain exact modulo that final whitespace, independently qualified without redundant GREEN. First commit preparation stopped failfast before commit on the EOF warning and is preserved. Fresh actualMASTER loads the clean final bytes with all45files/257423expectations. Exact source inverse, reviewed private-index commit, ff-only local integration and fresh actual-master acceptance precede normal nonforce push.

User files/env/unrelated indexes preserved. Current source/index/continuation old hashes map only to baseline/before-master/continuation-before exact bytes; all older maps/raw/rejections frozen. Full historical groups AND sessions checked using boot/start_ticks/command, exact unrelated WSL identity allowance retained, no PID-alone identity. CI off, automation paused, HH reuse disabled; broader/fullsuite/x64/native-retention/end-to-end OPEN. No automatic new experiment.
