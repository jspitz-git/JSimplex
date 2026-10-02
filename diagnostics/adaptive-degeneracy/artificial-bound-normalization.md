# Exact nonbasic bounds at the artificial-removal boundary

Base: `3df48ec` on `codex/adaptive-degeneracy`.
This follows [native artificial-row recovery](artificial-row-recovery.md).

## Failure and isolated experiments

Fresh degen3 runs with the native and JuMP readers still stopped during
artificial removal. Observational instrumentation located the next rejection
at the existing `abs(artificial) <= primal_tolerance` prerequisite, before BTRAN.
Native reading had removed 22 of 25 basic artificials (iteration 2367), and
JuMP had removed three of four (iteration 2894).

The offending positive values were already present at auxiliary optimality:
approximately `1.1452136264e-7` and `2.6514584683e-7`, against tolerance `1e-7`.
The signed sums were approximately `-1.5852140882e-6` and `-1.3646734470e-6`.
Individually tolerated negative artificial values masked the positive value.
An auxiliary optimum within bound tolerances is therefore not sufficient to
establish that each artificial can be removed with a feasible exchange.

The following diagnostic alternatives were tested on private captures:

- Omitting the zero-artificial prerequisite selected a step that violated the
  entering variable's lower bound; the existing reconstruction checks rejected it.
- Inspecting other entering candidates, including independently validated native
  FTRAN corrections, found no admissible complete exchange. Best resulting bound
  violations were about `1.42e-7` (native) and `2.65e-7` (JuMP).
- Snapping only nonbasic artificials to zero broke full primal feasibility.
- Fixing artificials to zero, clearing the objective and selecting dual feasibility
  optimization worked, but took **zero dual pivots**. This motivated separating
  reconstruction from algorithm and objective changes.
- Snapping **all nonbasic variables** to their exact state bounds, retaining the
  same basis, objective, primal algorithm and policy, then using existing native
  reconstruction and full point certification succeeded in both captures.
  Unchanged artificial removal subsequently exported certified original points.

Only the last, isolated result motivates the production change. The broader
alternatives remain diagnostic scripts, not solver behavior.

## Bounded core change

Normal artificial exchanges retain their existing order. Only when the current
basic artificial fails the existing magnitude prerequisite does removal try one
normalization. A prior exchange can make a later artificial removable; checking
all artificials before the first exchange would incorrectly reject that path.
A regression covers this case with native, disabled-budget and checked policies.
Ordinary iterations and already admissible exchanges preserve retained values.

Otherwise, the supported native Float32/Float64 primal kernel with a positive
refinement budget gets one attempt on the private auxiliary workspace. It assigns
nonbasic lower/upper states their exact finite bounds, and free nonbasic states
zero; it then refactorizes the unchanged basis and calls the existing native
phase-transfer completion. The complete point must be certified, and every
artificial must satisfy the unchanged tolerance before removal proceeds.

No pivot, final export or original-model feasibility check is relaxed. Costs,
algorithm, numerical policy and precision remain unchanged. This is boundary
reconstruction, not a pricing or degeneracy heuristic. Checked/staged policies,
dual workspaces, unsupported types and disabled refinement budgets retain their
previous rejection. Stop callbacks and iteration budgets still apply; work is
charged even on failed or interrupted reconstruction. The original numerical
workspace is adopted only after the entire removal and export succeeds.

## Reproduction

Run Julia processes serially through the established 8 GiB guard, with one Julia
and one BLAS thread and local `precompile_workload=false`. Preserve manifests and
binary captures locally. No runtime, medium, big, largo or AnyMod solve is needed
for this boundary investigation.

The seven `reproduce/degen3_*.jl` diagnostic scripts in this change describe their
individual probes. Run them against base `3df48ec` to reproduce the original
failure without the new boundary normalization. `degen3_phase_capture.jl` takes the
same arguments as `broad_corpus.jl`; other probes take one or more capture prefixes.
The exact-nonbasic probe reports actual changed assignments, including zero-valued
variables whose selected bound is nonzero.

Local captures and hashes are listed in `results/artificial-bounds/captures.json`.
Text evidence is retained in the same results directory. Production verification
uses `broad_corpus.jl` and the unchanged 30-job artificial-row manifest; diagnostics
still disable original-LP retries and the separate weak-pivot pricing preference.
Native/JuMP/permuted model equivalence, original unscaled primal feasibility and
independent HiGHS objective references remain checked. Recorded times include
compilation and are not speed measurements.

## Regression design

A portable three-row auxiliary has two nonbasic artificials at `-3tol/4` and
one basic artificial at `3tol/2`. Its signed objective is zero and its auxiliary
point and optimality certificates pass, but old removal rejects it. All eight
Float32/Float64 and basis-manager combinations failed removal before the change
(the 32 prerequisite assertions passed).

Additional fixtures retain a structural nonbasic value outside a lower or upper
bound within tolerance. Exact normalization either restores the feasible origin
or produces an infeasible basic point; the latter must be rejected without
changing the original workspace. Policies, refinement budgets, iteration limits,
early/late cancellation and callback exceptions are tested. A separate fixture
proves that a preceding ordinary exchange may repair a later artificial without
normalization, including on unsupported policies. No-op transfers keep the same
primal values and refactorization count.

## Verification

The final focused suite passes **450 assertions** with normal compilation.
The broader semantic runner passes **10,111 assertions** with `--compile=min`,
including those focused checks, the earlier phase/point/pricing regressions and
eight saved mod010-boundary assertions. Counts include overlap between existing
runners and do not represent distinct tests. A production-only replay of both
exact degen3 rejection captures passes another 12 assertions and certifies
original points after removal at iterations 2370 and 2895.

This is not a full project-suite pass. The immediately preceding change's
300-second normal-compilation project attempt stopped in LLVM compilation;
see the artificial-row report. That unchanged compilation limitation is not
reclassified as success or a solver failure. The focused suite here uses normal
compilation, while the broader semantic run deliberately uses `--compile=min`.

Final production source SHA-256: `c45f33f73dde24d285b3af014540d0efaa0c695fe6e5e3b9fdb3ddf60b20baab`.

The final **30-configuration whole-model run** has **23 verified optima and seven
numerical errors**, compared with 21 and nine on the base commit. Native degen3
now solves in **3613 iterations**, JuMP degen3 in **4089**, with objective
approximately **-987.294** and verified original primal feasibility. Both results
come from fresh MPS solves, not only saved-boundary continuation.

The other **28 configurations are unchanged** in status, iteration and
refactorization counts, phase sequence and objective. The seven earlier errors
remain: mod010 permutation seed 1 with FT/SS, native boeing1, both p0201 readers,
native cycle and JuMP stocfor2. This change does not resolve those errors or the
separate nonzero-RHS Float32 export fixture recorded in the preceding report.
See [the paired outcomes](results/artificial-bounds/models.md).
