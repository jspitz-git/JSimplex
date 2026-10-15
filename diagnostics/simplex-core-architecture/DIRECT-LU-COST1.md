# Direct LU Task 3: first cost process stopped on reference residual

Decision: numerical/cost qualification NOT ACCEPTED. One independently admitted
cost1 process was executed once; its reservation is CONSUMED. No rerun, tuning,
threshold change or cost2 launch. Cost2 is blocked by the existing predecessor
gate. The canonical false audit, exit2, raw and all partial records are preserved.
This report's independent review accepts only the diagnostic disposition if stated
by its companion review, never a successful cost qualification.

## Outcome and exact failure

HEAD at launch40d520eaf6bff7f0174192213e9cfed0652dc28c; master unchanged
6f68e24e8ddac42b948da8fcc2d636c010751194. Fresh independent stage review bound
4708paths to4707sealed inventory entries. Launch inventory4709; all pins unchanged.
Actual loaded overlay matches the approved path. No production/test/env/CI changes.

The process returned exit2 after12.816527476seconds inclusive, without timeout,
forced kill or cleanup error. It wrote241 completed lifecycle windows,12 complete
cells and the13th start marker. All12 completed cells are n32 (sparse/dense x
FT/SS/BG xnative/Markowitz). There are168 measured windows (84pairs), all with
zero measured compile/recompile and zero in-window GC. No second process ran.
The inclusive duration is not a performance metric.

Cell13 is sparse96 / Forrest–Tomlin / native / ordinary REFERENCE, pair1/order1,
warm not measured. Candidate sparse96 was never started. Input tokens unchanged
and modes ordinary/ordinary/ordinary pass; the residual component fails. New exact
posthoc arithmetic on the saved outputs confirms four DSE FTRAN residual failures,
steps5–8, after the first scheduled refactor. Each has worst row87 and signed
residual9928545/144115188075855872 (about6.8893e-11), exceeding the frozen bound
144694209253234815/39614081257132168796771975168 (about3.6526e-12) by
181942511239954432/9646280616882321 =18.8614159660 times. Entering FTRAN and BTRAN
outputs in the failed window pass, as do DSE outputs in steps1–4.

The standalone new partial-analysis.py checked all5784saved output vectors:
5780pass,4fail. All5760 outputs from the12complete cells pass exactly. This is an
additional preserved-data analysis, not a rerun or retroactive PASS for the
canonical auditor. Raw correctness flags agree with the exact analysis. Canonical
cost1-audit.json remains all_passed=false/complete=false with Missing phase evidence,
as expected for the stopped schedule. Neither its source nor output was rewritten.

Temporal localization after refactor is established; the specific internal source
operation responsible is NOT. The raw records contain detached solutions, not
LU factors, prepared-cache state or an internal arithmetic trace. No claim of
historical CI cause, a general solver defect or a direct-candidate failure follows.
No tolerance relaxation, forced precision, fixture change or retry is justified.

## Descriptive partial costs only

Each row below uses the seven measured pairs of the first process only. Time is
the median of paired candidate/reference whole-lifecycle ratios; other columns
are candidate/reference side medians. Retained is the final reachable Julia graph
after refactor2, not native live/peak memory. Full individual ratios/MAD/ranges,
bytes/events and raw component durations remain in preserved data. No pooling
across managers and no two-process acceptance is made.

| Fixture | Manager | Backend | Time ratio | Bytes ratio | Events ratio | Retained ratio |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| sparse32 | FT | native | 1.1850 | 1.3251 | 2.6186 | 0.3886 |
| sparse32 | FT | markowitz | 1.4659 | 2.8529 | 2.5497 | 0.1453 |
| sparse32 | SS | native | 1.0996 | 1.3133 | 2.4009 | 0.3680 |
| sparse32 | SS | markowitz | 1.4420 | 2.7960 | 2.4829 | 0.1423 |
| sparse32 | BG | native | 1.3392 | 1.4108 | 2.4406 | 0.4201 |
| sparse32 | BG | markowitz | 1.6016 | 2.9772 | 2.4955 | 0.1701 |
| dense32 | FT | native | 1.4369 | 1.4274 | 2.4552 | 0.4659 |
| dense32 | FT | markowitz | 2.0086 | 8.3131 | 3.4980 | 0.7041 |
| dense32 | SS | native | 1.4181 | 1.4224 | 2.2434 | 0.4538 |
| dense32 | SS | markowitz | 2.1320 | 7.9277 | 3.0210 | 0.6769 |
| dense32 | BG | native | 1.7378 | 1.4947 | 2.5386 | 0.4771 |
| dense32 | BG | markowitz | 2.9168 | 8.3012 | 3.3392 | 0.6987 |

Every completed cell has a slower median and increased median allocation bytes
and events, already failing necessary first-process cost conditions. The smaller
final reachable graph does not compensate under the fixed selection rules. These
are partial, instrumented, tiny n32 results with order/noise uncertainty; no
universal/end-to-end claim. The required reversed-order process and n96 comparison
are absent. Native direct still omits UMFPACK combined-solve refinement.

## Work, resources and evidence limits

241 returned whole lifecycles imply source-derived241initial constructions,
1928updates,3856FTRAN,1928BTRAN and482explicit refactors. There are121reference
and120candidate windows. Candidate construction/export entries360, up to180native
orientation solves additional. These are source-derived completed-call counts,
not instrumented backend/native attempt counts or complete import work.
The failure happens during detached validation after the whole lifecycle returned;
no additional Julia numerical experiment or solve was made for this diagnosis.

Twelve resource samples plus terminal sample: minimum availableRAM22,081,896KiB,
swap0. Fresh supplemental process check covers204groups ANDsessions, all
absent/noJulia, boot/ref identity and all514baseline files unchanged. Eleven new
supplemental integrity checks pass; these do not change the failed qualification.
postcheck.py is supplemental and not a launch pin. Partial-analysis.py and its
exact arithmetic are also new postexit evidence, not historical launch inputs.

No new production computational work or memory was introduced. Candidate setup/
refactor still pays owned export, validation, normalization, packing and complete
replacement-manager construction, losing ordinary spare/buffer reuse; all are
inside the measured window. No new per-solve production scans/copies. Harness
nested timers and mode reads remain charged identically. Deferred duplicate
post-window input scans and unused per-cell record retention remain frozen and
can affect outer allocations/GC/process budget. Detached outputs, exact posthoc
oracles and serialization are diagnostic work, not native-memory or neutral-
instrumentation proof. All raw outliers and in-window GC fields are preserved.

## Continuation

Next concrete work, if requested: bounded SOURCE/saved-evidence diagnosis of the
ordinary sparse96 FT/native DSE residual after its first refactor, without numerical
replay, performance tuning, changed tolerances or automatic candidate promotion.
A subsequent numerical attempt requires a separate frozen admission; this attempt
and its failed canonical audit never become reusable permission. Cost2 cannot
proceed under the existing gate. Original Task1–2 correctness remains scoped to
its earlier fixtures and unchanged evidence; the broader programme remains open.

Current preparation closure/publication STATUS/roadmap bindings map only to the
new before-cost1 copies (four mappings); the stage review's textual current STATUS
hash resolves there too. All older mappings, before copies and failed evidence
remain unchanged. CIoff, automationpaused, HHreuse disabled, user files preserved.
