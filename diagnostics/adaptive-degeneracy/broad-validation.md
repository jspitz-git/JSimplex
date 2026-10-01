# Broader validation of phase-export recovery

Tested production commit: `26ba604` (`codex/adaptive-degeneracy`).
Production source digest (sorted `Project.toml` and `src/**/*.jl`, including paths):
`7a0e1517d0685035eb496f1c6c73d4dac5ffe644a1fdb18fd9c05bf771a97e76`.
No production solver code was changed for this investigation.

The latest homogeneous-component recovery has useful coverage beyond runtime:
paired runs demonstrate a necessary repair on both **NetLib scsd6** and
**MIPLib mod010**. However, the broader isolated solver configuration is still
sensitive to ordering and has unresolved numerical failures. These results
support retaining the bounded, certified recovery for further development;
they do not establish general robustness or justify merging the entire branch.

## Scope and controls

The corpus contains **33 additional models**, 22 NetLib and 11 MIPLib LP
relaxations. It emphasizes the degen, cycle, stochastic-forestry, SCSD,
shipbuilding, airline, set-covering and integer-model relaxation families,
with other models providing variety. Selection is not a statistical sample or
a claim that every case has severe degeneracy. runtime and medium were not
rerun here; their earlier results remain separate. No big, largo, AnyMod or
alias was solved or factored.

Every model was loaded natively and through `JuMP.read_from_file`, followed by
the production MOI translation into JSimplex. The translated problem was then
passed to `_solve_diagnosed` to apply exactly the same isolated policy and
observer. This covers the JuMP reader and MOI translation, **not an end-to-end
public `JuMP.optimize!` test**. Exact equality of the matrix, objective, constant,
sense, bounds and domains was checked after matching row and column names.
Of 33 JuMP inputs, 21 changed row order and none changed column order. Six
additional runs therefore explicitly permuted both rows and columns.

All corpus solves used Float64, steepest-edge pricing, native refactorization,
interval 80, relaxed integrality, a 1,000,000-iteration ceiling and a **90-second
solver limit per case**. Primary runs used primal PFI. Follow-ups changed only
the named reader/order, algorithm, basis manager or component toggle.

Only stagnation monitoring, adaptive pricing, primal/dual perturbations and
Phase-I construction were enabled in the explicit numerical policy. Other
policy switches were false, including precision boosting and refinement.
The separate adaptive weak-pivot preference was disabled with the existing
`pricing_isolation.jl` override. The outer original-LP retry was disabled to
expose the first failure. Core native safeguards remained active. Consequently,
these results describe this **isolated configuration without the rescue restart**,
not the public default adaptive preset or every possible recovery path.

An observational source override counted repair entry, proposal and local
certification, and captured component inputs. The disabled-component control
returns false at the new helper's entry, preserving all preceding recovery.
Instrumentation hashes are identical across all four corpus result files.
A local certificate alone is not a full phase-export certificate; successful
phase transitions and independently checked final optima provide that additional
evidence for the successful cases below.

Independent references used installed HiGHS 1.15.0 through its C API, simplex,
LP relaxation, one thread, default presolve and a 60-second limit. All 33 returned
OPTIMAL. Every JSimplex OPTIMAL was checked against its reference objective
(`rtol=1e-8`, `atol=1e-7`) and for original primal feasibility at `1e-7`, both in
the loaded model and after mapping back to native input order. All 68 reported
optima passed; the largest normalized objective difference was
`1.5148122048238201e-9`.

Runs were serialized on Julia 1.13.0 aarch64, JuMP 1.31.2, one Julia/BLAS thread,
with precompile workload disabled. The established guard limited owned process
virtual memory to 8 GiB and stopped only its process group if available RAM
fell below 6 GiB or swap exceeded 1 GiB. Independent HiGHS runs were also
serialized and guarded. Common paths were warmed, but compilation and snapshot
I/O remain in timing measurements. **This is not a speed benchmark.**

## Corpus results

| Group | Solves | Verified OPTIMAL | NUMERICAL_ERROR | TIME_LIMIT | INFEASIBLE |
| --- | ---: | ---: | ---: | ---: | ---: |
| Primary: 33 models, native primal PFI | 33 | 22 | 6 | 4 | 1 |
| Primary: same models, JuMP primal PFI | 33 | 24 | 3 | 5 | 1 |
| Follow-up: FT/SS/BG, 4 models each | 12 | 10 | 2 | 0 | 0 |
| Follow-up: explicit row/column permutations | 6 | 4 | 1 | 1 | 0 |
| Follow-up: dual PFI, 4 models, both readers | 8 | 8 | 0 | 0 | 0 |
| Paired controls: component disabled | 9 | 0 | 8 | 0 | 1 |
| Total | 101 | 68 | 20 | 10 | 3 |

The total includes deliberately disabled controls and is not a success rate
for 101 independent models. See the [33-model primary table](results/broad-validation/primary-table.md)
and [individual follow-up results](results/broad-validation/followup-table.md).
Raw TOML records retain objective checks, event counts, phase transitions,
ordering counts, budgets and capture paths. No run ended in a harness exception.

All ten TIME_LIMIT results remain unresolved within 90 seconds; they are not
proofs of nonconvergence. In the primary runs, degen3, air04, air05 and 10teams
reached the limit with both readers, and degen2 with JuMP. All remained in Phase I.

The observer counts *exactly zero primal steps on completed pivots*, excluding
bound flips and near-zero steps. Examples: native scsd6 had 247/340 zero steps,
native mod010 317/532, and JuMP degen3 109,271/113,419 observed pivots. These
observations establish substantial degeneracy in parts of the selected corpus;
they do not measure all forms of stalling.

## Direct evidence for the latest repair

| Model / reader / manager | With component recovery | With component disabled |
| --- | --- | --- |
| scsd6 / native / PFI | OPTIMAL, 340 iterations; export at 118 | NUMERICAL_ERROR at 118, artificial removal incomplete |
| scsd6 / JuMP / PFI | OPTIMAL, 340 iterations; export at 118 | NUMERICAL_ERROR at 118, artificial removal incomplete |
| mod010 / native / PFI | OPTIMAL, 532 iterations; export at 273 | NUMERICAL_ERROR at 273, artificial removal incomplete |

The component was attempted, proposed and locally certified once in each enabled
case. Native scsd6 also invoked and certified the component with FT, SS and BG,
reaching verified optima in 326, 329 and 337 iterations respectively. These
triangular-manager cases were not separately rerun with the component disabled.

The two explicit scsd6 permutations reached optima in 334 and 355 iterations
without needing this repair. JuMP mod010 reached its optimum in 595 iterations
without entering local repair. Thus ordering changes the need for recovery;
there is no claim of an identical trajectory or universal necessity.

Only these six enabled real-model runs entered the new component helper:
five scsd6 cases and one mod010 case. Other successes provide regression coverage
but no direct evidence of the component's effectiveness.

## Failures outside this repair

Every nonoptimal enabled corpus run had zero component attempts and zero local
reconstruction attempts. Six paired controls (native degen2, cycle, scsd8,
boeing1, pilotnov and JuMP stocfor2) reproduced the same termination status,
message and iteration with the component disabled. This rules out execution of
the new helper as the direct cause of those captured failures; it does not
attribute all failures to master or exclude interactions among earlier branch
changes.

Observed numerical termination categories include:

- Reduced cost versus direction disagreement: native degen2 (2160), native
  boeing1 (202), p0201 both readers (110), native misc07 (198).
- Bounded feasibility recovery exhausted: native cycle (868), scsd8 both readers
  (649), and native cycle with SS (897).
- Primal feasibility lost: JuMP stocfor2 (1957).
- Primal point could not be certified: native stocfor2 with BG (975).
- Artificial removal incomplete: explicitly permuted mod010 (325).

Numbers in parentheses are iterations. The mod010 permutation failure is
particularly useful for further diagnosis: the original ordering solves, the
permutation fails before the new local/component recovery is entered. Captured
last-observed workspaces are retained locally; they are diagnostic observations,
not guaranteed exact snapshots of the outer termination boundary.

Dual PFI solved degen2, degen3, cycle and scsd6 with both readers (8/8 verified
optima). None entered the component repair. This is limited cross-method
coverage, not a claim that dual is robust on the whole 33-model corpus.

### pilotnov presolve tolerance discrepancy

Both readers reject pilotnov before simplex, reporting inconsistent row bounds.
A separate HiGHS point, mapped by column names, passes the original JSimplex
primal check at `1e-7`: maximum column violation is zero and maximum row
violation from Float64 matrix-vector multiplication is
`3.8198777474462986e-10`; objective is `-4497.2761882188715`.

At the captured native presolve rejection, row `KDRL01` (current index 21 in a
919-by-1759 reduced problem) has lower bound `-147.0`. Its strict activity-bound
comparison has a gap of only `8.1601392309949e-15`, computed using exact rational
representations of the current floating-point data. The rounded displayed
maximum is also `-147.0`. Presolve source is unchanged from master.

This establishes a mismatch between tolerance-based point acceptance and a
strict reduced-bound contradiction. It **does not prove exact rational
feasibility of the original LP or mathematical incorrectness of a particular
presolve pass**. It requires a separate tolerance-policy investigation. The
three diagnostic assertions verify this observation, not a fix.

## Independent generated local tests

The local reconstruction runner builds 40 independently generated nonsingular,
diagonally dominant homogeneous blocks (sizes 3 through 10), coupled in a block
diagonal matrix with a two-variable nonzero-RHS subsystem. It tests Float32 and
Float64, with original, permuted and scaled/permuted layouts: **240 variants**.
Row/column scale factors are powers of two with exponents in `[-8,8]`.

All 240 recover the known point and pass the full compensated residual check;
237 require the new component (80 original, 80 permuted, 77 scaled/permuted).
The other three already recover with local sweeps. Every forced nonzero-RHS
candidate and zero-cutoff trial is rejected atomically, leaving the input point
unchanged. The altered nonzero-RHS systems remain nonsingular and solvable;
rejecting this bounded recovery candidate is not a statement of infeasibility.

The runner passes **2,880 assertions**. These are tests of a bounded local
reconstruction family, not 240 independent LP solves, arbitrary scaling
invariance, or a convergence proof. No coefficients are taken from runtime.

## Artifacts and reproduction

All inputs, source hashes and jobs are recorded under
[`results/broad-validation`](results/broad-validation). The input manifest lists
original compressed files, prepared MPS files and both hashes. No source input
was modified. Binary captures and the named oracle point remain under the local
`.superpowers/adaptive-degeneracy/broad-validation/captures` directory;
[`local-captures.json`](results/broad-validation/local-captures.json) records
absolute paths, sizes and hashes. Presolve-only failures have no workspace
capture and are marked absent. Manifests and LocalPreferences are not committed.

The smoke and primary harness copies preserve their exact as-run versions.
Later diagnostic edits add job/seed metadata, exception fields and compilation
timing; the instrumented arithmetic hashes are unchanged. The current reference
script additionally writes TOML and named primal points; the original 33-reference
run wrote JSON, then its identical numeric records were converted to TOML.
The separate pilotnov rerun used the current script to capture its point.

Set up a local Julia project with JSimplex pointing to this checkout and
JuMP 1.31.2, and preserve `precompile_workload=false`. The reference script uses
the installed HiGHS library path shown in its source; adjust that path on a
different machine. Run the following commands **serially through the existing
owned-process memory guard**, with one Julia/BLAS thread (the corpus runner sets
BLAS to one). Use unique output prefixes; the runners refuse to overwrite results.
The existing `julia.sh` wrapper also supplies the local offline depot stack.

```sh
python3 diagnostics/adaptive-degeneracy/reproduce/broad_prepare.py /tmp/broad-inputs
python3 diagnostics/adaptive-degeneracy/reproduce/broad_reference.py \
  /tmp/broad-inputs/inputs.toml /tmp/new-reference.json

julia --project=.superpowers/adaptive-degeneracy/broad-validation/env \
  diagnostics/adaptive-degeneracy/reproduce/broad_corpus.jl \
  /tmp/broad-inputs/inputs.toml /tmp/new-reference.toml \
  diagnostics/adaptive-degeneracy/results/broad-validation/primary-jobs.toml \
  /tmp/new-primary
# Repeat serially with followup-jobs.toml and mod010-baseline-jobs.toml.

julia --project=. --compile=min \
  diagnostics/adaptive-degeneracy/reproduce/broad_components.jl /tmp/new-components.toml
julia --project=. --compile=min \
  diagnostics/adaptive-degeneracy/reproduce/broad_pilotnov.jl \
  /tmp/broad-inputs/netlib-pilotnov.mps \
  /tmp/new-reference-netlib-pilotnov-primal.toml /tmp/new-pilotnov.toml
```

The primary run was split into the first two jobs (smoke) and remaining 64;
therefore use those manifests and frozen harness copies to reproduce that process
split. The follow-up runner used 34 jobs, followed by the one mod010 control.
As-run wall guards were 2,400 seconds for the reference corpus, 4,200 for the
34-job follow-up and 300 for each generated/control diagnostic; per-case solver
budgets are in the job manifests. Allow enough wall time for compilation and
all serialized solver budgets when repeating the 66-job primary manifest.

## Assessment and next investigation

The final component correction is not supported solely by runtime: two unrelated
real models need it, all four managers exercise it on scsd6, and independent
local families verify its bounded, atomic behavior. Yet a broad claim that the
simplex core is now stable would be false. The corpus exposes earlier failures,
ordering sensitivity and a presolve tolerance discrepancy, all recorded without
hiding them behind an original-model restart.

The next useful work is to capture and classify the reduced-price/direction
failures and the mod010 permutation's failed artificial removal, alongside a
separate presolve tolerance analysis. Further runtime-specific fallback layers
are not justified by these results. No production adjustment, merge or push was
performed in this validation step.
