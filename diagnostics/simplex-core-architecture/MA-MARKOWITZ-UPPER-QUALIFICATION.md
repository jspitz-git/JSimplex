# MA-F: Markowitz MA qualification attempt — harness failure

MA-F is NOT ACCEPTED for correctness or performance. The single reserved attempt
stopped in the RED driver before test inclusion. The expected two missing-helper
assertions were not evaluated; qualification and every cost process were not run.
This is a diagnostic harness defect, not evidence against the MA candidate.
Production, actual tests, Project/environment, master and CI remain unchanged.

## Execution and preservation

Preflight passed 11 gates, including all 1,761 immutable launch pins, 1,760 required
members, 33 final-review bindings, prior closure/publication, local/remote refs,
protected user files and all 44 historical process groups AND sessions/no Julia.
The exact reviewed seal ran once; separate nine-gate seal inspection passed.
The exact reviewed launcher ran once and consumed its exclusive reservation.

Diagnostic baseline: bf4f941328538134e6df6251655f2465370a1405.
Master/primary baseline: 6f68e24e8ddac42b948da8fcc2d636c010751194.
Canonical manifest SHA256:
8bea50419a47272608b551d429171a35da5362cf036622c126a80063db0376e4.

Only the reference RED child launched. Its terminal process record is exit 1,
reason exit1; pins_unchanged=true. Launcher invocation all_passed=false, no accepted
stages, error ValueError('terminal guard failure'). The generic launcher message
is not the root-cause diagnosis. The raw TOML preserves the actual exception:
`UndefVarError: push_testset not defined in Test`, at MA-E/driver.jl:53.
No tests/counts/compare_metrics/full_metrics fields were produced; records is empty.
No RED audit, qualification or cost output exists. An empty run.log is preserved;
the driver caught and serialized its exception into raw.toml before exit 1.
current.json is the initial launch snapshot (reason launch_error/returncode null),
not the terminal outcome; process.json is the terminal record.

Eight original attempt files have byte-identical portable copies under
results/MA-F/attempt-1. Execution seal and reservation remain in results/MA-E at
the exact admitted paths. All initial/rejected reviews, scripts and false gates
remain unchanged. No launcher, driver or original auditor was rerun or rewritten.

## Root cause and scope

The frozen driver calls Test.push_testset(ts) before its inner try and before
Base.include of tests-instrumented.jl. Installed Julia 1.13.0 Test.jl contains
neither push_testset nor pop_testset. Its current context uses ScopedValue and
@with_testset, with scoped parent/depth restoration. The read-time Test.jl hash
and exact relevant excerpt are recorded separately in postcheck.json and
installed-Test-context.txt. This is not a retroactive launch pin.

MA-E admission failed to verify these entry/exit symbols against the installed
Test implementation. The same obsolete API error was already recorded in S4-AD;
its separate repaired collector uses @with_testset. That earlier repair is a
source reference for a future amendment, not evidence that this driver works.
The original MA-E accepted review stays frozen and is not retroactively corrected.

The source path/version checks were reached before the error and raw records the
reference overlay on Julia 1.13.0. No test body or fixture sweep was reached, so
there were zero scheduled test assertions, candidate kernel calls, fixture solves
or measurement windows. Ordinary package import/initialization occurred; this is
not zero total work, an import-work budget or a hidden-runtime closure proof.
No allocation or speed result can be inferred from this failed attempt.

## Independent post-exit evidence and computational cost

New postcheck.py was saved before one execution: 15/15 provenance checks PASS.
It rehashed all 1,761 launch pins, verified all eight portable files, seal/reservation/
command linkage, protected files, actual source/test/Project/CI and local/remote
refs. This PASS accepts failure provenance only, not the failed RED or qualification.

Runner PID/PGID/SID190814 start_ticks9635543; child PID/PGID/SID190815
start_ticks9635574; boot dade7243-9103-4398-bb45-fa28fbc0be72. Fresh host enumeration
checked all old 44 plus both new groups AND sessions: none present, no Julia.
The complete recorded commands accompany identities in process.json.

Four resource samples: minimum available RAM22,052,268KiB, maximum swap0KiB;
terminal RAM22,250,452KiB/swap0. Guard inclusive4.290566305s, launcher inclusive
5.135017348s. These include startup/failure handling and are not benchmark samples.
The run ended well inside its RED30s/total750s bounds without resource rejection.

No production code changed; therefore no new per-iteration scans, solves,
conversions, allocations or retained caches were introduced. Diagnostic import,
manifest hashing, serialization and portable copying are cold workflow costs.
Candidate ownership, sequential rounding, allocations, retained scratch and
full-forward benefit remain runtime-unqualified by MA-F; all predeclared correctness
and performance thresholds remain intact. No numerical safeguard was relaxed.

## Continuation and binding map

The MA-F attempt is consumed and frozen. Do not rerun its launcher, reuse its
reservation, extend limits, retune the candidate or call the failed RED an expected
regression failure. No production integration is admissible from this evidence.

Next concrete work is a separate offline harness amendment: use the installed
scoped Test context, enumerate every Test-qualified symbol/result field, verify
parent/depth restoration and child recording exactly once on exceptional paths,
and preserve all 381 test assertions, fixture bits, arithmetic, work counts,
comparison schedule and benefit thresholds. Reuse the already repaired S4-AD
collector as a source reference. Create new files and a fresh independently reviewed
admission/seal/output reservation before any later short attempt. Standing human
short-run authorization remains; no duplicate permission question is required.
No amendment implementation or second numerical attempt is included in this closure.

MA-E current STATUS/roadmap hashes in closure.json, closure-final.json and
publication.json now map ONLY to MA-F/STATUS.md.before-MA-F and
MA-F/roadmap.md.before-MA-F, respectively. All older mappings remain unchanged.
The original MA-F plan remains frozen as the executed decision contract.
Automation remains paused, CI off, HH reuse disabled; broader MA and S2/S3/S4/S5/S6
remain open. All stopped routes remain stopped.
