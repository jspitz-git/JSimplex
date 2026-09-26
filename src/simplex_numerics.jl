# Internal numerical quality is separate from user feasibility tolerances.
const NUMERICAL_SWITCHES = (
    :stable_ratio, :pivot_validation, :solve_refinement, :recovery, :feasibility_recovery, :incremental_primal, :incremental_primal_pivots, :adaptive_refactor,
    :adaptive_stalling, :adaptive_dual_perturbation,:adaptive_primal_perturbation, :adaptive_pricing, :partial_pricing, :sparse_pricing, :hypersparse,
    :crash, :phase_one, :precision_boosting, :lp_refinement,
)
const IMPLEMENTED_NUMERICAL_SWITCHES = (:stable_ratio,:pivot_validation,:solve_refinement,:recovery,:feasibility_recovery,:incremental_primal,:incremental_primal_pivots,:adaptive_refactor,:adaptive_stalling,:adaptive_dual_perturbation,:adaptive_primal_perturbation,:adaptive_pricing,:partial_pricing,:sparse_pricing,:hypersparse,:crash,:phase_one,:precision_boosting,:lp_refinement)

struct NumericalPolicy{T<:Real}
    solve_tolerance::T
    pivot_error_tolerance::T
    max_refinements::Int
    max_pivot_candidates::Int
    max_recovery_rounds::Int
    stagnation_window::Int
    max_precision_bits::Int
    max_precision_memory_bytes::Int
    max_lp_refinements::Int
    stable_ratio::Bool
    pivot_validation::Bool
    solve_refinement::Bool
    recovery::Bool
    feasibility_recovery::Bool
    incremental_primal::Bool
    incremental_primal_pivots::Bool
    adaptive_refactor::Bool
    refactor_timing::Bool
    adaptive_stalling::Bool
    adaptive_dual_perturbation::Bool
    adaptive_primal_perturbation::Bool
    adaptive_pricing::Bool
    partial_pricing::Bool
    sparse_pricing::Bool
    hypersparse::Bool
    crash::Bool
    phase_one::Bool
    precision_boosting::Bool
    lp_refinement::Bool
end

function NumericalPolicy(::Type{T}; simplex_strategy::Symbol=:legacy,
    solve_tolerance=nothing, pivot_error_tolerance=nothing,
    max_refinements::Integer=3, max_pivot_candidates::Integer=8,
    max_recovery_rounds::Integer=2, stagnation_window::Integer=64,
    max_precision_bits::Integer=512, max_precision_memory_bytes::Integer=1<<30,
    max_lp_refinements::Integer=8,
    stable_ratio::Bool=(simplex_strategy == :adaptive), recovery::Bool=(simplex_strategy == :adaptive),
    incremental_primal::Bool=(simplex_strategy == :adaptive),
    incremental_primal_pivots::Bool=(simplex_strategy == :adaptive),
    pivot_validation::Bool=(simplex_strategy == :adaptive),
    solve_refinement::Bool=(simplex_strategy == :adaptive),
    feasibility_recovery::Bool=(simplex_strategy == :adaptive),
    adaptive_refactor::Bool=(simplex_strategy == :adaptive), refactor_timing::Bool=true,
    adaptive_stalling::Bool=(simplex_strategy == :adaptive),
    adaptive_dual_perturbation::Bool=(simplex_strategy == :adaptive),
    adaptive_primal_perturbation::Bool=(simplex_strategy == :adaptive),
    adaptive_pricing::Bool=(simplex_strategy == :adaptive), partial_pricing::Bool=(simplex_strategy == :adaptive), sparse_pricing::Bool=false, hypersparse::Bool=false,
    crash::Bool=false, phase_one::Bool=false, precision_boosting::Bool=false,
    lp_refinement::Bool=false,
) where {T}
    _supported_value_type(T) || throw(ArgumentError("Unsupported numerical policy type $T"))
    simplex_strategy in (:legacy,:adaptive) || throw(ArgumentError("Unknown simplex strategy"))
    exact = _is_exact(T) === Val(true)
    default_solve = exact ? zero(T) : T(256)*eps(T)
    exact || default_solve < one(T) ||
        throw(ArgumentError("Insufficient precision for the numerical error bound"))
    solve_limit = isnothing(solve_tolerance) ? default_solve : convert(T, solve_tolerance)
    pivot_limit = isnothing(pivot_error_tolerance) ?
        (exact ? zero(T) : sqrt(eps(T))) : convert(T, pivot_error_tolerance)
    if exact
        iszero(solve_limit) && iszero(pivot_limit) ||
            throw(ArgumentError("Exact solve and pivot error tolerances must be zero"))
    else
        all(t -> isfinite(t) && zero(T) < t < one(T), (solve_limit,pivot_limit)) ||
            throw(ArgumentError("Numerical error tolerances must be finite and between zero and one"))
    end
    all(>=(0), (max_refinements,max_recovery_rounds,max_lp_refinements)) &&
        max_pivot_candidates > 0 && stagnation_window > 0 && max_precision_bits >= 2 &&
        0 <= max_precision_memory_bytes <= typemax(Int) ||
        throw(ArgumentError("Invalid numerical recovery limits"))
    switches = (stable_ratio,pivot_validation,solve_refinement,recovery,feasibility_recovery,incremental_primal,incremental_primal_pivots,adaptive_refactor,
        adaptive_stalling,adaptive_dual_perturbation,adaptive_primal_perturbation,adaptive_pricing,partial_pricing,sparse_pricing,hypersparse,crash,
        phase_one,precision_boosting,lp_refinement)
    for (name, enabled) in zip(NUMERICAL_SWITCHES,switches)
        enabled && !(name in IMPLEMENTED_NUMERICAL_SWITCHES) &&
            throw(ArgumentError("Numerical stage $name is not implemented"))
    end
    # Stage switches remain disabled by default until their implementations land.
    return NumericalPolicy{T}(solve_limit,pivot_limit,Int(max_refinements),
        Int(max_pivot_candidates),Int(max_recovery_rounds),Int(stagnation_window),
        Int(max_precision_bits),Int(max_precision_memory_bytes),Int(max_lp_refinements),stable_ratio,pivot_validation,solve_refinement,recovery,feasibility_recovery,
        incremental_primal,incremental_primal_pivots,adaptive_refactor,refactor_timing,adaptive_stalling,adaptive_dual_perturbation,adaptive_primal_perturbation,adaptive_pricing,
        partial_pricing,sparse_pricing,hypersparse,crash,phase_one,precision_boosting,lp_refinement)
end

NumericalPolicy(::Type{T}, options::SolverOptions) where {T} =
    NumericalPolicy(T; simplex_strategy=options.simplex_strategy)

struct SolveQuality{T<:Real}
    absolute_error::T
    relative_error::Union{Nothing,T}
    finite::Bool
    reliable::Bool
end

struct SolveQualityScratch{T,W}
    residual::Vector{T}
    work_residual::Vector{W}
    work_scale::Vector{W}
    terms::Vector{Int}
    compensation::Vector{W}
    error_sum::Vector{W}
end

function SolveQualityScratch(::Type{T}, rows::Integer) where {T}
    rows >= 0 || throw(ArgumentError("Negative residual dimension"))
    W = T
    return SolveQualityScratch(zeros(T,rows), zeros(W,rows), zeros(W,rows), zeros(Int,rows), W[], W[])
end

# Error-free product (FMA) and TwoSum, followed by compensated accumulation.
# The enclosure is Dot2Err, Algorithm 5.8 of Ogita/Rump/Oishi (2005), including
# its underflow allowance. No reassociation or fast-math is permitted here.
@inline function _compensated_quality_term!(scratch, a::T, x::T, target) where T
    (iszero(a) || iszero(x)) && return nothing
    h = -a*x
    product_error = fma(-a,x,-h)
    old = scratch.work_residual[target]
    total = old+h
    part = total-old
    sum_error = (old-(total-part))+(h-part)
    correction = sum_error+product_error
    scratch.work_residual[target] = total
    scratch.compensation[target] += correction
    scratch.error_sum[target] += abs(correction)
    scratch.work_scale[target] += abs(h)
    scratch.terms[target] += 2
    return nothing
end

function _compensated_quality_components!(scratch,B,x,transposed)
    if B isa SparseMatrixCSC
        for column in axes(B,2), p in nzrange(B,column)
            row = B.rowval[p]
            target,source = transposed ? (column,row) : (row,column)
            _compensated_quality_term!(scratch,B.nzval[p],x[source],target)
        end
    else
        for column in axes(B,2), row in axes(B,1)
            target,source = transposed ? (column,row) : (row,column)
            _compensated_quality_term!(scratch,B[row,column],x[source],target)
        end
    end
    return nothing
end

function _compensated_solve_quality!(scratch::SolveQualityScratch{T},B,x,rhs,policy,
                                     transposed) where {T<:Union{Float32,Float64}}
    rounding(T) == RoundNearest || return nothing
    # Error-free products and Dot2Err's underflow allowance require gradual
    # underflow. A caller may have enabled a thread-local flush-to-zero mode.
    get_zero_subnormals() && return nothing
    resize!(scratch.compensation,length(rhs))
    resize!(scratch.error_sum,length(rhs))
    fill!(scratch.compensation,zero(T))
    fill!(scratch.error_sum,zero(T))
    for i in eachindex(rhs)
        scratch.work_residual[i] = rhs[i]
        scratch.work_scale[i] = abs(rhs[i])
        scratch.terms[i] = 1
    end
    _compensated_quality_components!(scratch,B,x,transposed)
    u = eps(T)/2
    absolute = relative = zero(T)
    accepted = true
    rejected = false
    for i in eachindex(rhs)
        residual = scratch.work_residual[i]+scratch.compensation[i]
        scale = scratch.work_scale[i]
        error_sum = scratch.error_sum[i]
        all(isfinite,(residual,scale,error_sum)) || return nothing
        # Account for rounding in the positive componentwise scale as well.
        # eps(T) (twice unit roundoff) leaves slack in this computed gamma.
        k = T(scratch.terms[i])*eps(T)
        k < T(1)/4 || return nothing
        gamma = k/(one(T)-k)
        n = T(1+(scratch.terms[i]-1)÷2)
        delta = (n*u)/(one(T)-2*n*u)
        error = (u*abs(residual)+(delta*error_sum+3*nextfloat(zero(T))/u))/(one(T)-2*u)
        if iszero(scale)
            # Nonzero products may have underflowed to zero; the native check
            # cannot distinguish those from a truly homogeneous zero row.
            scratch.terms[i] == 1 && iszero(residual) || return nothing
            ratio = zero(T)
        else
            lower_scale = prevfloat(scale*(one(T)-gamma))
            upper_scale = nextfloat(scale/(one(T)-gamma))
            lower_scale > zero(T) && isfinite(upper_scale) || return nothing
            upper_error = nextfloat((nextfloat(abs(residual)+error))/lower_scale)
            lower_error = prevfloat(max(zero(T),prevfloat(abs(residual)-error))/upper_scale)
            accepted &= upper_error <= policy.solve_tolerance
            rejected |= lower_error > policy.solve_tolerance
            ratio = abs(residual)/scale
        end
        scratch.residual[i] = residual
        absolute = max(absolute,abs(residual))
        relative = max(relative,ratio)
    end
    # Only an ambiguous enclosure needs arbitrary precision. A demonstrably
    # bad residual can proceed directly to an ordinary working-type correction.
    accepted || rejected || return nothing
    return SolveQuality{T}(absolute,relative,true,accepted)
end

_compensated_solve_quality!(scratch,B,x,rhs,policy,transposed) = nothing

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

struct _UnreliableBasisSolve <: Exception end
Base.showerror(io::IO,::_UnreliableBasisSolve) = print(io,"basis solve refinement did not meet the numerical error bound")
