# Numerical guard repairs

Work starts from master `3807f50` on `codex/numerical-guard-repair`.
The historical findings are in `../numerical-guard-audit/README.md`. Numerical
repairs precede performance changes. No tolerances or candidate policies are
relaxed. Numerical jobs run sequentially with one Julia/BLAS thread, the existing
8 GiB VM / 6 GiB available RAM / 1 GiB swap guard, and preserved local preferences.

## Greenbea: ambiguous terminal row complementarity

The original BG/native80 dual legacy solve reproduces `NUMERICAL_ERROR` after
9,061 iterations. Its first terminal candidate is at iteration 3,350, before
postsolve. Primal feasibility passes, but row-activity variable 5203 fails the
independent original-objective complementarity check. Its negative price is
approximately -100 and its upper bound is 50; the coarse activity enclosure is
[49.99999995562166, 50.00000010464976]. The upper endpoint lies just beyond the
absolute primal tolerance 1e-7. Three native dual corrections, or a fresh LU dual
solve, do not resolve this row-activity uncertainty; after the first correction
the basic stationarity error already falls below 1e-12.

The repair batches only unresolved, nonstationary Float32/Float64 row activities
and checks their distance to the bound selected by the certified price sign.
Passing that same bound as both lower and upper targets preserves absolute
complementarity, rather than merely accepting row feasibility. The existing
native compensated row filter is tried first; the existing bounded exact
fallback remains available for unresolved extreme arithmetic. Basic stationarity,
structural-variable checks, finite-bound checks, and both tolerances are unchanged.
No refinement storage is created when the ordinary certificate succeeds.

The repaired full solve returns OPTIMAL after 3,640 iterations, objective
-72555248.1298455, and independently verified original primal feasibility. This
matches the preserved HiGHS reference -72555248.12984599 for the identical input
SHA-256. The first 42 logged progress samples (excluding timestamps) are identical to the baseline;
the trajectory changes only after the formerly rejected terminal candidate.
The solve then completes postsolve cleanup, without an original-LP restart.
Peak process RSS is 2.198/2.203 GiB (baseline/repaired, including compilation).
Whole-call time is 38.04/37.50 s and compilation 34.67/35.88 s: these cold diagnosed
runs establish correctness, not a speedup.

The focused test initially fails all four optimal-witness assertions on the
baseline (Float32/Float64, lower/upper active bounds), while the feasibility and
negative controls pass. After repair these 28 checks pass. Four further negative
controls reverse the row price while preserving basic stationarity, so rejection
cannot be attributed to the basic-column check. The combined targeted numerical
and allocation suite passes 1,381 checks. Independent static review found no
blocker; its sign-test suggestion was incorporated. Broader semantic validation passes all 15,681 assertions; 100 unique external
combinations pass all 305 assertions, including original primal feasibility and
reference objectives. `results/external-audit.json` verifies completeness and
unchanged source throughout both guarded jobs. These are selected regressions,
not a claim that the entire project suite passes (known baseline failures remain).

Raw snapshots remain in `.superpowers/numerical-guard-repair/greenbea-baseline`
and `greenbea-repaired`. They contain candidate equations and values, not live LU
pointers. `results/greenbea-probe.toml` records the baseline candidate analysis. Reproduce its `certified=false` fields
against baseline `3807f50`; the probe calls the certificate in the loaded checkout,
so the repaired code should instead certify that same stored candidate.
The result files' `source_revision` is the base HEAD; the repaired run additionally
uses the uncommitted row-complementarity patch, whose source aggregate was recorded after the solve without further source changes
and is stored
in `results/final-validation-source.json` (Project.toml plus src/**/*.jl sorted by
relative path, each path followed by NUL and file bytes).

## Reproduction

Run all Julia scripts under the repository's existing memory guard and Julia
wrapper. `reproduce/capture.jl INPUT MANAGER BACKEND OUTDIR` uses native reading,
Float64, dual legacy steepest-edge, interval80, no partial pricing, integrality
relaxation, a 300 s solver budget, and terminal-only snapshots. Each output
directory must be fresh. `reproduce/probe_terminal.jl SNAPSHOT OUTPUT` separates
feasibility, stationarity, and row/column complementarity; its 256-bit selected
price dots are independent diagnostics, not production iteration arithmetic.
`reproduce/targeted.jl` runs the focused numerical and allocation regressions.
