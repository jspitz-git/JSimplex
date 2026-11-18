# Cache only the audited hardware-float legacy path. Unknown callbacks and
# observers may mutate state, so they must retain the original full traversal.
const _DUAL_INFEASIBILITY_LEGACY32 = NumericalPolicy(Float32; simplex_strategy=:legacy)
const _DUAL_INFEASIBILITY_LEGACY64 = NumericalPolicy(Float64; simplex_strategy=:legacy)

_dual_infeasibility_factor_supported(f, ::Type) = false
function _dual_infeasibility_factor_supported(f::HuangfuHallFactorization{T,F,R},
                                               ::Type{T}) where {T,F,R}
    R === :native && T in (Float32,Float64) && eltype(f.work) === T || return false
    return T === Float64 ? F === Float64UMFPACK : F <: LinearAlgebra.LU{Float32}
end
function _dual_infeasibility_factor_supported(f::Union{PFIFactorization,
        ForrestTomlinFactorization,SuhlSuhlFactorization,BartelsGolubFactorization},
        ::Type{T}) where T
    T in (Float32,Float64) && eltype(f.work) === T && isnothing(f.sparse) || return false
    return T === Float64 ?
        f.base isa UMFPACKBackend && f.base.pivot_policy === _NATIVE_PIVOT_DEFAULT :
        f.base isa Float32LUBackend && eltype(f.base.factorization.factors) === Float32
end

_dual_infeasibility_observer_safe(observer) = false
_dual_infeasibility_observer_safe(::Nothing) = true
function _dual_infeasibility_allowed(w::SimplexWorkspace{T}, stop) where T
    p = w.progress.numerical_policy
    return T in (Float32,Float64) && w.options.simplex_strategy === :legacy &&
        p === (T === Float32 ? _DUAL_INFEASIBILITY_LEGACY32 : _DUAL_INFEASIBILITY_LEGACY64) &&
        _dual_infeasibility_factor_supported(w.factorization,T) &&
        w.options.pricing in (:dantzig,:devex,:steepest_edge) &&
        !w.options.partial_pricing && !p.recovery && !p.pivot_validation &&
        !_is_staged_workspace(w) && _readonly_dual_stop(stop) &&
        (isnothing(w.progress.diagnostics) ||
         _dual_infeasibility_observer_safe(w.progress.diagnostics.observer))
end

@inline function _invalidate_dual_infeasibility!(w)
    c = w.scratch.dual_infeasibility
    isnothing(c) || (c.valid = false)
    return nothing
end

# Suspending nested/unsupported scopes also invalidates the outer values before
# restoring their authority. No arrays are allocated until the first cache use.
function _begin_dual_infeasibility!(w, stop)
    previous = w.scratch.dual_infeasibility_active
    w.scratch.dual_infeasibility_active = _dual_infeasibility_allowed(w, stop)
    _invalidate_dual_infeasibility!(w)
    return previous
end
function _end_dual_infeasibility!(w, previous::Bool)
    w.scratch.dual_infeasibility_active = previous
    _invalidate_dual_infeasibility!(w)
    return nothing
end

_dual_infeasibility_fingerprint(w) = (objectid(w.primal), objectid(w.lower),
    objectid(w.upper), objectid(w.basis.basic_indices), UInt(w.refactorizations))

@inline function _dual_infeasibility_row!(c, w, row, index)
    value = max(_lower_violation(w.lower[index], w.primal[index]),
                _upper_violation(w.upper[index], w.primal[index]))
    c.values[row] = value
    pos = c.positions[row]
    if value > w.options.primal_tolerance
        if pos == 0
            c.count += 1
            c.rows[c.count] = row
            c.positions[row] = c.count
        end
    elseif pos != 0
        tail = c.rows[c.count]
        c.rows[pos] = tail
        c.positions[tail] = pos
        c.positions[row] = 0
        c.count -= 1
    end
    return nothing
end

function _rebuild_dual_infeasibility!(c, w)
    fill!(c.positions, 0)
    c.count = 0
    for (row, index) in enumerate(w.basis.basic_indices)
        _dual_infeasibility_row!(c, w, row, index)
    end
    c.fingerprint = _dual_infeasibility_fingerprint(w)
    c.tolerance = w.options.primal_tolerance
    c.valid = true
    return c
end

function _current_dual_infeasibility!(w::SimplexWorkspace{T}) where T
    # Keep unsupported arithmetic statically on the original path, even when
    # inference cannot know the value of the mutable scope flag.
    T in (Float32,Float64) || return nothing
    w.scratch.dual_infeasibility_active || return nothing
    c = w.scratch.dual_infeasibility
    m = length(w.basis.basic_indices)
    if isnothing(c) || length(c.values) != m
        # Every element is initialized by rebuild before it can be observed.
        c = _DualInfeasibilityState(Vector{T}(undef,m), Vector{Int}(undef,m),
            Vector{Int}(undef,m), 0, false, _dual_infeasibility_fingerprint(w),
            w.options.primal_tolerance)
        w.scratch.dual_infeasibility = c
    end
    if !c.valid || c.fingerprint != _dual_infeasibility_fingerprint(w) ||
       c.tolerance != w.options.primal_tolerance
        _rebuild_dual_infeasibility!(c, w)
    end
    return c
end

@inline _dual_infeasibility_changed!(::Nothing, w, row, index, old) = nothing
@inline function _dual_infeasibility_changed!(c::_DualInfeasibilityState, w, row, index, old)
    isequal(old, w.primal[index]) || _dual_infeasibility_row!(c, w, row, index)
    return nothing
end
function _dual_infeasibility_pivot!(w, row)
    c = _current_dual_infeasibility!(w)
    isnothing(c) || _dual_infeasibility_row!(c, w, row, w.basis.basic_indices[row])
    return nothing
end

function _cached_dual_edge_selection(w::SimplexWorkspace{T}, c, scoring::Val{S})::Int where {T,S}
    selected = -1
    scored = 0
    best = zero(S)
    weighted = _effective_pricing(w, :dual) != :dantzig
    for pos in 1:c.count
        row = c.rows[pos]
        row in w.scratch.rejected_rows && continue
        scored += 1
        index = w.basis.basic_indices[row]
        score = _dual_pricing_score(c.values[row], w.pricing_weights[index], weighted, scoring)
        # Swap deletion changes storage order, never the original logical-row
        # tie break. In particular, zero/NaN scores must not create a winner.
        if score > best || (selected != -1 && score == best && row < selected)
            selected, best = row, score
        end
    end
    _record_full_pricing!(w.progress.diagnostics, length(c.values), scored)
    return selected
end
