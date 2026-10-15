# Direct LU native backend diagnostic result

The ONE admitted diagnostic completed with exit0 in6.795441914000548seconds
inclusive. Diagnostic integrity is accepted by the canonical12-gate audit; this
is NOT numerical correctness or cost acceptance. Of18 exact residual checks,
15 pass and3 fail: fresh DSE, ordinary post-refactor DSE, and direct-base DSE.
All three failing vectors are bit-identical to each other and to the original
cost1 step5 failed vector. The original cost1 false audit remains frozen and
cost2 remains blocked. No production/test/environment/CI/master change.

## What the new evidence establishes

The same error is present in a freshly constructed B4 native UMFPACK backend,
without the FT update/refactor prefix. It is also present when directly solving
through the native backend after that prefix. Thus the observed error does not
require FT history or the post-backend composed-row operations. This statement
is scoped to these recorded inputs/outputs; it does not establish the specific
native operation, machine instruction or implementation defect causing it.

The worst original residual is row87:
9928545/144115188075855872 = approximately6.889312037516859e-11.
The unchanged exact bound is
144694209253234815/39614081257132168796771975168,
so residual/bound=18.861415966018026. All entering and BTRAN outputs pass, as do
the four prefix DSE outputs before refactor. No tolerance or precision was changed.

Fresh and prefix factor snapshots agree in every captured field except Info.
Each has234 lower and248 upper stored entries. Actual do_recip=1 in both contexts;
recorded Rs is the effective multiplier, range approximately0.20915..0.23529.
The exact scaled factor identity L*U=(Rs.*B4)[p,q] is NOT exact: maximum entry
residual53/4398046511104. Nonzero factor residual alone is not a defect proof.

The source-bound offline decomposition separates recorded representation from
combined application consistency. At permuted row31 / original row87, converted
back to original row units:

| Term | Value (approximate) |
| --- | ---: |
| Representation action (L*U - scaled B)*x | -1.568052914940958e-11 |
| Combined application (L*U)*x - scaled rhs | +5.321259122575901e-11 |
| Original B*x-rhs = application - representation | +6.889312037516859e-11 |

Both terms are nonzero and contribute with the shown signs. The exact identity
is checked in interpretation.json, with rational terms retained. This is not
captured intermediate forward/back substitution state, nor proof identifying
which native factorization or solve operation introduced either discrepancy.
There is no allocation/time comparison, universal speedup or public-solver claim.

## Executed scope, ownership and work

Exactly3 explicit factorization entries,13FTRAN,5BTRAN,4replacements,1refactor,
and2 final metadata snapshots were recorded. Native default IRSTEP remained0;
five control captures and both snapshot controls are bit-identical. All16 reset
predicates pass before step5; inputs retain exact tokens and native CSC inputs
are separately owned and equal. The two ordinary outputs were captured before
the extra base-only solve and remain unchanged afterward. No fifth replacement,
warmup, hidden diagnostic orientation solve, factor copy, quality/refinement/
certificate call, GC or cleanup was added. Entry counts are not transitive
native/import-work accounting.

The preparation's diagnostic cost ledger applies unchanged:18 length96 output
vectors,192 immediate snapshot tokens, full input parsing/preservation scans,
two owned CSR-L/CSC-U snapshots plus control/Info/native-CSC records. Each snapshot
uses one get_lunz and one combined get_numeric, capturing do_recip in that call.
Fresh B4, prefix active B4 and retained B0 spare make three live native factors;
ordinary FT scratch/history/prepared storage and serialization remain additional.
No peak native-memory, native deallocation, GC-root neutrality or observer-neutrality
claim. Production remains unchanged; no unnecessary new production work/memory.

## Admission and evidence integrity

Fresh preflight checked HEAD a892ebd3382473532f36e92c32ad47328a350935 and master
6f68e24e8ddac42b948da8fcc2d636c010751194, both remote refs, preparation closure19,
publication exact39 committed names/blobs, full4744 preparation pins and all204
prior groups AND sessions/noJulia. Independent exact-stage review passed28checks,
rehashing4747 sealed entries and binding exactly4748 admission paths. Launch4749
pins include the sealed manifest and actual admission. The reviewed45second outer
limit/39second guard deadline and one-attempt reservation were used unchanged.

Six resource samples plus terminal sample: minimum available RAM22211864KiB,
maximum swap0. Inclusive6.7954s includes harness/import/compilation and is NOT a
kernel benchmark. Runner PID/PGID/SID192340 start_ticks11148988, child192341
start_ticks11149027, boot284d2228-1d9a-4c5f-913c-b9f1098b5838. All206 groups AND
sessions, including both new groups, are absent afterward; no Julia remains.
The recorded child command is the wrapper launch identity, not a separate claim
about every transient runtime loader choice. Source/runtime/command pins do not
prove observer neutrality or complete hidden native/import work.

Canonical audit ran once,12/12 integrity gates PASS, all18 residual outcomes
preserved. New post-exit supplement10checks PASS verifies full4749 pins, actual
baseline514, audit bindings, process closure and byte-identical portable8files.
New interpretation10checks PASS reads saved records only. Postcheck/interpretation
are separately source/hash-bound supplements, not retroactive launch pins; no
canonical auditor or numerical rerun. Independent result review follows before
publication. Original preparation selector failure and all older failures remain.

## Preservation and continuation

Evidence: results/DIRECT-LU-BACKEND-DIAGNOSTIC; actual invocation/admission/audit/
output paths remain in DIRECT-LU-BACKEND-PREPARATION as prospectively frozen.
Only new probe-* files were added there; all earlier preparation scripts/pins/
checks/reviews remain unchanged. This allowance is CONSUMED. No second attempt,
cost2, production repair, candidate tuning or automatic promotion is admitted.

The diagnostic plan's bounded evidence objective is met. Native root cause and a
safe repair remain unresolved; any proposed repair needs a separate concrete
plan and review. The existing captured factor/solution/source evidence can be
used for a bounded offline analysis without repeating this run. Preserve prior
preparation closure/publication current STATUS/roadmap bindings via the new
before-probe copies; all earlier mappings stay. CIoff, HHreuse disabled, automation
paused, broader optimization/fullsuite plan OPEN, master unchanged.
