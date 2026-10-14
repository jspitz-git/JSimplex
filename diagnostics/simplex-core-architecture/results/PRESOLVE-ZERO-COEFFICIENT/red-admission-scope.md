# Missing-zero conversion RED admission

User approved the concrete sparse-equality optimization and short numerical attempts.
This first stage runs ONE tiny Float64 model only, before any candidate code exists.
The full original aggregate function is copied with ONLY its function name and the
single missing-entry exact conversion redirected to a forwarding counter. No method
is overwritten. The counter forwards identical conversion; it is outside performance
measurement and never production. Input: 2x+3y=4,4x<=20, free x/y, cost2y+7.
Expected exact reduced coefficient -6 and upper12, source preserved; exactly one
missing zero conversion in current code. The work test demands zero and must FAIL
(exit1, two preservation/correctness passes and one work failure). This is an actual
forwarded-work test, not a source-text RED or solver defect. Save raw before assertion.

One guard114s / inclusive supervisor120s, one Julia/BLAS1, existing compiled modules,
heap2GiB hint/VM8GiB/availableRAM6GiB/swap1GiB. No MPS input, solver, old auditor,
production/test/env changes, candidate or retry. Fresh full groups ORsessions and
pins before/after. Failure beyond the exact expected RED stops. Admission review
must bind every required config path and the pins SHA before launcher execution.
