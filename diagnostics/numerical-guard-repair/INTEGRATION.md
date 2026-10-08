# Numerical guard integration, 2026-10-08

The user authorized merging and pushing verified fixes immediately. This
integration applies original commits `2d98f3e` and `343e7ca` to master `eb758ab`
as `a148571` and `5619ab0`. Their source and test patches are unchanged.
The already integrated BG empty reset, CI preference, and postsolve box-hint
repair remain present. The separate certificate-reuse optimization `97f4969`
is excluded while numerical work has priority.

The integrated fixes refine ambiguous terminal row complementarity in native
precision, validate fresh dual transpose rows and perform transactional bounded
candidate reselection, and preserve the configured Markowitz backend in the
existing exceptional small-pivot refinement path. Tolerances and certification
requirements are not relaxed. Earlier results in README.md retain their original
source provenance; this file describes checks on the integrated combination.

`reproduce/integration_validation.py` runs focused checks with normal compilation,
semantic regressions with `--compile=min`, a full dual BG/native80 greenbea solve,
and a full dual HH/native160 runtime solve sequentially. It pins source digests
and uses the existing 8 GiB VM, 6 GiB available-RAM, 1 GiB swap guard with one
Julia/BLAS thread. The full solves check original primal feasibility and are
compared to retained reference objectives. These are correctness checks, not
paired performance benchmarks or a complete-project-suite claim.

Independent read-only review approved the unchanged patches, registration of
all four new test files, preservation of existing master fixes, and absence of
dependencies on the excluded performance change.

Open findings remain: pilotnov's later sensitive phase-II basis, primal degen3
loss of feasibility, and aged FT/SS factor accuracy including the historical
direct-SS runtime failure. These integrated fixes do not close those findings.

## Fresh results

All four sequential processes exited 0 with unchanged source digests:

- 1,850 focused numerical and allocation assertions passed with normal compilation.
- 15,688 semantic assertions passed with `--compile=min`.
- Full greenbea BG/native80: OPTIMAL, 3,640 iterations, originally feasible,
  objective -72,555,248.1298455, matching the retained reference. Diagnosed call
  time 37.879 s includes 36.468 s compilation.
- Full runtime HH/native160 dual: OPTIMAL, 55,034 iterations, originally feasible,
  objective 51,425,691.76209734, matching the reference within 1e-4 absolute.
  Solve time 192.224 s includes 0.046 s compilation.

`results/integration-validation.json` records process and solve outcomes, source
and log hashes. `reproduce/audit_integration.py` verifies completion, unchanged
sources, exact assertion counts, original feasibility, input identity for
greenbea, and both objective comparisons. The runtime reproduction separately
asserts its input digest before solving. Full raw logs remain in
`.superpowers/numerical-guards-integration` in the integration worktree.

No complete CI pass is claimed; existing unrelated test failures remain open.
