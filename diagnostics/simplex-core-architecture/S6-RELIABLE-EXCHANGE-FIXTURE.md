# S6-AA: exact reliable-exchange test fixture

Status: independently accepted and integrated; test f2e7647 -> master74f7835.
Base477ed88, prior masterb9e7cb1. Test-only change in native_phase_transfer_tests.jl.

The reliable zero-budget test now selects a separate identity6 helper qualified
by S6-Z. All four original assertions, manager loop, diagnostics, policy and options
are unchanged. Native roundoff helper and all neighboring testsets are byte-identical.
The new helper is the qualified construction with a distinct name, inserted before
the first testset; it does not execute until called. No adapters or diagnostic
records enter permanent test code. One call-site changes;24helper/comment lines added.

Both old and new original structural feasible sets are the singleton[1,1,0,0,0,0]
(old determinant31071), but equations, row activities and cancellation behavior
differ. The exact fixture isolates reliable reconstruction with zero correction
budget; it does not replace native reconstruction or cancellation coverage.

## Verification

- red-1: two expected structural failures; zero workspace/exchange/solve. Exit1
  retained, all15audit gates,621pins. This is structural RED, not old numerical replay.
- green-1:127/127:2structural+16target+108selected native cancellation/policy neighbor
  +1ambient state. Actual source extracted/executed without decision clones or fake
  quality. Exit0,17audit gates621pins;raw/portable/source/driver/user hashes verified.
- Same single Julia/BLAS1 guard,heap2GiB,VM8GiB,minRAM6GiB,maxswap1GiB. Native and target
  exchange count20 in this new-source gate, not old fullfile/corpus replay.
- Separate host runner402885/child402886/driver402858 absent after completion.

S6-Z supplies accepted exact point/basis/certificate and 5FTRAN/4BTRAN/2refactor
kernel counts with fresh export setup separate; it was not rerun after the change.
The current target deliberately retains its original four assertions.

## Computational work and scope

Production unchanged: no hot-path scan, solve, allocation, precision or memory cost.
Permanent target still performs four exchanges and the same original checks. Helper
adds a fixed6x6 identity construction at cold test setup; no extra permanent solves,
iterations, counters, snapshots or retained records. No benchmark/speedup claim.
Native helper duplication keeps its bytes and independent recovery intent intact.

Historical private export state/backend cause, the four scalar-unknown accepted=false
failures, actual x64/fullsuite and broader S6 remain open. No assertion/tolerance/
precision/safeguard/workflow weakening; CI disabled. No accepted X/Y/Z reruns.

## Integration closure

Fresh independent gpt-6-astra review: no Critical/Important/Minor findings and no
unnecessary work or retained memory. Actual-master master-1 passes19/19
(2structural+16target+1ambient),exit0,all18audit gates621pins. Actual source equals
accepted GREEN, raw/portable/driver/user hashes match; six supplementary checks.
Separate host runner403571/child403572/driver403563 absent,noJulia,
boot20de7dde-704e-41c8-bee7-b8511c0a86b0. Master push completed.
Next S6-AB begins with ownership/lifecycle preflight under its separate plan; no
component/old qualification rerun is authorized by this closure.
