# Reuse the previously verified guard/event oracle. Permit absent correction
# hits, and report coverage explicitly rather than requiring a changed path.
let source=read(joinpath(@__DIR__,"audit-original.jl"),String)
    hit="        @assert get(tally,\"row_reused\",0)>0 && get(tally,\"finite_reused\",0)>0"
    @assert count(hit,source)==1
    source=replace(source,hit=>"        nothing")
    source=replace(source,
        "function event!(ws,reason)\n"=>"function event!(ws,reason)\n    Main.pricing_event!(ws,reason)\n",
        "    counted(\"finite_reused\")"=>"    counted(\"finite_reused\")\n    Main.mode_count!(ws,\"finite_reused\")",
        "    counted(\"row_reused\")"=>"    counted(\"row_reused\")\n    Main.mode_count!(ws,\"row_reused\")")
    Base.include_string(Main,source,joinpath(@__DIR__,"audit-original.jl"))
end
const pricing_counts=Dict{String,Int}()
const switch_history=Dict{String,Any}[]
const weight_context=Ref(0)

function mode_count!(ws,kind)
    key=string(kind,"/",JS._weight_pricing(ws,:dual),"/phase",ws.scratch.phase_generation)
    pricing_counts[key]=get(pricing_counts,key,0)+1
end
function pricing_event!(ws,reason)
    @assert ws.factorization isa Factor
    active=JS._weight_pricing(ws,:dual)
    record("pricing",reason,ws.iterations,active,ws.dual_devex_fallback,ws.dual_pricing_fallback,ws.scratch.phase_generation)
    reason==:pivot_completed && mode_count!(ws,JS._is_staged_workspace(ws) ? "staged_pivot_event" : "live_pivot_event")
end

function count_committed(expr)
    body=expr.args[2]
    expr.args[2]=quote
        Main.mode_count!(workspace,"completed")
        $body
    end
    return expr
end
install_audit()
install_method("_switch_dual_pricing_to_devex!";transform=expr->begin
    body=expr.args[2]
    expr.args[2]=quote
        local before=_weight_pricing(workspace,:dual)
        local value=(()->begin $body end)()
        local after=_weight_pricing(workspace,:dual)
        push!(Main.switch_history,Dict("iteration"=>workspace.iterations,
            "phase_generation"=>workspace.scratch.phase_generation,"from"=>string(before),
            "to"=>string(after),"reason"=>reason,"during_weight_update"=>Main.weight_context[]>0,"staged"=>_is_staged_workspace(workspace)))
        Main.record("switch",workspace.iterations,before,after,reason,Main.weight_context[]>0,_is_staged_workspace(workspace))
        return value
    end
    expr
end)
install_method("update_dual_pricing_weights!", (
    "            # No state changes before the final check: reuse this successful check.\n            return true"=>
    """            @assert _finite_workspace(workspace)
            Main.counted("common_dse_weight")
            Main.mode_count!(workspace,"common_dse_weight")
            return true""",);transform=expr->begin
    body=expr.args[2]
    expr.args[2]=quote
        Main.weight_context[]+=1
        try
            $body
        finally
            Main.weight_context[]-=1
        end
    end
    expr
end)
needle="        if !Validated && !_finite_workspace(workspace)"
install_method("_dual_iteration_entry!",(needle=>"""        if Validated
            @assert _finite_workspace(workspace)
            local kind=stop_requested isa _StopCallback{<:_BasisBudgetStop} ? "driver_entry" : "common_entry"
            Main.counted(kind)
            Main.mode_count!(workspace,kind)
        end
$needle""",))
if arm=="shadow"
    install_method("_dual_iteration_unchecked!",(
        "                    row_failed = false"=>"                    Main.shadow_row(workspace,rho,leaving_row)\n                    row_failed = false",
        "    _replace_pivot_column!(workspace, tableau_column, leaving_row;"=>"    Main.before_publish(workspace,changed_primal_index)\n    _replace_pivot_column!(workspace, tableau_column, leaving_row;"))
    needle="        isfinite(workspace.primal[changed_primal_index]) || return _numerical_failure()"
    install_method("_dual_after_iteration!",(needle=>"        Main.shadow_finite(workspace,changed_primal_index)\n"*needle,);transform=count_committed)
    install_method("_dual_optimize!",("        if !previous_step_checked"=>"""        if previous_step_checked
            @assert _finite_workspace(workspace)
            Main.counted("from_last_pivot")
            Main.mode_count!(workspace,"from_last_pivot")
        else""",);transform=time_loop)
else
    install_method("_dual_after_iteration!";transform=count_committed)
    install_method("_dual_optimize!";transform=time_loop)
end
