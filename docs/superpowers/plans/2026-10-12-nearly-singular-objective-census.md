# S6-N: nearly singular bounded objective census

> **For agentic workers:** Use superpowers:executing-plans inline, sequentially.

Goal: explain the remaining original solver_tests.jl:552 objective equality failure
without weakening assertions, changing tolerances, or assuming platform roundoff.
Both historical CI runs report -1.7592186044416062e13 versus exact -2^44 in
"A nearly singular bounded model has no recession ray". The fixture has two free
columns and two bounded rows, matrix [s s; s nextfloat(s)] constructed in Float32,
s=2^-20, then converted to Float32/Float64/BigFloat/Rational{BigInt}.

- [ ] Reconcile existing recession/original-certificate and solver test evidence.
  Do not rerun accepted broad corpora or full solver file. Inventory exact CI
  expression/value and known scalar context; do not infer type from print alone.
- [ ] Derive exact stored-matrix determinant, strict optimum and bounds analytically
  using rationals. Separately account for configured original row/column/dual
  tolerance; distinguish strict optimum equality from valid returned certificate.
- [ ] Run one bounded four-type current-source census with unchanged constructors,
  original options and original assertions. Record exact returned primal/objective,
  status/message, options, original row residuals and certificate diagnostics only
  as necessary. Preserve any original oracle failures and return code. Verify
  source/pins, model preservation and no invalid solution/ray publication.
- [ ] If observed objective differs, identify which original feasibility/optimality
  conditions are met. A small relative gap alone is not an explanation or license
  to relax equality. No precision escalation to manufacture a pass. No production
  edit before evidence and a separate RED/GREEN implementation subplan.
- [ ] One final independent numerical/work/memory review, publish limits and next
  action. No actual x64 or full CI claim from local results; CI remains disabled.

Use one guarded Julia (Julia/BLAS1,heap2GiB,VM8GiB,availableRAM6GiB,swap1GiB), and
separate host previous runner/child/driver absence with boot/start_ticks/command
before launch/edits. Preserve user environments, raw failures and old worktrees.
No big/largo/AnyMOD or aliases; no repeats of accepted long/HH/scalar measurements.
