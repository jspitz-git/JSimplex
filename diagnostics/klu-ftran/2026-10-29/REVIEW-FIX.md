# Bounded offline admission corrections

Original43 source bindings remain frozen. Their candidate.jl, PLAN.md and driver.jl keys map ONLY to candidate.jl.before-review, PLAN.md.before-review and driver.jl.before-review. All other original bindings remain live and unchanged. No Julia was run.

1. Independent Important work finding: full CSC control cleared n work values immediately before overwriting all n during scaling/gather. Move fill! exclusively to local branch; full control now avoids that redundant full-vector store pass.
2. Root prelaunch constructor check: pass explicit UInt32(0) epoch to parametric GraphContext constructor, matching its declared field instead of relying on Int conversion at inferred outer constructor.
3. Correct plan wording: only L/U are sorted by extraction; F order remains native extraction order and is identical in local/full controls.
4. Clarify exported-only counters; native routes0 do not imply no native work, and budget fallback includes both sunk exported work and native solve.

5. Add three cold microchecks: eligible-context dense-column fallback path3, its exact native output match, and unknown-support destination/private-work alias rejection. No old numerical expectation is changed; no new measured case.

No original numerical expectations, eligibility thresholds, inputs, controls, measured schedule or guards changed. New verify.py is a prospective offline auditor, not in the original43 source bindings; final launch manifest will bind it.
