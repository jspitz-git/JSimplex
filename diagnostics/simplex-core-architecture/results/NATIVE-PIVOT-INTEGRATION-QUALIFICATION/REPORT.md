# Native pivot integration: first attempt timed out

The independently admitted ONE<=60s Task3 integration attempt is FAILED and its
allowance is CONSUMED. It is not accepted for numerical qualification or production
promotion. No retry, additional warmup, longer run, modified tests or Julia query
was performed. Original raw/process/seal/admission/audit evidence is immutable.

The inner guard records wall_time, child returncode-9, elapsed_including_launch
52.504130901s. Outer supervisor records soft_timeout=true, hard_timeout=false,
guard_term=true, accepted=false; complete launcher duration56.128167785s is within
the inclusive60s cap. The inner52.504130901s value is recorded before termination
cleanup; only the outer56.128167785s duration includes termination. Both include
startup/import and any compilation reached; neither is a performance measurement.
The supplied process identifiers are runner
283004/start_ticks17890497/PGID+SID283004 and child283006/start_ticks17890547/
PGID+SID283006, boot284d2228-1d9a-4c5f-913c-b9f1098b5838. Fresh post-exit218groups
ANDsessions are absent, noJulia by comm/readable executable; inaccessible system
exe links remain a visibility limit.

Five original output files exist: pins.json,current.json,process.json,resources.jsonl,
run.log. raw.toml is ABSENT. Original audit all_passed=false with
RuntimeError('Exact output membership') is correct fail-closed behavior, not a
successful numerical result or an auditor defect. The expected162 assertions,
9case outcomes, policy/control checks and selected work totals are UNKNOWN from
this attempt; do not infer zero work or partial passes from absent completed raw.
The prepared postcheck.py remains UNEXECUTED because it expected complete raw;
separate timeout-postcheck.py handles failure preservation without rerunning audit.

The termination log shows LLVM optimization/JIT frames, jl_compile_codeinst and
public_case at observed-tests.jl:20 (the public solve call), then the scoped Test
include. That locates the interrupted stack; it does not measure total compilation
share, identify the current manager/policy, establish all earlier cases, isolate a
specific compiler/observer cause or prove a solver/numerical defect. Compiler and
Test overhead must not be presented as steady-state solver performance.

53 resource samples have minimum availableRAM21,169,564KiB, maximum swap0;
terminal availableRAM23,246,864KiB/swap0. Child resident highwater1,887,136KiB is
observed whole-process RSS, not native factor memory or Julia allocations. Guard
reason is time; stored memory samples satisfy the unchanged guards. No allocation
or kernel-cost comparison can be made from this interrupted qualification.

Fresh exact-stage admission passed53checks,1643sealedinputs/1644reviewbindings;
launch1646pins and76stagefiles retained. New timeout-postcheck23preservationchecks
pass: all current hashes/resolved identities, boot/command/reservation/linkage,
source520baseline and process closure verified. These PASS records are diagnostic
integrity ONLY, never a replacement for the failed numerical acceptance. No actual
production/test/envsettings/master changes, no unnecessary NEW production work or
memory; unchanged bounded diagnostic overhead remains in original driver contract.

Independent fresh gpt-6-astra result review is required before publication. Next
work may only use saved evidence/source to design a separately reviewed bounded
integration arrangement; do not repeat this attempt, extend its deadline, drop
assertions, prewarm off-budget or change compiler settings under this admission.
Any new numerical attempt needs its own concrete accepted driver/admission and
fresh host/environment/seal under standing short-run authorization. Task3 and
production promotion remain open. CIoff,HHreuse disabled,automationpaused; all old
failed/rejected results, outliers and consumed attempts stay preserved.
