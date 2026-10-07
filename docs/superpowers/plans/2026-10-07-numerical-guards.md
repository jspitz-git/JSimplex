# Numerical guard repairs before performance changes

Start from master3807f50 in codex/numerical-guard-repair. Implement sequentially;
commit each verified functional repair. No merge/push without a new instruction.
Keep native problem precision, tolerances and simplex candidate policy. Use one
Julia/BLAS process under the existing8GiBVM/RAM/swap guard. Retain prior experiments.

1. Reproduce greenbea dual originalBG/native80 with terminal snapshot observer.
   Separate primal feasibility, basic dual stationarity and complementarity
   rejection in the stored candidate. Test one native correction against the
   full certificate. Add a small failing regression before changing production.
   Relevant source: dual_simplex.jl, native_certificate_recovery.jl.
2. Reproduce pilotnov dualPFI/Markowitz80. Identify the precise failed condition
   of _stabilize_small_dual_pivot! before designing its native repair. Retain the
   amplified small-pivot accuracy requirement and all nonbasic price checks.
3. Reproduce directSS/fast0507 interval320 failure using preserved exchange tape.
   Probe exchanges561..640 and separate factor growth from solve/application
   error. Existing replay cannot pass by silently refactorizing early. Keep
   experimental factor comparisons isolated from production backend dispatch.
4. Only after numerical work, measure duplicate primal certificate activities.
   Reuse identical per-call activity enclosures and scratch without removing
   either model-bound or row-consistency validation. Add agreement/allocation
   checks, paired ordered decisions and original certificates before timing.

Each repair requires red/green unit evidence, appropriate semantic/corpus
regressions, original failing-case completion and independent review. Final
runtime dual verification must have at least300s budget. Carry forward known
master test failures explicitly; no claim of a passing entire project suite.
Diagnosis may revise a proposed repair, but not tolerances or acceptance criteria.
