# Baseline Recorded During Planning

Date: 2026-09-22. Production source: d93cfd3.
Worktree: /home/jspitz/JSimplex.jl/.worktrees/simplex-modernization.
Branch: feature/simplex-modernization. Julia: 1.13.0, aarch64 Linux.
Preparation added planning documents and this record only.

## Successful full production test-runner invocation

~~~bash
JULIA_DEPOT_PATH=/tmp/jsimplex-modernization-depot:/home/jspitz/.julia JULIA_PKG_OFFLINE=true julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/runtests.jl")' > /tmp/jsimplex-modernization-baseline.log 2>&1
~~~

Exit code: 0.

~~~text
Test Summary: |   Pass   Total     Time
JSimplex      | 224921  224921  7m48.1s
~~~

This result covers all of test/runtests.jl, including MOI tests, in the new
worktree before algorithm changes. The log under /tmp is a temporary local
artifact, not a persistent repository file. This is not a solver performance
measurement. Translating the plans does not constitute a new test run.

## Difference when using Pkg.test

Earlier invocation:

~~~bash
JULIA_DEPOT_PATH=/tmp/jsimplex-modernization-depot:/home/jspitz/.julia JULIA_PKG_OFFLINE=true julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'
~~~

It exited with code 1: 183,653 passed, 0 failed, 1 errored.
The tool truncated its extensive output, so the exact cause was not captured
reliably. Pkg.test cannot be described as fixed, nor can this be identified
as a proven launcher defect. The subsequent direct full-suite invocation
passed without source changes. No tests or tolerances were changed.

Before implementation, repeat Pkg.test with its entire output redirected to
a file, identify the first error, and commit any infrastructure fix separately.
This is a preparation gate, not an unverified numerical fix.

Pkg created a local Manifest.toml from available cache entries
(MathOptInterface 1.54.0, OrderedCollections 2.0.1); Project.toml content
was unchanged. The manifest is excluded from the planning commit.
The used manifest was copied to /tmp/jsimplex-modernization-baseline-Manifest.toml.
On resumption, restore that copy or instantiate the environment normally.
Temporary files do not guarantee long-term dependency availability.

## Work not measured during preparation

No new full solve of runtime.mps, medium.mps, or greenbea, performance
ablation, or development GLPK/JET/JuMP suite was run. Those evaluations belong
to F01 and later features. This record provides no evidence of algorithmic
speedup or improved numerical robustness.

## English-language and corpus revision

All documents prepared for this development branch are in English, as
requested for material intended for the remote repository. The algorithm
plan now uses /home/jspitz/NetLib, /home/jspitz/MIPLib, and /home/jspitz/mps.

Read-only inventory checks found 94 NetLib MPS files, 1,065 compressed MIPLib
MPS files, and 10 additional MPS files. Selected MIPLib gzip headers were read
successfully. The local filename corresponding to AnyMod.mps is AnyMOD.mps.
big.mps, largo.mps, and AnyMOD.mps are stress-only and excluded from complete
simplex solves. See the [test corpus plan](../../docs/superpowers/plans/2026-09-22-simplex-test-corpus.md)
for budgets, discovery, and selection rules.

## Plan checks

Check that F01–F25 each appear exactly once as detailed feature tasks,
relative links resolve, no placeholder sections remain, and whitespace is
clean. The specification and overview require a separate commit for each
verified feature, evidence before default rollout, and a shared recovery
budget. Corpus checks validate selected paths and preserve the explicit
oversized-model exclusions; they do not run a full simplex solve.
