module GenericVirtualFreePivotTests
module VFPReference
using JSimplex,SparseArrays,LinearAlgebra
using JSimplex: SimplexWorkspace,SolveQualityScratch,NumericalPolicy,SolveQuality,
    PivotCandidate,CandidatePool,VariableState,AT_LOWER,AT_UPPER,FREE_NONBASIC,BASIC,
    _is_exact,_compensated_solve_quality!,_compensated_quality_term!,_primal_direction_magnitude,_PriceAuditMatrix,
    _prepare_auto_pricing!,_partial_pricing_enabled,_effective_pricing,
    _primal_initialize_steepest!,_primal_steepest_weight!,_primal_dantzig_score,
    _primal_weighted_score,_record_full_pricing!,_is_fixed,_pricing_pool!,
    _record_pricing_work!,_select_pool!,_pool_primal_score,_select_dual_pool!,
    _pivot_quality_buffers,_pivot_column!,_basis_matrix!,_sync_recovery_rejections!

function _componentwise_backward_error(residual::AbstractVector{T}, scale) where {T<:AbstractFloat}
    axes(residual) == axes(scale) || throw(DimensionMismatch("Residual and scale dimensions differ"))
    error = zero(T)
    for i in eachindex(residual,scale)
        r, s = abs(residual[i]), scale[i]
        isfinite(r) && isfinite(s) && s >= zero(s) || return T(Inf)
        ratio = iszero(s) ? (iszero(r) ? zero(T) : T(Inf)) : r/s
        error = max(error,ratio)
    end
    return error
end

_quality_values(B::AbstractMatrix) = B
_quality_values(B::SparseMatrixCSC) = nonzeros(B)

@inline function _accumulate_quality_term!(r::AbstractVector{W}, scale, terms,
                                          x, a, row, column, transposed) where {W}
    target, source = transposed ? (column,row) : (row,column)
    product = W(a)*W(x[source])
    r[target] -= product
    scale[target] += abs(product)
    terms[target] += 2
    return W <: AbstractFloat && !iszero(a) && !iszero(x[source]) &&
           abs(product) < floatmin(W)
end

function _quality_components!(r::AbstractVector{W}, scale, terms, B, x, rhs, transposed) where {W}
    for i in eachindex(rhs)
        r[i] = W(rhs[i])
        scale[i] = abs(r[i])
        terms[i] = 1
    end
    unsafe_range = false
    if B isa SparseMatrixCSC
        for column in axes(B,2), p in nzrange(B,column)
            unsafe_range |= _accumulate_quality_term!(r,scale,terms,x,B.nzval[p],B.rowval[p],column,transposed)
        end
    else
        for column in axes(B,2), row in axes(B,1)
            unsafe_range |= _accumulate_quality_term!(r,scale,terms,x,B[row,column],row,column,transposed)
        end
    end
    return unsafe_range
end

# A call-local comparison limit is shared only across ordinary array accesses.
@inline function _bigfloat_quality_term!(r, scale, terms, x, a, row, column,
                                         transposed, limit::Union{Nothing,BigFloat})
    target, source = transposed ? (column,row) : (row,column)
    product = BigFloat(a)*BigFloat(x[source])
    r[target] -= product
    magnitude = _primal_direction_magnitude(product)
    scale[target] += magnitude
    terms[target] += 2
    if !iszero(a) && !iszero(x[source])
        if limit === nothing
            limit = floatmin(BigFloat)
        end
        return magnitude < limit, limit
    end
    return false, limit
end

function _quality_components!(r::Vector{BigFloat}, scale::Vector{BigFloat},
                              terms::Vector{Int},
                              B::Union{Matrix{BigFloat},SparseMatrixCSC{BigFloat}},
                              x::Vector{BigFloat}, rhs::Vector{BigFloat}, transposed)
    for i in eachindex(rhs)
        r[i] = BigFloat(rhs[i])
        scale[i] = _primal_direction_magnitude(r[i])
        terms[i] = 1
    end
    unsafe_range = false
    limit::Union{Nothing,BigFloat} = nothing
    if B isa SparseMatrixCSC
        for column in axes(B,2), p in nzrange(B,column)
            unsafe, limit = _bigfloat_quality_term!(r,scale,terms,x,B.nzval[p],
                B.rowval[p],column,transposed,limit)
            unsafe_range |= unsafe
        end
    else
        for column in axes(B,2), row in axes(B,1)
            unsafe, limit = _bigfloat_quality_term!(r,scale,terms,x,B[row,column],
                row,column,transposed,limit)
            unsafe_range |= unsafe
        end
    end
    return unsafe_range
end

function _quality_roundoff(::Type{W}, terms) where {W<:AbstractFloat}
    k = maximum(terms; init=0)
    product = W(k)*eps(W)
    return isfinite(product) && product < one(W) ? product/(one(W)-product) : W(Inf)
end

function _floating_quality!(scratch::SolveQualityScratch{T}, r, scale, terms, policy) where {T}
    ratio = _componentwise_backward_error(r,scale)
    absolute = maximum(abs,r; init=zero(eltype(r)))
    for i in eachindex(r)
        scratch.residual[i] = convert(T,r[i])
    end
    absolute_T, ratio_T = convert(T,absolute), convert(T,ratio)
    iszero(absolute_T) && absolute > 0 && (absolute_T = nextfloat(zero(T)))
    finite = isfinite(absolute_T) && isfinite(ratio_T) && all(isfinite,scratch.residual)
    roundoff = _quality_roundoff(eltype(r),terms)
    reliable = finite && isfinite(roundoff) && roundoff < 1 &&
        (ratio + roundoff)/(1-roundoff) <= policy.solve_tolerance
    return SolveQuality{T}(absolute_T,ratio_T,finite,reliable)
end

function _componentwise_backward_error(residual::Vector{BigFloat}, scale::Vector{BigFloat})
    T = BigFloat
    axes(residual) == axes(scale) || throw(DimensionMismatch("Residual and scale dimensions differ"))
    error = zero(T)
    for i in eachindex(residual,scale)
        r, s = _primal_direction_magnitude(residual[i]), scale[i]
        isfinite(r) && isfinite(s) && s >= Clong(0) || return T(Inf)
        ratio = iszero(s) ? (iszero(r) ? zero(T) : T(Inf)) : r/s
        error = max(error,ratio)
    end
    return error
end

function _quality_roundoff(::Type{BigFloat}, terms)
    W = BigFloat
    k = maximum(terms; init=0)
    product = W(k)*eps(W)
    return isfinite(product) && product < Clong(1) ? product/(Clong(1)-product) : W(Inf)
end

function _floating_quality!(scratch::SolveQualityScratch{T}, r::Vector{BigFloat},
                            scale::Vector{BigFloat}, terms::Vector{Int}, policy) where {T}
    ratio = _componentwise_backward_error(r,scale)
    absolute = maximum(_primal_direction_magnitude,r; init=zero(eltype(r)))
    for i in eachindex(r)
        scratch.residual[i] = convert(T,r[i])
    end
    absolute_T, ratio_T = convert(T,absolute), convert(T,ratio)
    iszero(absolute_T) && absolute > 0 && (absolute_T = nextfloat(zero(T)))
    finite = isfinite(absolute_T) && isfinite(ratio_T) && all(isfinite,scratch.residual)
    roundoff = _quality_roundoff(eltype(r),terms)
    reliable = finite && isfinite(roundoff) && roundoff < 1 &&
        (ratio + roundoff)/(1-roundoff) <= policy.solve_tolerance
    return SolveQuality{T}(absolute_T,ratio_T,finite,reliable)
end

_stored_quality_bits(::Type{T}, B, x, rhs, policy) where {T<:AbstractFloat} = precision(T)
function _stored_quality_bits(::Type{BigFloat}, B, x, rhs, policy)
    return max(precision(BigFloat), precision(policy.solve_tolerance),
        maximum(precision,_quality_values(B);init=2), maximum(precision,x;init=2),
        maximum(precision,rhs;init=2))
end

function _wide_solve_quality!(scratch::SolveQualityScratch{T}, B, x, rhs, policy, transposed) where {T}
    input_bits = _stored_quality_bits(T,B,x,rhs,policy)
    term_count = max(size(B,1),size(B,2),1)
    # Additional bits keep residual-evaluation uncertainty below the policy's
    # solve tolerance; this does not change the basis working precision.
    bits = max(128, 2*input_bits + ndigits(term_count; base=2) + 16)
    return setprecision(BigFloat,bits) do
        r, scale = zeros(BigFloat,length(rhs)), zeros(BigFloat,length(rhs))
        unsafe_range = _quality_components!(r,scale,scratch.terms,B,x,rhs,transposed)
        quality = _floating_quality!(scratch,r,scale,scratch.terms,policy)
        unsafe_range ? SolveQuality{T}(quality.absolute_error,quality.relative_error,false,false) : quality
    end
end

"""Evaluate an absolute residual and a componentwise backward error.

Scratch is owned separately from live tableau vectors. Float32 and Float64 use
native compensated accumulation before a local BigFloat evaluation is needed
for unsafe range or an inconclusive rounding-error enclosure. Stored
BigFloat precision is respected. Small backward error is not a forward-error
or pivot-safety certificate. Exact rationals require an exactly zero residual.
"""
function solve_quality!(scratch::SolveQualityScratch{T}, B::AbstractMatrix{T},
                        x::AbstractVector{T}, rhs::AbstractVector{T},
                        policy::NumericalPolicy{T}; transposed::Bool=false) where {T}
    rows, columns = transposed ? reverse(size(B)) : size(B)
    length(rhs) == rows && length(x) == columns && length(scratch.residual) == rows ||
        throw(DimensionMismatch("Incompatible basis residual dimensions"))
    any(array -> Base.mightalias(array,rhs) || Base.mightalias(array,x) ||
        Base.mightalias(array,_quality_values(B)),
        (scratch.residual,scratch.work_residual,scratch.work_scale,
         scratch.compensation,scratch.error_sum)) &&
        throw(ArgumentError("Quality scratch must not alias basis, solution, or RHS"))
    if _is_exact(T) === Val(true)
        _quality_components!(scratch.work_residual,scratch.work_scale,scratch.terms,B,x,rhs,transposed)
        copyto!(scratch.residual,scratch.work_residual)
        absolute = maximum(abs,scratch.residual;init=zero(T))
        return SolveQuality{T}(absolute,nothing,true,iszero(absolute))
    end
    if !all(isfinite,_quality_values(B)) || !all(isfinite,x) || !all(isfinite,rhs)
        fill!(scratch.residual,T(Inf))
        return SolveQuality{T}(T(Inf),T(Inf),false,false)
    end
    T === BigFloat && return _wide_solve_quality!(scratch,B,x,rhs,policy,transposed)
    unsafe_range = _quality_components!(scratch.work_residual,scratch.work_scale,scratch.terms,B,x,rhs,transposed)
    roundoff = _quality_roundoff(eltype(scratch.work_residual),scratch.terms)
    if unsafe_range || !all(isfinite,scratch.work_residual) || !all(isfinite,scratch.work_scale) ||
       roundoff > policy.solve_tolerance/4
        if !unsafe_range
            native = _compensated_solve_quality!(scratch,B,x,rhs,policy,transposed)
            isnothing(native) || return native
        end
        return _wide_solve_quality!(scratch,B,x,rhs,policy,transposed)
    end
    return _floating_quality!(scratch,scratch.work_residual,scratch.work_scale,scratch.terms,policy)
end

_quality_values(B::_PriceAuditMatrix) = nonzeros(B.matrix)

function _compensated_quality_components!(scratch,B::_PriceAuditMatrix{T},x,transposed) where T
    A = B.matrix
    m,n = size(A)
    for j in axes(A,2), p in nzrange(A,j)
        target,source = transposed ? (A.rowval[p],j) : (j,A.rowval[p])
        _compensated_quality_term!(scratch,A.nzval[p],x[source],target)
    end
    for i in 1:m
        target,source = transposed ? (i,n+i) : (n+i,i)
        _compensated_quality_term!(scratch,-one(T),x[source],target)
    end
    for i in 1:n+m
        target,source = transposed ? (m+i,i) : (i,m+i)
        _compensated_quality_term!(scratch,one(T),x[source],target)
    end
    return nothing
end

function _quality_components!(r::AbstractVector{W},scale,terms,B::_PriceAuditMatrix{T},
                               x,rhs,transposed) where {W,T}
    for i in eachindex(rhs)
        r[i] = W(rhs[i])
        scale[i] = abs(r[i])
        terms[i] = 1
    end
    A = B.matrix
    m,n = size(A)
    unsafe = false
    for j in axes(A,2), p in nzrange(A,j)
        unsafe |= _accumulate_quality_term!(r,scale,terms,x,A.nzval[p],j,A.rowval[p],transposed)
    end
    for i in 1:m
        unsafe |= _accumulate_quality_term!(r,scale,terms,x,-one(T),n+i,i,transposed)
    end
    for i in 1:n+m
        unsafe |= _accumulate_quality_term!(r,scale,terms,x,one(T),i,m+i,transposed)
    end
    return unsafe
end


function _primal_price_prediction_reliable(ws::SimplexWorkspace{T},predicted) where T
    all(i -> iszero(predicted[i]),ws.basis.basic_indices) || return false
    B = _PriceAuditMatrix(ws.problem.A)
    values = vcat(ws.scratch.rho,predicted)
    scratch = SolveQualityScratch(T,length(ws.costs))
    return solve_quality!(scratch,B,values,ws.costs,ws.progress.numerical_policy).reliable
end

function _primal_entering(workspace::SimplexWorkspace{T}, tolerance::T) where {T}
    _prepare_auto_pricing!(workspace,:primal)
    state = workspace.scratch.pricing
    isnothing(state) || (state.pricing_passes += 1)
    if _partial_pricing_enabled(workspace,:primal)
        entering = _select_workspace_pool!(workspace,:primal;tolerance)
        direction = entering == 0 ? zero(T) :
            (workspace.reduced_costs[entering] < zero(T) ? one(T) : -one(T))
        return entering,direction
    end
    pricing = _effective_pricing(workspace,:primal)
    pricing == :steepest_edge && _primal_initialize_steepest!(workspace)
    entering = 0
    scored = 0
    direction = zero(T)
    best_score = _primal_dantzig_score(one(T))
    for index in eachindex(workspace.basis.states)
        state = workspace.basis.states[index]
        state == BASIC && continue
        index in workspace.scratch.rejected_entering && continue
        _is_fixed(workspace.lower[index], workspace.upper[index]) && continue
        reduced_cost = workspace.reduced_costs[index]
        improving = (state == AT_LOWER && reduced_cost < -tolerance) ||
                    (state == AT_UPPER && reduced_cost > tolerance) ||
                    (state == FREE_NONBASIC && abs(reduced_cost) > tolerance)
        improving || continue
        scored += 1
        score = if pricing == :dantzig
            _primal_dantzig_score(reduced_cost)
        else
            weight = pricing == :steepest_edge && !workspace.scratch.steepest_valid[index] ?
                _primal_steepest_weight!(workspace, index) : workspace.pricing_weights[index]
            _primal_weighted_score(reduced_cost, weight)
        end
        if entering == 0 || score > best_score
            entering = index
            direction = reduced_cost < zero(T) ? one(T) : -one(T)
            best_score = score
        end
    end
    _record_full_pricing!(workspace.progress.diagnostics,length(workspace.basis.states),scored)
    return entering, direction
end

function _primal_entering(workspace::SimplexWorkspace{T}, tolerance::T) where {T<:Union{BigFloat,Rational{BigInt}}}
    _prepare_auto_pricing!(workspace,:primal)
    state = workspace.scratch.pricing
    isnothing(state) || (state.pricing_passes += 1)
    if _partial_pricing_enabled(workspace,:primal)
        entering = _select_workspace_pool!(workspace,:primal;tolerance)
        direction = entering == 0 ? zero(T) :
            (workspace.reduced_costs[entering] < 0 ? one(T) : -one(T))
        return entering,direction
    end
    pricing = _effective_pricing(workspace,:primal)
    pricing == :steepest_edge && _primal_initialize_steepest!(workspace)
    entering = 0
    scored = 0
    direction = zero(T)
    best_score = _primal_dantzig_score(one(T))
    negative_tolerance = tolerance
    negative_ready = false
    reuse_negative = pricing === :dantzig || pricing === :devex
    for index in eachindex(workspace.basis.states)
        state = workspace.basis.states[index]
        state == BASIC && continue
        index in workspace.scratch.rejected_entering && continue
        _is_fixed(workspace.lower[index], workspace.upper[index]) && continue
        reduced_cost = workspace.reduced_costs[index]
        improving = if state == AT_LOWER
            if reuse_negative
                if !negative_ready
                    negative_tolerance = -tolerance
                    negative_ready = true
                end
                reduced_cost < negative_tolerance
            else
                reduced_cost < -tolerance
            end
        else
            (state == AT_UPPER && reduced_cost > tolerance) ||
            (state == FREE_NONBASIC && abs(reduced_cost) > tolerance)
        end
        improving || continue
        scored += 1
        score = if pricing == :dantzig
            _primal_dantzig_score(reduced_cost)
        else
            weight = pricing == :steepest_edge && !workspace.scratch.steepest_valid[index] ?
                _primal_steepest_weight!(workspace, index) : workspace.pricing_weights[index]
            _primal_weighted_score(reduced_cost, weight)
        end
        if entering == 0 || score > best_score
            entering = index
            direction = reduced_cost < 0 ? one(T) : -one(T)
            best_score = score
        end
    end
    _record_full_pricing!(workspace.progress.diagnostics,length(workspace.basis.states),scored)
    return entering, direction
end

function _pool_primal_eligible(ws,index,tolerance)
    state = ws.basis.states[index]
    state == BASIC && return false
    index in ws.scratch.rejected_entering && return false
    _is_fixed(ws.lower[index],ws.upper[index]) && return false
    value = ws.reduced_costs[index]
    return (state == AT_LOWER && value < -tolerance) ||
           (state == AT_UPPER && value > tolerance) ||
           (state == FREE_NONBASIC && abs(value) > tolerance)
end

function select_pricing_candidate!(ws,pool::CandidatePool,policy;
                                   force_full::Bool=false,
                                   tolerance=ws.options.dual_tolerance)::Int
    force_full = force_full || !policy.partial_pricing
    T = eltype(ws.costs)
    _prepare_auto_pricing!(ws,pool.algorithm)
    if pool.algorithm == :primal
        pricing = _effective_pricing(ws,:primal)
        pricing == :steepest_edge && _primal_initialize_steepest!(ws)
        eligible = index -> _pool_primal_eligible(ws,index,tolerance)
        score = index -> _pool_primal_score(ws,index,pricing)
        return _select_pool!(pool,length(ws.basis.states),eligible,score,
                             _primal_dantzig_score(one(T)),true;force_full)
    end
    if ws.options.pricing == :auto && T <: Rational
        return _select_dual_pool!(ws,pool,Val(Rational{BigInt});force_full)
    elseif ws.options.pricing == :auto
        return _select_dual_pool!(ws,pool,Val(:scaled);force_full)
    end
    return _select_dual_pool!(ws,pool,Val(T);force_full)
end

function _select_workspace_pool!(ws,algorithm;force_full=false,
                                 tolerance=ws.options.dual_tolerance)
    pool = _pricing_pool!(ws,algorithm)
    previous = (pool.scanned_entries,pool.scored_entries,pool.full_scans,pool.block_scans)
    result = select_pricing_candidate!(ws,pool,ws.progress.numerical_policy;force_full,tolerance)
    _record_pricing_work!(ws.progress.diagnostics,pool,previous,result)
    return result
end

function dual_infeasibility_summary(workspace::SimplexWorkspace{T}) where {T}
    infeasibility = zero(T)
    count = 0
    tolerance = workspace.options.dual_tolerance
    for index in eachindex(workspace.basis.states)
        state = workspace.basis.states[index]
        state == BASIC && continue
        _is_fixed(workspace.lower[index], workspace.upper[index]) && continue

        reduced_cost = workspace.reduced_costs[index]
        if state == AT_LOWER && reduced_cost < -tolerance
            infeasibility -= reduced_cost
            count += 1
        elseif state == AT_UPPER && reduced_cost > tolerance
            infeasibility += reduced_cost
            count += 1
        elseif state == FREE_NONBASIC && abs(reduced_cost) > tolerance
            infeasibility += abs(reduced_cost)
            count += 1
        end
    end
    return infeasibility, count
end

function dual_infeasibility_summary(workspace::SimplexWorkspace{T}) where {T<:Union{BigFloat,Rational{BigInt}}}
    infeasibility = zero(T)
    count = 0
    tolerance = workspace.options.dual_tolerance
    negative_tolerance = tolerance
    negative_ready = false
    for index in eachindex(workspace.basis.states)
        state = workspace.basis.states[index]
        state == BASIC && continue
        _is_fixed(workspace.lower[index], workspace.upper[index]) && continue

        reduced_cost = workspace.reduced_costs[index]
        if state == AT_LOWER
            if !negative_ready
                negative_tolerance = -tolerance
                negative_ready = true
            end
            if reduced_cost < negative_tolerance
                infeasibility -= reduced_cost
                count += 1
            end
        elseif state == AT_UPPER && reduced_cost > tolerance
            infeasibility += reduced_cost
            count += 1
        elseif state == FREE_NONBASIC
            magnitude = abs(reduced_cost)
            if magnitude > tolerance
                infeasibility += magnitude
                count += 1
            end
        end
    end
    return infeasibility, count
end

function _pivot_agrees(row_pivot, column_pivot, error_bound)::Bool
    all(isfinite, (row_pivot,column_pivot,error_bound)) || return false
    error_bound >= zero(error_bound) || return false
    sign(row_pivot) == sign(column_pivot) || return false
    min(abs(row_pivot),abs(column_pivot)) > error_bound || return false
    return abs(row_pivot-column_pivot) <= error_bound
end


function validate_pivot!(ws::SimplexWorkspace{T}, proposal::PivotCandidate{T},
                         policy::NumericalPolicy{T})::Symbol where {T}
    if policy.recovery && !isempty(ws.scratch.recovery_rejections)
        _sync_recovery_rejections!(ws)
        (proposal.leaving_row,proposal.entering) in ws.scratch.recovery_rejections &&
            return :reject_candidate
    end
    B = _basis_matrix!(ws)
    m = size(B,1)
    length(proposal.column) == length(proposal.rho) == m ||
        throw(DimensionMismatch("pivot solve dimensions"))
    checkbounds(proposal.column,proposal.leaving_row)
    checkbounds(ws.basis.states,proposal.entering)
    buffers = _pivot_quality_buffers(ws)
    rhs = _pivot_column!(buffers.rhs,ws,proposal.entering)
    unit = fill!(buffers.unit,zero(T))
    unit[proposal.leaving_row] = one(T)
    column_quality = buffers.column
    row_quality = buffers.row
    cq = solve_quality!(column_quality,B,proposal.column,rhs,policy)
    rq = solve_quality!(row_quality,B,proposal.rho,unit,policy;transposed=true)
    cq.reliable && rq.reliable || return :refresh
    row_pivot = proposal.row_pivot
    column_pivot = proposal.column[proposal.leaving_row]
    independently_priced = dot(proposal.rho,rhs)
    all(isfinite,(row_pivot,column_pivot,independently_priced)) || return :reject_candidate
    sign(row_pivot) == sign(column_pivot) || return :reject_candidate
    iszero(column_pivot) && return :reject_candidate
    isfinite(inv(column_pivot)) || return :reject_candidate
    all(value -> isfinite(value/column_pivot),proposal.column) || return :reject_candidate
    if _is_exact(T) === Val(true)
        return row_pivot == independently_priced &&
               _pivot_agrees(row_pivot,column_pivot,zero(T)) ? :accept : :reject_candidate
    end
    # e_r = B' * rho + row_residual and rhs = B * column + column_residual.
    # Their contractions bound disagreement, not forward error in an arbitrary
    # ill-conditioned basis. Cap the allowed error separately and require an
    # independently accumulated row estimate to agree as well.
    contraction = zero(T)
    dot_scale = zero(T)
    for i in eachindex(rhs)
        contraction += abs(row_quality.residual[i]*proposal.column[i]) +
                       abs(column_quality.residual[i]*proposal.rho[i])
        dot_scale += abs(proposal.rho[i]*rhs[i])
    end
    gamma = T(4m+8)*eps(T)
    gamma < one(T) || return :refresh
    roundoff = gamma/(one(T)-gamma) *
        (dot_scale+abs(row_pivot)+abs(column_pivot))
    error_bound = contraction + roundoff
    isfinite(error_bound) || return :refresh
    error_bound <= policy.pivot_error_tolerance *
                   min(abs(row_pivot),abs(column_pivot)) || return :refresh
    return _pivot_agrees(row_pivot,column_pivot,error_bound) &&
           _pivot_agrees(row_pivot,independently_priced,error_bound) ?
           :accept : :reject_candidate
end


end

const VFPA=JSimplex
const VFPB=JSimplex
const VFPC=JSimplex
using Test,JSimplex,SparseArrays,LinearAlgebra
const J=JSimplex
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
same(a,b)=isequal(a,b)
same(a::BigFloat,b::BigFloat)=isequal(a,b)&&precision(a)==precision(b)&&signbit(a)==signbit(b)
same(a::Tuple,b::Tuple)=length(a)==length(b)&&all(same(x,y) for (x,y) in zip(a,b))
same(a::AbstractArray,b::AbstractArray)=axes(a)==axes(b)&&all(same(a[i],b[i]) for i in eachindex(a,b))
same(a::J.Bound,b::J.Bound)=a.bounded==b.bounded&&same(a.value,b.value)
same(a::J.SolveQuality,b::J.SolveQuality)=same(a.absolute_error,b.absolute_error)&&same(a.relative_error,b.relative_error)&&a.finite==b.finite&&a.reliable==b.reliable
capture(f)=try;(:value,f());catch e;(:error,typeof(e),sprint(showerror,e));end
cost(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
patternvalue(::Type{T},i,pattern) where T = T(pattern===:zero ? 0 : (pattern===:negative||pattern===:mixed&&iseven(i) ? -1 : 1)*((i%3+1)//8))
function makeworkspace(::Type{T},n,m,density,pattern;pricing=:dantzig,partial=false) where T
 A=zeros(T,m,n)
 for j in 1:n,i in 1:m
  if j<=m
   if i==j;A[i,j]=T(2)
   elseif i<j&&(density===:dense||j==i+1);A[i,j]=one(T)
   end
  elseif i==1||density===:dense||(i+j)%4==0
   A[i,j]=T(((i+j)%5+1)//32)
  end
 end
 # A literal dyadic direction gives an independent pivot oracle. Upper
 # triangular 2I+integer U keeps all control-type solves representable.
 wanted=T[patternvalue(T,i,pattern) for i in 1:m]
 n>m&&(A[:,m+1]=A[:,1:m]*wanted)
 rho=T[patternvalue(T,i,pattern) for i in 1:m]
 objective=transpose(A)*rho
 p=LinearProblem(sparse(A),objective;column_lower=zeros(T,n),column_upper=fill(T(4),n),row_lower=fill(-T(1024),m),row_upper=fill(T(1024),m))
 opt=SolverOptions(T;algorithm=:primal,pricing=pricing,partial_pricing=partial,verbose=false)
 pol=J.NumericalPolicy(T;pivot_validation=true,recovery=false,solve_refinement=false,partial_pricing=partial,refactor_timing=false)
 w=J.initialize_workspace(p,opt;progress=J.SimplexProgressContext(p;numerical_policy=pol))
 fill!(w.basis.states,J.AT_LOWER);copyto!(w.basis.basic_indices,collect(1:m));fill!(w.scratch.basic_mask,false)
 for i in 1:m;w.basis.states[i]=J.BASIC;w.scratch.basic_mask[i]=true;end
 J.recompute!(w;refactorize=true)
 return w,rho,wanted
end
poolstate(p)=isnothing(p) ? nothing : Tuple(getfield(p,k) isa AbstractArray ? copy(getfield(p,k)) : getfield(p,k) for k in fieldnames(typeof(p)))
function restorepool!(p,seed)
 for (i,k) in enumerate(fieldnames(typeof(p)))
  if k===:indices;resize!(p.indices,length(seed[i]));copyto!(p.indices,seed[i])
  else;setfield!(p,k,seed[i])
  end
 end
 nothing
end
function fixture(::Type{T},n,m,scope,density,pattern) where T
 pricing=scope===:enter_devex ? :devex : :dantzig
 partial=scope in (:partial_hit,:partial_rebuild)
 w,rho,wanted=makeworkspace(T,n,m,density,pattern;pricing,partial)
 if scope in (:audit,:virtual,:virtual_transposed)
  copyto!(w.scratch.rho,rho)
  predicted=vcat(w.costs[1:n]-transpose(w.problem.A)*rho,rho)
  if scope===:audit;return (scope=scope,w=w,predicted=predicted);end
  B=J._PriceAuditMatrix(w.problem.A)
  x=scope===:virtual ? vcat(rho,predicted) : T[patternvalue(T,i,pattern) for i in 1:size(B,1)]
  rhs=scope===:virtual ? copy(w.costs) : vcat(w.problem.A*x[1:n]-x[n+1:n+m],x)
  return (scope=scope,w=w,B=B,x=x,rhs=rhs,scratch=J.SolveQualityScratch(T,length(rhs)),policy=w.progress.numerical_policy)
 elseif scope===:pivot
  enter=m+1;rhs=Vector(w.problem.A[:,enter]);column=similar(rhs);J.forward_solve!(column,w.factorization,rhs)
  unit=zeros(T,m);unit[1]=one(T);row=similar(unit);J.transpose_solve!(row,w.factorization,unit)
  proposal=J.PivotCandidate(enter,1,dot(row,rhs),column,row)
  return (scope=scope,w=w,proposal=proposal,wanted=wanted)
 end
 for i in eachindex(w.basis.states)
  w.basis.states[i]==J.BASIC&&(w.reduced_costs[i]=zero(T);continue)
  w.reduced_costs[i]=patternvalue(T,i,pattern===:bound ? :positive : pattern)
  w.pricing_weights[i]=T(2)
  w.basis.states[i]=pattern===:bound ? J.AT_UPPER : J.FREE_NONBASIC
  if pattern!==:bound;w.lower[i]=J.Bound{T}(nothing);w.upper[i]=J.Bound{T}(nothing);end
 end
 seed=nothing
 if partial
  pool=J._pricing_pool!(w,:primal)
  J.select_pricing_candidate!(w,pool,w.progress.numerical_policy)
  seed=poolstate(pool)
 end
 return (scope=scope,w=w,poolseed=seed)
end
function reset!(v)
 if v.scope in (:partial_hit,:partial_rebuild)
  restorepool!(v.w.scratch.pricing_pool,v.poolseed)
  if v.scope===:partial_rebuild;J._invalidate_pricing_pool!(v.w;basis=false,costs=true);end
 end
 nothing
end
function qualityout(s)
 (s.residual,s.work_residual,s.work_scale,s.terms,s.compensation,s.error_sum)
end
function outputs(v)
 w=v.w
 if v.scope in (:virtual,:virtual_transposed);return qualityout(v.scratch)
 elseif v.scope===:pivot
  b=w.scratch.pivot_quality_cache;bm=w.scratch.basis_matrix
  return (isnothing(b) ? nothing : (b.rhs,b.unit,b.correction,b.trial,b.singletons,qualityout(b.column),qualityout(b.row)),isnothing(bm) ? nothing : (bm.colptr,bm.rowval,bm.nzval))
 end
 state=w.scratch.pricing
 (w.primal,w.reduced_costs,w.pricing_weights,w.scratch.steepest_valid,w.scratch.steepest_initialized,poolstate(w.scratch.pricing_pool),isnothing(state) ? nothing : Tuple(getfield(state,k) for k in fieldnames(typeof(state))))
end
function inputs(v)
 w=v.w;common=(w.problem.A.nzval,w.problem.A.rowval,w.problem.A.colptr,w.costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states)
 if v.scope===:audit;return (common...,w.scratch.rho,v.predicted)
 elseif v.scope in (:virtual,:virtual_transposed);return (common...,v.x,v.rhs)
 elseif v.scope===:pivot;return (common...,v.proposal.column,v.proposal.rho)
 end
 return (common...,w.reduced_costs,w.primal)
end
snapshot(v)=(inputs(v),map(copy,inputs(v)),deepcopy(inputs(v)))
function intact(v,s)
 all(inputs(v)[i]===s[1][i]&&same(inputs(v)[i],s[3][i])&&all(inputs(v)[i][j]===s[2][i][j] for j in eachindex(s[2][i])) for i in eachindex(s[1]))
end
@noinline function whole(::Val{arm},::Val{scope},v) where {arm,scope}
 mod=arm===:original ? VFPReference : arm===:A ? VFPA : arm===:B ? VFPB : VFPC
 if scope===:audit;return mod._primal_price_prediction_reliable(v.w,v.predicted)
 elseif scope in (:virtual,:virtual_transposed);return mod.solve_quality!(v.scratch,v.B,v.x,v.rhs,v.policy;transposed=scope===:virtual_transposed)
 elseif scope===:pivot;return mod.validate_pivot!(v.w,v.proposal,v.w.progress.numerical_policy)
 elseif scope===:summary;return mod.dual_infeasibility_summary(v.w)
 end
 return mod._primal_entering(v.w,v.w.options.dual_tolerance)
end
sink(x::Bool)=Int(x)
sink(x::Symbol)=x===:accept ? 1 : x===:refresh ? 2 : 3
sink(x::J.SolveQuality)=Int(x.finite)+2Int(x.reliable)+Int(iszero(x.absolute_error))
sink(x::Tuple{Int,<:Real})=x[1]+Int(signbit(x[2]))
sink(x::Tuple{<:Real,Int})=x[2]+Int(iszero(x[1]))
@noinline runwhole(m,s,v)=sink(whole(m,s,v))
function timed(m::M,s::S,v::V) where {M,S,V}
 t=@timed runwhole(m,s,v);merge(cost(t),Dict("sink"=>t.value))
end
armfor(scope)=scope in (:audit,:virtual,:virtual_transposed) ? :A : scope===:pivot ? :C : :B
function checkpair(a,b;protect=true)
 arm=armfor(a.scope);reset!(a);reset!(b);sa=snapshot(a);sb=snapshot(b);ctx=(precision(BigFloat),rounding(BigFloat))
 x=capture(()->whole(Val(:original),Val(a.scope),a));y=capture(()->whole(Val(arm),Val(b.scope),b))
 @test same(x,y)
 @test same(outputs(a),outputs(b))
 @test ctx==(precision(BigFloat),rounding(BigFloat))
 protect&&@test intact(a,sa)&&intact(b,sb)
 x
end
function checkroute(v,before)
 if v.scope in (:partial_hit,:partial_rebuild)
  p=v.w.scratch.pricing_pool;actual=length(v.w.basis.states)>128
  @test J._partial_pricing_enabled(v.w,:primal)==actual
  if actual
   @test p.passes==before.passes+1
   @test v.scope===:partial_hit ? p.scanned_entries==before.scanned_entries : p.full_scans==before.full_scans+1&&p.scanned_entries==before.scanned_entries+length(v.w.basis.states)
  else
   @test poolstate(p)==before.state
  end
 end
end
function routebefore(v)
 if v.scope in (:partial_hit,:partial_rebuild)
  p=v.w.scratch.pricing_pool
  @test v.scope===:partial_hit ? p.valid&&!isempty(p.indices) : !p.valid&&isempty(p.indices)
  return (passes=p.passes,scanned_entries=p.scanned_entries,full_scans=p.full_scans,state=poolstate(p))
 end
 nothing
end
function correctness(::Type{T}) where T
 @testset "Virtual/free/pivot correctness $T" begin
  for scope in (:audit,:virtual,:virtual_transposed,:enter_dantzig,:enter_devex,:partial_hit,:partial_rebuild,:summary,:pivot),density in (:sparse,:dense),pattern in (:positive,:negative,:mixed,:zero)
   # A zero candidate pool cannot have a cached hit; zero exhaustion uses rebuild.
   scope===:partial_hit&&pattern===:zero&&continue
   a=fixture(T,8,4,scope,density,pattern);b=fixture(T,8,4,scope,density,pattern)
   z=checkpair(a,b)
   @test z[1]===:value
   scope===:audit&&@test z[2]===true
   scope===:pivot&&@test z[2]===(pattern===:zero ? :reject_candidate : :accept)
   if scope===:pivot
    @test same(a.proposal.column,b.proposal.column)
    @test pattern===:zero ? all(iszero,a.proposal.column)&&all(iszero,b.proposal.column) : T===Float64 ? native_direction_oracle(a)&&native_direction_oracle(b) : same(a.proposal.column,a.wanted)&&same(b.proposal.column,b.wanted)
   end
  end
  # Independently exercise both genuine >128 partial routes and small fallback.
  for n in (8,128),scope in (:partial_hit,:partial_rebuild)
   a=fixture(T,n,4,scope,:sparse,:positive);b=fixture(T,n,4,scope,:sparse,:positive)
   for (arm,v) in ((:original,a),(:B,b))
    reset!(v);before=routebefore(v);z=whole(Val(arm),Val(scope),v);@test z[1]>0;checkroute(v,before)
   end
  end
  for scope in (:audit,:virtual,:virtual_transposed,:enter_dantzig,:summary,:pivot),edge in (:nonfinite,:mixed_precision,:dimension,:alias,:perturbed)
   a=fixture(T,8,4,scope,:dense,:mixed);b=fixture(T,8,4,scope,:dense,:mixed)
   for side in (:a,:b)
    v=side===:a ? a : b
    if scope===:audit
     if edge===:nonfinite&&T<:AbstractFloat;v.w.scratch.rho[1]=T(NaN)
     elseif edge===:mixed_precision&&T===BigFloat;v.w.scratch.rho[1]=setprecision(()->BigFloat(v.w.scratch.rho[1]),BigFloat,512)
     elseif edge===:dimension;v=merge(v,(predicted=v.predicted[1:end-1],))
     elseif edge===:alias;v=merge(v,(predicted=v.w.costs,))
     elseif edge===:perturbed;v.predicted[v.w.basis.basic_indices[1]]=one(T)
     end
    elseif scope in (:virtual,:virtual_transposed)
     if edge===:nonfinite&&T<:AbstractFloat;v.x[1]=T(Inf)
     elseif edge===:mixed_precision&&T===BigFloat;v.x[1]=setprecision(()->BigFloat(3//7),BigFloat,512)
     elseif edge===:dimension;v=merge(v,(x=v.x[1:end-1],))
     elseif edge===:alias
      q=v.scratch;v=merge(v,(rhs=q.residual,))
     elseif edge===:perturbed;v.rhs[1]+=one(T)
     end
    elseif scope===:pivot
     c=v.proposal
     if edge===:nonfinite&&T<:AbstractFloat;c.column[1]=T(Inf)
     elseif edge===:mixed_precision&&T===BigFloat;c.column[1]=setprecision(()->BigFloat(c.column[1]),BigFloat,512)
     elseif edge===:dimension;v=merge(v,(proposal=J.PivotCandidate(c.entering,c.leaving_row,c.row_pivot,c.column[1:end-1],c.rho),))
     elseif edge===:alias;v=merge(v,(proposal=J.PivotCandidate(c.entering,c.leaving_row,c.row_pivot,c.column,c.column),))
     elseif edge===:perturbed;v=merge(v,(proposal=J.PivotCandidate(c.entering,c.leaving_row,-c.row_pivot,c.column,c.rho),))
     end
    else
     if edge===:nonfinite&&T<:AbstractFloat;v.w.reduced_costs[end]=T(NaN)
     elseif edge===:mixed_precision&&T===BigFloat;v.w.reduced_costs[end]=setprecision(()->BigFloat(3//7),BigFloat,512)
     elseif edge===:dimension;resize!(v.w.reduced_costs,1)
     elseif edge===:perturbed;fill!(v.w.reduced_costs,zero(T))
     end
    end
    side===:a ? (a=v) : (b=v)
   end
   z=checkpair(a,b;protect=edge!==:alias)
   if edge===:dimension&&scope in (:virtual,:virtual_transposed,:pivot);@test z[1]===:error&&z[2]===DimensionMismatch;end
   edge===:alias&&scope in (:virtual,:virtual_transposed)&&@test z[1]===:error&&z[2]===ArgumentError
   edge===:perturbed&&scope===:audit&&@test z[1]===:value&&z[2]===false
  end
  # Empty implicit system and views retain generic dispatch and guards.
  for transposed in (false,true)
   B=J._PriceAuditMatrix(spzeros(T,0,0));scope=transposed ? :virtual_transposed : :virtual
   a=(scope=scope,w=fixture(T,8,4,:audit,:sparse,:positive).w,B=B,x=T[],rhs=T[],scratch=J.SolveQualityScratch(T,0),policy=J.NumericalPolicy(T));b=merge(a,(x=T[],rhs=T[],scratch=J.SolveQualityScratch(T,0)))
   z=checkpair(a,b);@test z[1]===:value&&z[2].reliable
   a=fixture(T,8,4,scope,:sparse,:positive);b=fixture(T,8,4,scope,:sparse,:positive);a=merge(a,(x=view(a.x,:),));b=merge(b,(x=view(b.x,:),));checkpair(a,b)
  end
  # Steepest pricing may solve weights between candidates: no reuse is made
  # across those calls. Exercise the real cold weight route separately.
  a=fixture(T,8,4,:enter_dantzig,:sparse,:positive);b=fixture(T,8,4,:enter_dantzig,:sparse,:positive)
  for v in (a,b)
   v.w.options=SolverOptions(T;algorithm=:primal,pricing=:steepest_edge,verbose=false)
   fill!(v.w.scratch.steepest_valid,false)
  end
  checkpair(a,b)
 end
end
# Additional independent boundary oracles. Ordinary Test only; outside timing.
function extra_correctness(::Type{T}) where T
 @testset "Explicit free/virtual/pivot boundaries $T" begin
  for price in (T(1//4),-T(1//4),zero(T)),tol in (T(1//4),T(1//8),-T(1//8))
   a=fixture(T,8,4,:enter_dantzig,:sparse,:positive);b=fixture(T,8,4,:enter_dantzig,:sparse,:positive)
   for (mod,v) in ((VFPReference,a),(VFPB,b))
    for i in eachindex(v.w.reduced_costs);v.w.basis.states[i]==J.BASIC||(v.w.reduced_costs[i]=copy(price));end
    eligible=abs(price)>tol;expected=eligible ? (5,price<0 ? one(T) : -one(T)) : (0,zero(T))
    before=snapshot(v)
    @test same(mod._primal_entering(v.w,tol),expected)
    @test mod._pool_primal_eligible(v.w,5,tol)==eligible
    @test intact(v,before)
    # Summary uses the unchanged, valid options tolerance; all eight free
    # variables contribute the same independently known magnitude.
    active=abs(price)>v.w.options.dual_tolerance
    @test same(mod.dual_infeasibility_summary(v.w),(active ? T(8)*abs(price) : zero(T),active ? 8 : 0))
   end
  end
  triples=((T(1),T(1),zero(T),true),(T(1),T(1),T(1),false),(T(1),T(5//4),T(1//4),true),(T(1),T(5//4),T(1//8),false),(T(1),-T(1),T(1//4),false),(zero(T),zero(T),zero(T),false),(T(1),T(1),-T(1),false))
  for (x,y,e,expected) in triples
   @test VFPReference._pivot_agrees(x,y,e)==expected
   @test VFPC._pivot_agrees(x,y,e)==expected
  end
  if T<:AbstractFloat
   for x in (T(NaN),T(Inf),-T(Inf))
    @test !VFPReference._pivot_agrees(x,T(1),zero(T))
    @test !VFPC._pivot_agrees(x,T(1),zero(T))
    @test !VFPReference._pivot_agrees(T(1),T(1),x)
    @test !VFPC._pivot_agrees(T(1),T(1),x)
   end
  end
  # One real >128 pool rebuild with a hand-computed tie winner, independent
  # of the original price pattern used to create its now-invalid cache.
  for mod in (VFPReference,VFPB)
   v=fixture(T,128,4,:partial_rebuild,:sparse,:positive)
   for i in eachindex(v.w.reduced_costs);v.w.basis.states[i]==J.BASIC||(v.w.reduced_costs[i]=T(1//4));end
   J._invalidate_pricing_pool!(v.w;basis=false,costs=true)
   before=routebefore(v);z=mod._primal_entering(v.w,T(1//8))
   @test same(z,(5,-one(T)));checkroute(v,before)
  end
  for mod in (VFPReference,VFPC)
   v=fixture(T,8,4,:pivot,:sparse,:positive);pol=J.NumericalPolicy(T;recovery=true,pivot_validation=true)
   J._sync_recovery_rejections!(v.w);push!(v.w.scratch.recovery_rejections,(1,5))
   before=snapshot(v);cache=v.w.scratch.pivot_quality_cache
   @test mod.validate_pivot!(v.w,v.proposal,pol)===:reject_candidate
   @test v.w.scratch.pivot_quality_cache===cache&&intact(v,before)
  end
  # A real quality-scratch overlap must still be rejected, before any
  # proposal values can be certified. Recreate separately owned arms.
  a=fixture(T,8,4,:pivot,:dense,:mixed);b=fixture(T,8,4,:pivot,:dense,:mixed)
  for side in (:a,:b)
   v=side===:a ? a : b;c=v.proposal;q=J._pivot_quality_buffers(v.w)
   copyto!(q.column.residual,c.column)
   v=merge(v,(proposal=J.PivotCandidate(c.entering,c.leaving_row,c.row_pivot,q.column.residual,c.rho),))
   side===:a ? (a=v) : (b=v)
  end
  z=checkpair(a,b;protect=false);@test z[1]===:error&&z[2]===ArgumentError
  if T===BigFloat
   for value in (BigFloat(0),-BigFloat(0),floatmin(BigFloat),-floatmin(BigFloat),floatmax(BigFloat),-floatmax(BigFloat))
    for scope in (:virtual,:virtual_transposed,:enter_dantzig,:summary,:pivot)
     a=fixture(T,8,4,scope,:dense,:positive);b=fixture(T,8,4,scope,:dense,:positive)
     for v in (a,b)
      if scope in (:virtual,:virtual_transposed);v.x[1]=copy(value)
      elseif scope===:pivot;v.proposal.column[1]=copy(value)
      else;v.w.reduced_costs[5]=copy(value)
      end
     end
     checkpair(a,b)
    end
   end
   # A reliable tiny pivot crosses the reciprocal range boundary. Directed
   # rounding may cap overflow at floatmax; require the original decision.
   a=fixture(BigFloat,2,1,:pivot,:sparse,:positive);b=fixture(BigFloat,2,1,:pivot,:sparse,:positive)
   for side in (:a,:b)
    v=side===:a ? a : b;c=v.proposal;p=floatmin(BigFloat)
    v.w.problem.A[1,2]=BigFloat(2)*p
    v=merge(v,(proposal=J.PivotCandidate(2,1,p,[p],[BigFloat(1//2)]),))
    side===:a ? (a=v) : (b=v)
   end
   for v in (a,b)
    B=J._basis_matrix!(v.w);p=v.proposal.column[1];pol=v.w.progress.numerical_policy
    @test J.solve_quality!(J.SolveQualityScratch(BigFloat,1),B,v.proposal.column,[BigFloat(2)*p],pol).reliable
    @test J.solve_quality!(J.SolveQualityScratch(BigFloat,1),B,v.proposal.rho,[BigFloat(1)],pol;transposed=true).reliable
   end
   z=checkpair(a,b);@test z[1]===:value
   !isfinite(inv(a.proposal.column[1]))&&@test z[2]===:reject_candidate
   # The first virtual coefficient times 1/2 exercises underflow; times 2
   # exercises overflow. Compare the internal unsafe flag and full quality,
   # never accepting a nonfinite result as a usable certificate.
   for coefficient in (floatmin(BigFloat),floatmax(BigFloat)),factor in (BigFloat(1//2),BigFloat(2)),transposed in (false,true)
    B=J._PriceAuditMatrix(sparse(reshape([coefficient],1,1)))
    x=fill(factor,transposed ? 2 : 3);rhs=zeros(BigFloat,transposed ? 3 : 2)
    sr=J.SolveQualityScratch(BigFloat,length(rhs));sn=J.SolveQualityScratch(BigFloat,length(rhs))
    old=VFPReference._quality_components!(sr.work_residual,sr.work_scale,sr.terms,B,x,rhs,transposed)
    new=VFPA._quality_components!(sn.work_residual,sn.work_scale,sn.terms,B,x,rhs,transposed)
    @test old==new
    product=coefficient*factor
    @test old==(!iszero(coefficient)&&!iszero(factor)&&abs(product)<floatmin(BigFloat))
    @test same(qualityout(sr),qualityout(sn))
    qo=VFPReference.solve_quality!(sr,B,x,rhs,J.NumericalPolicy(BigFloat);transposed)
    qn=VFPA.solve_quality!(sn,B,x,rhs,J.NumericalPolicy(BigFloat);transposed)
    @test same(qo,qn)&&same(qualityout(sr),qualityout(sn))
    @test !qo.reliable
    (!isfinite(product)||old)&&@test !qo.finite
   end
  end
 end
end
function native_direction_oracle(v)
 B=Matrix(v.w.problem.A[:,v.w.basis.basic_indices]);x=v.proposal.column
 rhs=Vector(v.w.problem.A[:,v.proposal.entering]);q=Rational{BigInt}
 M=q.(B);z=q.(x);b=q.(rhs);wanted=q.(v.wanted)
 residual=M*z-b
 scale=max(q(1),maximum(sum(abs(M[i,j]) for j in axes(M,2)) for i in axes(M,1))*maximum(abs,z),maximum(abs,b))
 bound=8*q(eps(Float64))*scale
 construction=M*wanted==b
 passed=construction&&maximum(abs,residual)<=bound
 passed
end

@testset "BigFloat virtual audit free pricing and checked pivots" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do;correctness(BigFloat);extra_correctness(BigFloat);end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);extra_correctness(T);end
 setprecision(BigFloat,128) do
  setrounding(BigFloat,RoundNearest) do
   for scope in (:audit,:virtual,:enter_dantzig,:summary,:pivot)
    @testset "Whole-call allocation $scope" begin
     a=fixture(BigFloat,128,16,scope,:dense,:positive);b=fixture(BigFloat,128,16,scope,:dense,:positive);arm=armfor(scope);s=Val(scope)
     for k in 1:3,(method,v) in ((Val(:original),a),(Val(arm),b));reset!(v);timed(method,s,v);end
     pairs=Tuple{Dict{String,Any},Dict{String,Any}}[]
     for k in 1:3
      if isodd(k);reset!(a);old=timed(Val(:original),s,a);reset!(b);new=timed(Val(arm),s,b)
      else;reset!(b);new=timed(Val(arm),s,b);reset!(a);old=timed(Val(:original),s,a)
      end
      @test old["compile_seconds"]==old["recompile_seconds"]==new["compile_seconds"]==new["recompile_seconds"]==0
      push!(pairs,(old,new))
     end
     @test all(new["bytes"]<old["bytes"]&&new["events"]<old["events"] for (old,new) in pairs) # RED whole-call cost gate
    end
   end
  end
 end
end
end
