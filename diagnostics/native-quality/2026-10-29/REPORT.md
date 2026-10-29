# Float32/Float64 solve-quality optimization

**Qualified integration: native SIMD finite validation, commit `c0fa748ffa61ccb7c1caaf248c40324f60bc737b`. No clean-suite pass is claimed.**

The user authorized short comparisons of two native possibilities, followed by autonomous integration of accepted variants with independent review. Only A (SIMD finite validation) is integrated. B (local ordinary CSC BTRAN integer term counter) and AB are rejected because of short sparse regressions; no selective B tuning was added. Previously excluded717 multiprecision optimizations and allocation-test changes remain excluded.

## Whole-function comparison

See [MEASUREMENT.md](MEASUREMENT.md), [summary.json](summary.json), and raw [measurement-1.toml](measurement-1.toml). One guarded process completed in14.08s inclusive (including compilation; not a kernel benchmark).72fixtures cover Float32/64, n16/128/384, CSCapproximately3/15entries percolumn and dense matrices, FTRAN/BTRAN quality, finite correct/incorrect solutions. All recorded quality/scratch/input equivalence checks passed, including6434 edge checks. Warmup and fixture setup are separate; measured compilation/recompilation/GC are zero.

A sparse category median ratios are0.810/0.864 and0.826/0.914 for Float32 FTRAN/BTRAN,0.851/0.885 and0.864/0.933 for Float64. Per-fixture medians span0.794–1.019; dense differences are near noise. This is a local whole-solve_quality! improvement, not faster basis-factor solves or end-to-end LP evidence. Single-process synthetic data and unmeasured invalid-tail latency limit generalization.

All864matched pair groups have exactly equal allocation bytes/events for original,A,B,AB. The timed batch wrapper records192–272bytes/3–5events; do not label these zero kernel allocations. No new owned data, views, cache or scratch preparation is required by A. Existing finite checks, arithmetic order, safeguards, alias rejection, tolerances, callbacks and generic/multiprecision fallback remain. Invalid native vectors are scanned to their end rather than short-circuited; this increases exceptional-path reads and is explicitly accepted.

## Ordinary verification and unresolved results

| Attempt | Outcome |
| --- | --- |
| Original-source new-helper RED |236pass,92missing-helper errors; expected absence, not an old numerical defect |
| Full candidate green-1 |wall_time1790s; INCOMPLETE, not passing |
| Full candidate green-2 |author stopped536.55s after independent scope correction; INCOMPLETE |
| Complete19-file candidate |54014pass,2fail/54016; exit1 |
| Unchanged235 two complete legacy files |16325pass,1fail/16326; exit1 |
| Complete19-file actual master |54014pass,2fail/54016; exit1 |

All native numerical, recovery, phase-one, public solver, exceptional-range/FTZ and ownership checks completed successfully on candidate and actual master, including328new permanent checks. See [FOCUSED-VERIFICATION.md](FOCUSED-VERIFICATION.md) for scope ruling, [verification-final.json](verification-final.json) for exact outcomes, and frozen raw logs.

**Allocation qualification stays UNRESOLVED:** candidate failed Rational residual601/581 and dual709; baseline235 failed Rational outer602/581; master failed residual601/581 and outer602/581. The baseline did NOT reproduce the exact candidate failure cases. No retry fishing, gate edits, threshold relaxation, failure relabeling or old717 promotion was performed.

Independent source tracing found no timed execution path from these unchanged Rational LP-residual/dual-update kernels into the new helper; Rational solve_quality! also returns before the modified finite branch. This supports qualified acceptance of native A with unresolved unrelated allocation qualification, not proof of allocator mechanism, all-payload/native-memory identity, or clean full-suite status. All five failures remain verbatim in raw output.

## Publication and preservation

[REVIEW.md](REVIEW.md) records independent qualified approval of exactc0fa748f for publication/push. The production commit changes exactly src/simplex_numerics.jl, test/native_quality_finite_tests.jl and one test/runtests.jl include. No source B, environment/CI or old test changes were committed. User .vscode settings, local environment files and earlier worktrees/evidence remain preserved.

Measurement/RED old worktree source hash32e360... maps only to preserved original.jl after integration; baseline old master source maps there separately in master-binding.json. Master pins bind actual integrated source; no retroactive launch pins. Initial/intermediate prepared drivers remain unexecuted; canonical measurement uses driver-admitted.jl/A.jl/B-ready.jl/AB-ready.jl. Raw attempts, guard outputs, pins and reviews are retained and must not be rerun/rewritten.

PUBLICATION.json records the local staging/source inventory. Remote refs are checked separately after push; a later REMOTE-VERIFIED.json records that publication event, without retroactive launch pins. CI and HH reuse settings were not changed. The broader performance plan remains open.
