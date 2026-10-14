# MA-S-2 DenseLU BigFloat: correctness qualified, whole cost gate rejected

The single admitted three-process sequence completed with exit0 in every process.
All160correctness cases passed4329assertions, reference smoke passed16/16, and
original missing-route RED produced exactly0pass/2fail/0error/0broken. The corrected
outer latest-world driver boundaries worked for this sequence. All36BigFloat target
cost cases passed, but four fallback controls failed allocation gates. Aggregate
accepted=false,48of52cases accepted. This exact variant is NOT accepted for
production promotion; Task3 integration must not start from this result.

## Admission, execution and correctness

Fresh published preparation HEADcfe00c83a1723d5bfce4da663e6bac8606ddad16 and
master6f68e24e8ddac42b948da8fcc2d636c010751194 were verified locally/remotely.
New preflight14checks verified all4304pins,73preparation bindings,514source
identities,6protected files and all160historical PGIDs ANDsessions/noJulia.
Independent numerical admission31checks/87bindings accepted the exact new context,
commands, corrected MA-S-LOAD driver and unchanged MA-R inputs. Original MA-S
world-age failure, reservation and all old evidence remain unchanged.

launcher.py was executed once with absolute /usr/bin/python3 -B. Process1 freshly
performed the reference smoke and exact missing-route RED before including the
candidate/instrumentation; the generic import failure of MA-S was not reused as RED.
The160cases contain162calls per side, reference/candidate/instrumented, plus2smoke
calls:488explicit backend entries. Exact token/precision/sign, input values/owners,
retained outputs, aliasing, matching/scoped rounding and mixed stored precision,
exception class/message and partial writes met the frozen assertions. Empty/small,
zero/nonfinite, pivot/dimension and copied-PFI cases retain their exact scope.
Processes2/3 performed no extra correctness/RED. These tests establish scoped local
correctness, not full public integration, all Julia versions or hidden trajectories.

Stage audits passed23/23,21/21,21/21 with all raw hashes and loaded-path membership.
All3120windows were preserved:936warm and2184measured,12480whole backend cost calls.
Every measured compile/recompile value is zero. There were52windows with nonzero GC,
including39measured (11/13/15per process); no GC sample or timing outlier was removed.
The accepted audit.py aggregate command was executed once, after all three
successful stage audits, and wrote aggregate.json.

## Measured benefit and exact rejecting controls

All36targets independently pass the frozen per-process and pooled rules. Their
pooled paired candidate/reference time medians range0.535572–0.743382, corresponding
to25.66–46.44% lower local whole-backend time. Across target/process median windows,
bytes ratios range0.508078–0.548609 and events ratios0.508122–0.549411: about45–49%
lower traffic/events. These ranges describe the fixed n16/32/64,128/256/512bit,
dense/zero-heavy FTRAN/BTRAN cases, not an aggregate end-to-end solver speedup.
Scratch construction, eligibility, original copies/pivots/scans/subtraction/division
and stores remain inside each whole-call window.

All16controls pass their time gates;12pass all gates. The following four fail
strict no-increase allocation rules. Values below are per four-call window; they
are process medians, not individual-event attribution.

| Control | Pooled paired time ratio | Median candidate minus reference bytes, processes1/2/3 | Events delta, processes1/2/3 |
| --- | ---: | ---: | ---: |
| scoped-rounding BigFloat forward | 1.006660 | +128/+128/+128 | +8/+8/+8 |
| scoped-rounding BigFloat transpose | 0.999127 | +128/+128/+128 | +8/+8/+8 |
| Rational{BigInt} forward | 0.994217 | +16/0/0 | 0/0/0 |
| Rational{BigInt} transpose | 1.003567 | +16/+16/+32 | 0/0/0 |

The BigFloat fallback delta averages32bytes and2events per call in these medians.
Rational byte deltas are small, but the admitted rule gives no byte tolerance and
must not be loosened after observing them. Their cause is not established by these
aggregate counters. Source shows these controls delegate to the original routine
before product scratch; the extra traffic is NOT evidence that the private product
was allocated on fallback. No allocation profiler, new probe or causal attribution
was executed. The full underlying per-process medians, ratio ranges, MADs, wins,
GC and outliers remain in raw.toml/aggregate.json. For example the rational-forward
ratio maximum6.124152 remains; no cause is inferred. Near-unity fallback times and
small byte variations are not universal regressions or equivalence proofs.

New result-analysis.py independently recomputed all52decisions from the three raw
files and unchanged fixtures;16checks pass. It confirms48accepted,all36targets,
12controls and all control time gates. It does not rerun or modify the old auditor.
False aggregate acceptance remains false.

## Resources, work and memory

Inclusive guarded invocation durations were17.771007/10.788732/10.788814seconds,
39.348553seconds cumulative. Guard durations17.382280/10.392001/10.379162seconds;
all below the accepted limits. Cold load4.601637/4.276598/4.261083seconds and candidate
definition0.028450/0.029421/0.030066seconds are separate observations, not paired
loader overhead or speedup. Resource samples17/10/10, minimum available RAM
22437900KiB, maximum swap0, terminal memory also within guard. New postcheck18PASS/
53bindings independently verifies unchanged4304pins, both reviews, all raw hashes,
refs/source514/protected6, boot and all166historical plus new PGIDs ANDsessions
absent/noJulia. Runner/child identities, commands and start_ticks are recorded.

The fixed source-bound schedule completed12968explicit backend entries including
correctness/smoke and costs,318explicit setup factorizations including2PFI constructors,
and2PFI copies. Setup/helper/import/native work is additional; these are not complete
PREforward counts. One private O(precision) product is created per eligible call;
O(1)eligibility and original O(n²)arithmetic/scans/O(n)copies/pivots remain. No new
production code, cache or retained production memory was introduced. Diagnostic
factor deepcopies, preservation/owner scans and exact tokens outside windows may
perturb cache/GC and retain leaves. Aggregate GC counters can include native traffic
and are not live/native-retention measurements. No public LP or eta lifecycle was
added. Four fallback allocation gates are a real admission blocker despite the
substantial target savings. The inherited duplicate cold Python resource validation
remains deferred; no new production overhead claim is hidden by that minor.

## Decision and continuation

The admitted sequence is consumed and frozen. Do not rerun any of its three stages,
audit or aggregate, change thresholds, tune fixtures, or promote this candidate.
No original numerical defect or general impossibility of MA is established.
A useful next step is a separate bounded offline analysis of fallback allocation
sources using these stored results and pinned source, with independent review before
any changed candidate or new experiment. This report itself authorizes no retry,
new numerical schedule or production change. Standing permission for short attempts
persists, but each distinct attempt still needs concrete accepted technical admission.
Broader plan remains OPEN; Task3 public PFI/afiro/sc50a gates remain conditional.

Current MA-S-2 preparation review, numerical seal, closure and publication STATUS/
roadmap hashes map ONLY to STATUS.md.before-MA-S-2-execution and
roadmap.md.before-MA-S-2-execution, explicitly in execution-continuation-map.json.
All earlier LOAD/S maps remain unchanged. The original preparation report, ledger,
plan, scripts, raw and false records are frozen. Current continuation updates occur
only after all runtime/audit/postcheck work finished. Independent result review and
separate execution closure/publication accept the diagnostic result, never convert
aggregate false to true. Production/test/user environments/master/CI unchanged;
HHreuse disabled, automation paused.
