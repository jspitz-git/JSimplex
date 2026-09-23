# Internal diagnostics are opt-in and do not change public SolveStatistics.
const SIMPLEX_EVENT_REASONS = (
    :phase_primal, :phase_dual, :phase_one, :phase_auxiliary, :phase_cleanup,
    :pivot_proposed, :pivot_rejected, :pivot_completed, :flip_completed, :bound_flipped,
    :refactor_initial, :refactor_limit, :refactor_residual, :refactor_pivot,
    :refactor_cost, :refactor_growth, :refactor_fill,
    :stagnation_watch, :stagnation_stalled, :stagnation_fallback,
    :pricing_scanned_entries, :pricing_scored_entries, :pricing_full_scan,
    :pricing_block_scan, :pricing_pool_hit,
    :pricing_devex, :pricing_dantzig, :pricing_reset, :pricing_weight_rejected,
    :refactor_other, :correction_attempt, :correction, :pricing, :perturbation, :restore_perturbations,
    :certification, :certification_failed, :repair, :checkpoint, :restore_checkpoint,
    :feasibility_recovery, :precision_boost, :lp_refinement,
)

mutable struct SimplexDiagnostics{F}
    counts::Dict{Symbol,Int}
    events::Vector{Symbol}
    next_event::Int
    observer::F
    kernel_timing::Bool
    kernel_calls::Dict{Symbol,Int}
    kernel_nanoseconds::Dict{Symbol,UInt64}
end

function SimplexDiagnostics(; observer=nothing, kernel_timing::Bool=false)
    events = Symbol[]
    sizehint!(events, 64)
    return SimplexDiagnostics(Dict(reason => 0 for reason in SIMPLEX_EVENT_REASONS),
        events, 1, observer, kernel_timing,
        Dict(key => 0 for key in (:ftran, :btran, :pricing, :refactorization)),
        Dict(key => UInt64(0) for key in (:ftran, :btran, :pricing, :refactorization)))
end

@inline _diagnostic_kernel(f, ::Nothing, reason::Symbol) = f()
@inline function _diagnostic_kernel(f, diagnostics::SimplexDiagnostics, reason::Symbol)
    diagnostics.kernel_timing || return f()
    haskey(diagnostics.kernel_calls, reason) || throw(ArgumentError("Unknown timed kernel: $reason"))
    started = time_ns()
    try
        return f()
    finally
        diagnostics.kernel_nanoseconds[reason] += time_ns() - started
        diagnostics.kernel_calls[reason] += 1
    end
end

function record_event!(d::SimplexDiagnostics, reason::Symbol)::Nothing
    haskey(d.counts, reason) || throw(ArgumentError("Unknown simplex diagnostic event: $reason"))
    d.counts[reason] += 1
    if length(d.events) < 64
        push!(d.events, reason)
    else
        d.events[d.next_event] = reason
    end
    d.next_event = mod1(d.next_event + 1, 64)
    return nothing
end

event_count(d::SimplexDiagnostics, reason::Symbol)::Int = get(d.counts, reason, 0)

"""Return an owned, chronological copy of the bounded event history."""
function recent_events(d::SimplexDiagnostics)
    length(d.events) < 64 && return copy(d.events)
    return vcat(d.events[d.next_event:end], d.events[1:d.next_event-1])
end

_diagnostic_event!(::Nothing, reason::Symbol, state=nothing) = nothing
struct DiagnosticObserverFailure{E} <: Exception
    cause::E
end
Base.showerror(io::IO, failure::DiagnosticObserverFailure) =
    (print(io, "Diagnostic observer failed: "); showerror(io, failure.cause))

function _diagnostic_event!(d::SimplexDiagnostics, reason::Symbol, state=nothing)
    record_event!(d, reason)
    if !isnothing(d.observer)
        try
            d.observer(reason, state)
        catch exception
            # A recorder failure must not be caught as a singular numerical solve.
            throw(DiagnosticObserverFailure(exception))
        end
    end
    return nothing
end
