from pathlib import Path
import json,shutil,hashlib
W=Path('/home/jspitz/.codex/worktrees/dual-step-experiment/JSimplex.jl');D=W/'diagnostics/dual-step-experiment/measurement';old=D.parent/'task5';D.mkdir()
for name in ('guard','project'):(D/name).mkdir()
for name in ('guard_reviewed.py','entry_gate.py','supervisor_reviewed.py'):shutil.copyfile(old/'guard'/name,D/'guard'/name)
for name in ('Project.toml','Manifest.toml'):shutil.copyfile(old/'project'/name,D/'project'/name)
(D/'project/src').symlink_to(W/'src',target_is_directory=True)
shutil.copyfile('/tmp/task6-host.json',D/'host.json');shutil.copyfile('/tmp/task6-driver.jl',D/'driver.jl')
raw=(W/'experimental/dual_engine/driver.jl').read_text();start=raw.index('function (adapter::PhaseAdapter)');end=raw.index('"""Opt-in complete solve;',start);original=raw[start:end]
body=original.replace('adapter::PhaseAdapter','adapter::Task6Adapter')
body=body.replace('    monitor=_EventMonitor(', '    _task6_capture!(adapter.probe,e,"setup")\n    monitor=_EventMonitor(')
body=body.replace('        _snapshot_counts!(r,e)','        _task6_capture!(adapter.probe,e,"exit")\n        _snapshot_counts!(r,e)')
notice=raw[raw.index('function J._dual_engine_notice!(adapter::PhaseAdapter'):start].replace('adapter::PhaseAdapter','adapter::Task6Adapter')
prefix='''# Diagnostic-only nominal adapter; no existing method is replaced.
# The primary timed arm uses the original E.solve_experimental, never this clone.
@eval E begin
mutable struct Task6Adapter{C,F}
    record::SolveRecord
    clock::C
    events::F
    entered::Bool
    probe::Dict{String,Any}
end
function _task6_capture!(probe,e,label)
    data=Dict{String,Any}("graph_bytes"=>Base.summarysize(e),"m"=>length(e.ws.basis.basic_indices),"N"=>length(e.ws.costs))
    for k in fieldnames(ProposalCounts);data["PC_"*string(k)]=getfield(e.proposal.counts,k);end
    seen=Base.IdSet{Any}();memories=Base.IdSet{Any}()
    function visit(x,path)
        x in seen&&return
        push!(seen,x)
        if x isa Vector
            memory=getfield(getfield(x,:ref),:mem)
            data[path*"_length"]=length(x);data[path*"_capacity"]=length(memory)
            if !(memory in memories)
                push!(memories,memory)
                data["unique_vector_payload_bytes"]=get(data,"unique_vector_payload_bytes",0)+length(memory)*Base.elsize(x)
            end
        elseif x isa Tuple
            for i in eachindex(x);visit(x[i],path*"_"*string(i));end
        elseif !(x isa Number||x isa Symbol||x isa AbstractString||x isa Function||x isa AbstractArray||x isa AbstractDict||x isa Module||x isa Ptr||x===nothing)
            for k in fieldnames(typeof(x));visit(getfield(x,k),path*"_"*string(k));end
        end
    end
    for k in (:proposal,:journal,:invariants,:supports,:kernels,:recovery,:residual_scale,:rows);visit(getfield(e,k),string(k));end
    for k in (:costs,:lower,:upper,:basis,:primal,:reduced_costs,:pricing_weights,:devex_reference,:scratch);visit(getfield(e.ws,k),"ws_"*string(k));end
    probe[label]=data
    nothing
end
'''
(D/'inspection.jl').write_text(prefix+notice+body+'end\n')
restored=body.replace('adapter::Task6Adapter','adapter::PhaseAdapter').replace('    _task6_capture!(adapter.probe,e,"setup")\n','').replace('        _task6_capture!(adapter.probe,e,"exit")\n','')
if restored!=original:raise ValueError('exact diagnostic adapter inverse')
(D/'inspection-inverse.json').write_text(json.dumps(dict(accepted=True,source=str(W/'experimental/dual_engine/driver.jl'),source_sha256=hashlib.sha256(raw.encode()).hexdigest(),exact_method_inverse=True,changes=['own nominal type','one setup and one exit read-only capture'],scope='cold qualification only, never primary measured arm'),indent=2))
runtime=json.loads((old/'runtime.json').read_text());runtime['experiment']=json.loads((D/'host.json').read_text())['experiment'];runtime['julia_flags']=[x.replace(str(old/'project'),str(D/'project')) for x in runtime['julia_flags']];(D/'runtime.json').write_text(json.dumps(runtime,indent=2))
(D/'README.md').write_text('''# Task6 whole-solve comparison admission

Only same-policy Float64/native PFI/fixed Devex is admitted here.16 fixed Task5 cases: n16/n64 sparse/dense plus the six specified MPS files with presolve false/true. No implementation, tolerance, native-control, coefficient or precision change. Qualification precedes comparison and separately matches instrumented reference and cold inspection outcomes/counters to their ordinary counterparts. The copied PhaseAdapter method has an exact inverse apart from its own nominal type and two read-only setup/exit captures; no existing method is replaced. Actual vector logical lengths/backing Memory capacities and Julia reachable graph sizes are cold diagnostics, not hidden native memory or peak/free accounting. Proposal counts are cold-qualified; primary E retains its existing Engine/Kernel/Recovery counters in every solve. Residual row-check interior terms, legacy scans and backend-private work remain source-attributed/uninstrumented, never silently zero.

Qualification:16x4 whole solves(reference/public, reference/counts, E, diagnostic E)+2 genuine infeasible boundary solves. All16 complete optimal outcomes/model immutability/original feasibility/objective and instrument neutrality required; four designated cases require real E commits/no whole-phase fallback or outer cleanup/retry/recovery. The infeasible fallback has zero commits and is never a speed result.

Comparison: exactly two warm complete solves per arm and five interleaved measured pairs on every case; rotate order each pair.224 solves total:64warm+160measured. One explicit full GC after each case's four warm solves is separately recorded; natural measured GC/outliers remain. Entire public reference J.solve versus ordinary E.solve_experimental, observer nothing, kernel timing false, immutable event sink NoEvents. E's mandatory bounded diagnostics/output/minimal counters are intrinsic included costs; reference timing is uninstrumented public solve. Separate reference counts use kernel_timing true only in qualification; no observer mutation. No DSE-versus-Devex algorithm-policy claim. Each window includes all solve setup/import/index/factor/copies, accepted and rejected steps, fallback/cleanup/original certification. Input generation/deepcopy, external verification and record formatting are outside solve windows and reported separately. Each arm creates its own record/solution; at most current solve results and one current input/snapshot are held. No growing vector snapshots or engine graphs after a solve. Allocated bytes/events are GC traffic, not live/native memory. Record retained Julia size and sampled RSS/HWM separately. Both warm and measured scalar records survive failed tests; ordinary Test only.

Each qualification/comparison admission has its own fresh common1800second reservation including loading, warmup, all solves, output and final checks. Existing global lock/one Julia/BLAS1, heap2GiB hint/VM8GiB/availableRAM6GiB/swap1GiB, full historic PGID ANDsession and boot/start/command guards apply. Project/Manifest are unchanged copies with strictly checked real source directory alias; offline compiled-modules/pkgimages existing. Original plan, Tasks1–5 and all old scripts/raw stay frozen.

Saved runtime/fast0507 history tapes contain bases/update sequences, not a short qualified complete fixed-Devex/PFI solve. Source-bound short whole-solve schedule for these larger original inputs is not established. They are excluded under Task6's explicit viability condition; no kernel/tape speed is substituted, no claim about large-model total speed. The16 small cases alone cannot settle the user-reported order-of-magnitude gap. No automatic tuning/calibration or production promotion. Result review will decide whether any later proposal is justified; this task also publishes the authorized experiment branch, never master.
''')
with (W/'.superpowers/sdd/2026-10-31-experimental-dual-engine/progress.md').open('a') as f:f.write('\nTask6 BASE0a06785c; fresh816PGIDANDsessions/boot/currentrefs/noJulia before changes; existingisolatedbranchverified. Scope Task6 same-policy complete-solvecost, then user-explicit push experimentalbranch only. Ruling: instrumented reference and exactinverse nominal phase-adapter inspection are qualification-only; primary timed reference publicsolve and original E unchanged, allmandatoryEcountercostincluded. Coldsetup/exitgraph/capacity walks are not repeated in timedarm. Costs ifwrong: qualification instrumentation notprovenneutral triggersfailure, no performanceinterpretation. Ruling:16fixedsmallcases; runtime/fast0507 savedhistorytapes are component inputs, not a source-bound short whole-solve schedule; excludeconditionally, no large-modelspeedclaim. Twoarms x(2warm+5measure)x16=224 complete timedsolves; qualification66calls; eachseparatecommon1800s. NoTask1–5/production/env/CIchanges.\n')
print('Task6 driver/inspection/stage prepared',D)
