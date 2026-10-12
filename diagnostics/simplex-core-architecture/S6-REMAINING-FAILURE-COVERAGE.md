# S6-AJ: complete historical failure coverage reconciliation

Source/evidence-only, at diagnostic base `4c34931` and master `354bb1f`.
No Julia, factor/workspace/solve/certificate call, test change, CI dispatch or old
parser/driver/auditor execution. Host process state was checked with /proc; previous
runner 417368, child 417369 and launch group 417360 were absent, no Julia present.
Exact boot: `20de7dde-704e-41c8-bee7-b8511c0a86b0`. Local and remote refs matched.

## Accounting and current source binding

`results/S6-AJ/coverage.json` maps every saved S6-A entry by the unique pair
(run ID, raw log line), retaining its historical file/line/title/kind/expression,
current assertion start, repair stage and remaining coverage limit. It does not
parse the original logs again. Original raw hashes were independently verified.

| Historical run | Passed | Failed | Errors | Total |
|---|---:|---:|---:|---:|
| 38149970679, 4914cbb | 329511 | 197 | 1 | 329709 |
| 38142752357, b720674 | 329508 | 200 | 1 | 329709 |

399 failure/error records map exactly once to 24 distinct assertion locations.
This is a reconciliation of two runs, not 399 independent defects. There are
18 successful offline checks and 534 input hashes. All tracked production/test/CI
files equal current master. Seven repair file versions equal their integrated
commits; the eighth repair, AA, is bound by its unchanged target block inside the
later AC version of the same file. Saved master audits and logs are read-only
historical evidence, not fresh executions on this master.

23 historical assertion starts remain byte-identical. S6-C intentionally changed
`@test terminal.status==NUMERICAL_ERROR` into
`@test !isnothing(terminal) && terminal.status==NUMERICAL_ERROR`; the historical
FieldError therefore maps to the current guarded status assertion, not an unchanged
error expression. The initial generic exact-line mapper rejected this location
before producing output. Its source/exit 1 are preserved in `parser-1`; the new
explicit mapping records that strengthening rather than silently normalizing it.
No numerical failure was reproduced by this Python analysis.

## Disjoint family ledger

Counts below are failures + errors, latest / older run. Local gate sizes include
added and neighboring checks; they must never be subtracted from historical counts.

| Historical test family | Latest / older | Repair and saved local master gate | Remaining limitation |
|---|---|---|---|
| Repeated primal price disagreement | 12+0 / 12+0 | W → b9e7cb1, 41/41 | Controlled Float64 BTRAN boundary; original backend trajectory unproved |
| Exhaustion after fresh pricing | 2+1 / 2+1 | C → a465da5, 20/20 | Upper bound 1→1e8 and guarded status; no x64 rerun |
| Dual rejection budget + refresh cancellation | 48+0 / 48+0 | AI → 354bb1f, 252/252 | Narrow declared-output recovery budget; AF certificate hypothesis stays rejected |
| Artificial exchange reconstruction / reliable zero-budget exchange | 8+0 / 8+0 | AC → 3c0af5c, 215/215; AA → 74f7835, 19/19 | Two disjoint four-failure assertions; private historical export/rejection not captured |
| Artificial-row cancellation/recovery | 96+0 / 96+0 | G → 8516e0d, 348/348 | Phase-only Float64 real-forward declaration, not downstream native arithmetic proof |
| Nearly singular bounded model | 1+0 / 1+0 | T → afb37d9, 19/19 | New row-balanced fixture has different feasible set; old cancellation stress remains evidence |
| Supplied BigFloat tolerance, primal kind | 30+0 / 30+0 | M → 7fea422, 1477/1477 | Valid margin 4g>2t; no end-to-end last-bit t-versus-g proof |
| Native bound-journal retirement after disabling heuristics | 0+0 / 3+0 | No S6 test repair; unchanged native source, S5-C focused 1463/1463 aggregate reused | Exact historical return status/message/elapsed deadline missing; unresolved family |

The first seven rows account for 197 failures + 1 error in EACH run and have scoped
local repairs. The additional three failures in the older run remain unrepaired as
a historical family. This does not mean either current CI run would have only three
failures, or that 197 historical failures have had their machine causes proved.

Every assertion location (counts per latest/older run):

| File | Historical → current line | Kind | Latest / older | Local repair |
|---|---|---|---:|---|
| `legacy_primal_direction_price_tests.jl` | 214 → 290 | failure | 4 / 4 | W |
| `legacy_primal_direction_price_tests.jl` | 215 → 291 | failure | 4 / 4 | W |
| `legacy_primal_direction_price_tests.jl` | 216 → 292 | failure | 4 / 4 | W |
| `legacy_primal_preference_work_tests.jl` | 38 → 40 | error | 1 / 1 | C |
| `legacy_primal_preference_work_tests.jl` | 39 → 41 | failure | 1 / 1 | C |
| `legacy_primal_preference_work_tests.jl` | 40 → 42 | failure | 1 / 1 | C |
| `dual_pivot_consistency_tests.jl` | 68 → 216 | failure | 16 / 16 | AI |
| `dual_pivot_consistency_tests.jl` | 69 → 217 | failure | 16 / 16 | AI |
| `dual_pivot_consistency_tests.jl` | 66 → 214 | failure | 4 / 4 | AI |
| `dual_pivot_consistency_tests.jl` | 61 → 209 | failure | 4 / 4 | AI |
| `dual_pivot_consistency_tests.jl` | 63 → 211 | failure | 4 / 4 | AI |
| `dual_pivot_consistency_tests.jl` | 103 → 255 | failure | 4 / 4 | AI |
| `native_phase_transfer_tests.jl` | 164 → 287 | failure | 4 / 4 | AC |
| `native_phase_transfer_tests.jl` | 211 → 348 | failure | 4 / 4 | AA |
| `native_artificial_row_tests.jl` | 65 → 114 | failure | 20 / 20 | G |
| `native_artificial_row_tests.jl` | 66 → 115 | failure | 20 / 20 | G |
| `native_artificial_row_tests.jl` | 68 → 117 | failure | 20 / 20 | G |
| `native_artificial_row_tests.jl` | 71 → 120 | failure | 20 / 20 | G |
| `native_artificial_row_tests.jl` | 70 → 119 | failure | 16 / 16 | G |
| `solver_tests.jl` | 552 → 564 | failure | 1 / 1 | T |
| `bigfloat_integrity_tests.jl` | 282 → 288 | failure | 30 / 30 | M |
| `primal_perturbation_integration_tests.jl` | 187 → 187 | failure | 0 / 1 | none |
| `primal_perturbation_integration_tests.jl` | 188 → 188 | failure | 0 / 1 | none |
| `primal_perturbation_integration_tests.jl` | 189 → 189 | failure | 0 / 1 | none |

The 16 dual state failures in each run are a subset of that run's 48 dual failures,
not an additional family. H's comparison excludes events. The sole error per run
is the preference test's `Nothing.status` access, not a runner/provisioning error.
The phase line 164 four `accepted=false` entries have unknown scalar in the saved
printout evidence. The eight explicit Float32 printouts analyzed in X are four
zero-budget entries per run, not eight additional failures per run. A printed phase
point is not the private export candidate or its runtime certificate. AA/AC do not
assign a historical scalar to the unknown four or identify the backend cause.

## Preserved native coverage and remaining integration obligations

All original 108 dual recovery predicates remain through AI; the other 108 native
assertions and old helper are byte-identical. AI freshly exercised 10 small-pivot
neighbor calls (60 assertions), while the duplicate-column native 48 assertions
were reused/static coverage. G/W/AA/AC preserve neighboring native testsets and
original predicates within their stated scopes. This report does not turn these
mixed fresh/reused obligations into a new complete file or full-suite run.

The unchanged `primal_perturbation_integration_tests.jl` was included in S5-C's
nine-file focused 1463/1463 run (saved file list, aggregate log and four audit checks).
`native-reuse.json` independently compares all saved S5-C audit source hashes with
current production. The cleanup test also matches both historical test sources.
This supports native coverage reuse; it does not explain why only the older CI run
failed at lines 187–189. The failed expression is a conjunction and does not expose
`run.status`, `run.message` or `run.primal`; the subsequent printouts expose shifted
bounds and a retained journal, not the return status or elapsed time.

The helper sets a 30-second limit. SimplexRunBudget inherits `ws.progress.start_ns`,
and `_install_driver_policy!` keeps that timestamp by default. A forced feasibility
path checks the shared deadline before basis verification. Cleanup restores active
bound perturbations only after OPTIMAL/INFEASIBLE/UNBOUNDED terminals. Thus an expired
budget is a source-supported candidate explanation for an unretired journal, not
a demonstrated historical cause. Native numerical rejection and other exits still
need source reconciliation. Do not reset clocks, extend limits or insert warmups
as an assumed fix.

Broader obligations remain distinct from this failure inventory:
- S2: full fused work/scan and rejected-candidate semantics; audited-flip S2-A stays rejected.
- S3: manager/support/history and sparse/dense transitions across end-to-end paths;
  accepted S3-A/B do not close the broader gate.
- S4: backend lifecycle/allocation/retention scope and native symbolic reuse; S4-C
  mostly-zero256 median 1.0258 is not a speedup. S4-D's original hash failure remains.
- S5: state ownership, cleanup/handoff work and original-model certificates; S5-C
  does not authorize eliminating initial reconstruction or deduplicating bound copies.
- S6: current-platform integration, both algorithms/full medium, outstanding test.mps
  certificate and reference-set obligations, and credible repeated timing comparisons.
  Historical completed reference/cost work must be reused; any genuinely missing
  numerical obligation needs its own bounded plan, not a blanket repeat of the roadmap.

Local 1.13.0 aarch64 evidence is not Julia 1.13.1 x64 Ubuntu CI with coverage and
bounds checking. CI remains manually disabled. No full-suite/platform success,
observer-neutrality, hidden trajectory or working-to-original certificate transfer
is established. S6-J and whole S6-AF remain rejected, with original failed oracles,
exit values and false gates untouched. AF's vacuous `no_errors` field is not used.

## Next selected obligation and cost review

Select the remaining native bound-journal retirement family. The new S6-AK plan
`2026-10-12-native-cleanup-termination-contract.md` is SOURCE/EVIDENCE ONLY: map
ownership/deadline and all possible returns before deciding what a new observation
could discriminate. No numerical launch is justified by the aggregate local pass
or guessed historical status alone. AK must produce a separate exact bounded
numerical plan if that analysis warrants one; it cannot silently rerun S5-C or the
old test file. This is a deliberate ruling in favor of establishing the missing
causal observation, not a claim that a deadline fix is ready.

No production execution frequency, scans, basis solves, allocation or retained memory
changed. This offline reconciliation adds no production work or memory cost; no
benchmark is warranted. The script stores 399 small mapping records and hashes only
as diagnostics. All historical numerical drivers/auditors remain unmodified.
Fresh independent coverage and work review is recorded separately.

## Review closure

Fresh gpt-6-astra review found no Critical/Important and one Minor structured
scalar label issue, author regraded Important for this ledger's explicit scalar
contract. One offline RED8 incorrect labels -> GREEN16/16 amendment now distinguishes
8 printed Float32 line211 records from 8 scalar-unknown line164 records across the
two runs. Original output and mapper remain preserved; no numerical/parser rerun.
See REVIEW and scalar-scope-fix.json. No new deferred Minor. Independent verification
also passed9checks, including hashes, event keys, two historical source trees and
current AI/AC/W frozen master test snapshots. The original mapper is exclusive-write
and is NOT the validator for amended output; use the explicit amendment and fresh
read-only checks. Source-only AJ is complete; master/production/test/CI unchanged.
