# Process-local prototype: observe an existing reduction; reset only after commit.
mutable struct QualityState
    iteration::Int
    refactors::Int
    phase::UInt
    epoch::Int
    observed_epoch::Int
    leaving::Int
    requested::Bool
end
QualityState() = QualityState(-1,-1,0,0,-1,0,false)
const quality_states = WeakKeyDict{Any,QualityState}()
const quality_counts = zeros(Int,9)
const count_names = ("observations","bad_ratios","invalid_operands","eligible_proposals",
                     "resets","discarded","staged_skipped","framework_resets","blocked_authority")
quality_counts_report() = Dict(count_names[i]=>quality_counts[i] for i in eachindex(count_names))
quality_state(ws) = get!(() -> QualityState(),quality_states,ws)
function invalidate_quality!(ws)
    s=get(quality_states,ws,nothing)
    if !isnothing(s) && s.iteration>=0
        quality_counts[6]+=1
        s.iteration=-1; s.requested=false
    end
    return nothing
end
function quality_bad(stored::Float64, computed::Float64)
    isfinite(stored) && stored>0 && isfinite(computed) && computed>0 || return false
    # A bounded ratio avoids overflow for otherwise valid operands.
    return min(stored,computed)/max(stored,computed) < 1.0/9.0
end
function quality_context(ws)
    return ws isa JS.SimplexWorkspace{Float64} && ws.factorization isa Factor &&
        ws.options.algorithm==:dual && ws.options.pricing==:devex &&
        ws.options.simplex_strategy==:legacy && JS._weight_pricing(ws,:dual)==:devex
end
function reset_arrays_safe(ws)
    a=ws.pricing_weights
    for b in (ws.primal,ws.costs,ws.reduced_costs,ws.problem.A.nzval,ws.problem.objective,
              ws.scratch.rho,ws.scratch.tableau_row,ws.scratch.row_solution,ws.scratch.tau,
              ws.scratch.row_rhs,ws.scratch.pricing_row,ws.scratch.ratio_steps,ws.scratch.ratio_gains)
        Base.mightalias(a,b) && return false
    end
    return !Base.mightalias(ws.devex_reference,ws.scratch.basic_mask) &&
           !Base.mightalias(ws.devex_reference,ws.scratch.steepest_valid)
end
# Audit methods add independent work; plain methods are no-ops.
quality_observed(ws, raw, stored, computed, bad, tableau_row) = nothing
quality_reset_observed(ws) = nothing
function observe_reference!(ws,raw,tableau_row=ws.scratch.tableau_row)
    mode=="off" && return nothing
    quality_context(ws) || return nothing
    if JS._is_staged_workspace(ws)
        quality_counts[7]+=1
        return nothing
    end
    s=quality_state(ws)
    s.iteration=-1; s.requested=false
    row=ws.scratch.selected_row
    1<=row<=length(ws.basis.basic_indices) || return nothing
    leaving=ws.basis.basic_indices[row]
    stored=ws.pricing_weights[leaving]
    computed=max(1.0,raw)
    quality_counts[1]+=1
    valid=isfinite(raw) && raw>=0 && isfinite(stored) && stored>0
    bad=valid && quality_bad(stored,computed)
    valid || (quality_counts[3]+=1)
    bad && (quality_counts[2]+=1)
    s.iteration=ws.iterations; s.refactors=ws.refactorizations
    s.phase=ws.scratch.phase_generation; s.observed_epoch=s.epoch
    s.leaving=leaving; s.requested=bad
    quality_observed(ws,raw,stored,computed,bad,tableau_row)
    return nothing
end
function after_framework_reset!(ws)
    quality_context(ws) && !JS._is_staged_workspace(ws) || return nothing
    s=quality_state(ws)
    invalidate_quality!(ws)
    s.epoch+=1
    quality_counts[8]+=1
    return nothing
end
function finish_quality!(ws,result,stop,changed_index)
    mode=="off" && return result
    s=get(quality_states,ws,nothing)
    isnothing(s) && return result
    pending=s.iteration>=0
    matched=pending && isnothing(result) && !JS._is_staged_workspace(ws) &&
        changed_index>0 && changed_index==s.leaving && ws.iterations==s.iteration+1 &&
        ws.refactorizations==s.refactors && ws.scratch.phase_generation==s.phase &&
        s.epoch==s.observed_epoch && quality_context(ws)
    requested=s.requested
    s.iteration=-1; s.requested=false
    if !matched
        pending && (quality_counts[6]+=1)
        return result
    end
    requested || return result
    if !JS._can_reuse_dual_checks(ws,stop) || !reset_arrays_safe(ws)
        quality_counts[9]+=1
        return result
    end
    quality_counts[4]+=1
    if mode=="active"
        JS.reset_devex!(ws)
        quality_counts[5]+=1
        # Keep full validation after changing the pricing state.
        JS._finite_workspace(ws) || return JS._numerical_failure()
        quality_reset_observed(ws)
    end
    return result
end
function install_quality!()
    mode=="off" && return
    install_method("update_devex!",(
        "    entering_weight = max(one(T), reference_weight / pivot^2)"=>
        "    Main.observe_reference!(workspace,reference_weight,tableau_row)\n    entering_weight = max(one(T), reference_weight / pivot^2)",))
    install_method("reset_devex!";file="simplex",transform=expr->begin
        body=expr.args[2]
        expr.args[2]=quote
            local value=(()->begin $body end)()
            Main.after_framework_reset!(workspace)
            return value
        end
        expr
    end)
    install_method("_retry_simplex_step!";file="simplex_pivot",transform=expr->begin
        body=expr.args[2]
        expr.args[2]=quote
            Main.invalidate_quality!(ws)
            $body
        end
        expr
    end)
    install_method("_dual_after_iteration!";transform=expr->begin
        body=expr.args[2]
        expr.args[2]=quote
            local value
            try
                value=(()->begin $body end)()
            catch
                Main.invalidate_quality!(workspace)
                rethrow()
            end
            return Main.finish_quality!(workspace,value,stop_requested,changed_primal_index)
        end
        expr
    end)
end
function reset_quality!()
    empty!(quality_states);fill!(quality_counts,0)
end
install_quality!()
