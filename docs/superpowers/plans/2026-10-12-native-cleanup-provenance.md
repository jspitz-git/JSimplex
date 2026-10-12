# S6-AL: one native cleanup termination provenance lifecycle

Diagnostic only, prerequisite reviewed S6-AK. No permanent test/production/CI change.
One NEW Float64/PFI lifecycle, not an old driver or full-file rerun. Historical
three failures remain unchanged. No timeout fix, clock reset, warmup, longer limit,
tolerance/precision/backend adjustment, adapter or observer.

1. Mandatory fresh host refs/process check (boot/start_ticks/command), source/runtime/
   environment/user/input/policy hashes. Pin actual helper shifted_primal_workspace,
   primal_stalled_monitor and target test body; extract definitions without executing
   neighboring testsets. Verify exact default options: primal/native/PFI, iteration20,
   time30, tolerances1e-7/1e-7/1e-12; adaptive setup with refactor_timing=false and
   native replacement NumericalPolicy(Float64), unchanged. Record precision/rounding,
   threads and both policies as values; no inferred policy equality from endpoint.
2. Budget exactly ONE helper invocation (real initialization/refactor/recompute/bound
   perturbation), ONE initial _primal_optimize!(ws,()->false), ONE run_from_basis!
   after the existing policy replacement and one SimplexRunBudget constructor.
   No solve(problem), extra iteration, component/factor/quality/certificate call,
   negative deadline control, trial workspace or additional manager/scalar. Count
   these driver entries before calls; internal production calls are not entrycounts.
3. Keep original observer=nothing. After real helper setup enable only existing
   diagnostics.kernel_timing=true; separate setup history/counters from initial
   optimizer and cleanup driver windows. Kernel counts cover attempts even on throws
   through production finally; no adapter or intercepted solve. Setup kernel totals
   were disabled and are NOT inferred from zero counters. This instrumentation and
   snapshot work consume the same30second budget and are not proved timing-neutral.
4. Capture owned tiny state at helper return, after initial optimize, before driver
   and immediately after driver: original model/bounds, working bounds/point/costs/
   prices/rho/basis/states, journal owner-match/activity and original/active values,
   diagnostics events/counts/kernels, options/policies, progress and budget start_ns,
   time limits/iterations/refactors/offsets. Record monotonic clock brackets around
   each call and distinguish capture duration from numerical window. No callback
   solves/refactors/certificates, no opaque pointer decoding. Serialize only after
   the final window. Do not insert hidden numerical precompilation or duplicatecall.
5. Preserve all six original test predicates plus helper shifted==1. Save actual
   initial terminal and final run status/message/objective/primal/basis or exception
   before assertions; raw must survive a failed oracle. Added gates: same owner and
   original-model bits, unchanged policy/tolerance/clock ownership; source/driver/
   process/exit/pins/globals and truthful complete call budgets. No invented success
   gate accepting a failure. Countedwork/events are observations; a pass does not
   identify historical CI cause or prove observer neutrality.
6. Offline audit actual returned values first. If before_call-start>=30seconds,
   entry expiration is supported; if after_call-start<30seconds, no deadline expiry
   in that bracket under the monotonic-clock assumption. A straddling bracket is
   ambiguous. Status/message identify a returned path class, not its exact internal
   clock check. Inspect restoration and finalcert events separately from returned
   status. Exact rational equations use actual captured bits, not substituted AK
   vectors. Unexpected work/result remains preserved; no retry/matrix scan.
7. Existing guard: one numerical Julia/BLAS1, heap2GiB,VM8GiB,minavailableRAM6GiB,
   maxswap1GiB; prohibited big/largo/AnyMOD and aliases. Separate host absence check
   immediately before launch. Freeze all src/test/env/diagnosticJulia files until
   process exit; verify process.json, exit, independent pins, actual source, raw/
   portable equality and proper new audit. Exit0 alone is not acceptance.
8. Fresh independent numerical/work/memory review. Only then decide the next bounded
   causal experiment or repair plan; no permanent RED/GREEN or master change here.
   Do not rerun accepted S5-C/S6-AJ/AK or historical H/I/J/X–AI/corpus/reference/cost.
   No CI dispatch; historical failures and S2-A/S6-J/wholeAF rejection preserved.
