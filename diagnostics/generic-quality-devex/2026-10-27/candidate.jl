module SavingsCandidate
using JSimplex,SparseArrays
using JSimplex: SimplexWorkspace,_pipeline_changed!,_primal_direction_magnitude,
    SolveQualityScratch,NumericalPolicy,SolveQuality,_stored_quality_bits,
    _quality_roundoff,_quality_values,_is_exact,_compensated_solve_quality!,
    _floating_quality!,_primal_store_rational_weight,_primal_devex_leaving_weight,
    _pipeline_unit_rhs!,_checked_basis_solve!,price!,BASIC
function _dual_direction_residual_ok!(workspace::SimplexWorkspace{T},
                                      direction::Vector{T}, pivot::T) where {T<:AbstractFloat}
    A = workspace.problem.A
    row_count, column_count = size(A)
    length(direction) == length(workspace.basis.basic_indices) == row_count &&
        length(workspace.scratch.tau) == length(workspace.scratch.row_rhs) == row_count ||
        throw(DimensionMismatch("direction residual vectors must match the row count"))
    residual = workspace.scratch.tau
    scale = workspace.scratch.row_rhs
    _pipeline_changed!(workspace,residual)
    _pipeline_changed!(workspace,scale)
    @inbounds for row in eachindex(residual)
        rhs = scale[row]
        residual[row] = -rhs
        scale[row] = abs(rhs)
    end
    for (basis_row, index) in enumerate(workspace.basis.basic_indices)
        1 <= index <= column_count + row_count || throw(BoundsError(workspace.primal, index))
        value = @inbounds direction[basis_row]
        if index <= column_count
            @inbounds for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                row = A.rowval[position]
                term = A.nzval[position] * value
                residual[row] += term
                scale[row] += abs(term)
            end
        else
            row = index - column_count
            @inbounds residual[row] -= value
            @inbounds scale[row] += abs(value)
        end
    end
    roundoff = T(256) * eps(one(T))
    pivot_tolerance = sqrt(eps(one(T))) * abs(pivot)
    @inbounds for row in eachindex(residual)
        isfinite(residual[row]) && isfinite(scale[row]) || return false
        tolerance = max(workspace.options.zero_tolerance, pivot_tolerance,
                        roundoff * (scale[row] + one(T)))
        abs(residual[row]) <= tolerance || return false
    end
    return true
end

function _dual_direction_residual_ok!(workspace::SimplexWorkspace{T},
                                      direction::Vector{T}, pivot::T) where {T<:BigFloat}
    A = workspace.problem.A
    row_count, column_count = size(A)
    length(direction) == length(workspace.basis.basic_indices) == row_count &&
        length(workspace.scratch.tau) == length(workspace.scratch.row_rhs) == row_count ||
        throw(DimensionMismatch("direction residual vectors must match the row count"))
    residual = workspace.scratch.tau
    scale = workspace.scratch.row_rhs
    _pipeline_changed!(workspace,residual)
    _pipeline_changed!(workspace,scale)
    @inbounds for row in eachindex(residual)
        rhs = scale[row]
        residual[row] = -rhs
        scale[row] = _primal_direction_magnitude(rhs)
    end
    for (basis_row, index) in enumerate(workspace.basis.basic_indices)
        1 <= index <= column_count + row_count || throw(BoundsError(workspace.primal, index))
        value = @inbounds direction[basis_row]
        if index <= column_count
            @inbounds for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                row = A.rowval[position]
                term = A.nzval[position] * value
                residual[row] += term
                scale[row] += _primal_direction_magnitude(term)
            end
        else
            row = index - column_count
            @inbounds residual[row] -= value
            @inbounds scale[row] += _primal_direction_magnitude(value)
        end
    end
    roundoff = T(256) * eps(one(T))
    pivot_tolerance = sqrt(eps(one(T))) * _primal_direction_magnitude(pivot)
    @inbounds for row in eachindex(residual)
        isfinite(residual[row]) && isfinite(scale[row]) || return false
        tolerance = max(workspace.options.zero_tolerance, pivot_tolerance,
                        roundoff * (scale[row] + Clong(1)))
        _primal_direction_magnitude(residual[row]) <= tolerance || return false
    end
    return true
end

function _dual_row_residual_ratio(workspace::SimplexWorkspace{T},
                                  rho::Vector{T}, leaving_row::Int) where {T<:AbstractFloat}
    A = workspace.problem.A
    row_count, column_count = size(A)
    length(rho) == length(workspace.basis.basic_indices) == row_count ||
        throw(DimensionMismatch("tableau residual vectors must match the row count"))
    roundoff = T(256) * eps(one(T))
    worst_ratio = zero(T)
    for (basis_row, index) in enumerate(workspace.basis.basic_indices)
        1 <= index <= column_count + row_count || throw(BoundsError(workspace.primal, index))
        expected = basis_row == leaving_row ? one(T) : zero(T)
        residual = -expected
        scale = expected
        if index <= column_count
            @inbounds for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                term = A.nzval[position] * rho[A.rowval[position]]
                residual += term
                scale += abs(term)
            end
        else
            term = @inbounds -rho[index - column_count]
            residual += term
            scale += abs(term)
        end
        isfinite(residual) && isfinite(scale) || return T(Inf)
        tolerance = max(workspace.options.zero_tolerance,
                        roundoff * (scale + one(T)))
        isfinite(tolerance) || return T(Inf)
        worst_ratio = max(worst_ratio, abs(residual) / tolerance)
    end
    return worst_ratio
end

function _dual_row_residual_ratio(workspace::SimplexWorkspace{T},
                                  rho::Vector{T}, leaving_row::Int) where {T<:BigFloat}
    A = workspace.problem.A
    row_count, column_count = size(A)
    length(rho) == length(workspace.basis.basic_indices) == row_count ||
        throw(DimensionMismatch("tableau residual vectors must match the row count"))
    roundoff = T(256) * eps(one(T))
    worst_ratio = zero(T)
    for (basis_row, index) in enumerate(workspace.basis.basic_indices)
        1 <= index <= column_count + row_count || throw(BoundsError(workspace.primal, index))
        expected = basis_row == leaving_row ? one(T) : zero(T)
        residual = -expected
        scale = expected
        if index <= column_count
            @inbounds for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                term = A.nzval[position] * rho[A.rowval[position]]
                residual += term
                scale += _primal_direction_magnitude(term)
            end
        else
            term = @inbounds -rho[index - column_count]
            residual += term
            scale += _primal_direction_magnitude(term)
        end
        isfinite(residual) && isfinite(scale) || return T(Inf)
        tolerance = max(workspace.options.zero_tolerance,
                        roundoff * (scale + Clong(1)))
        isfinite(tolerance) || return T(Inf)
        worst_ratio = max(worst_ratio, _primal_direction_magnitude(residual) / tolerance)
    end
    return worst_ratio
end

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
    scale[target] += _primal_direction_magnitude(product)
    terms[target] += 2
    if !iszero(a) && !iszero(x[source])
        if limit === nothing
            limit = floatmin(BigFloat)
        end
        return _primal_direction_magnitude(product) < limit, limit
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


_primal_devex_candidate_weight(coefficient::T, leaving_weight::T) where {T<:AbstractFloat} =
    min(floatmax(T), abs(coefficient) * leaving_weight)
_primal_devex_candidate_weight(coefficient::T, leaving_weight::T) where {T<:Rational} =
    _primal_store_rational_weight(T, big(coefficient)^2 * big(leaving_weight))

_primal_devex_candidate_weight(coefficient::BigFloat,leaving_weight::BigFloat) = begin
    product = _primal_direction_magnitude(coefficient) * leaving_weight
    isinf(product) && !signbit(product) ? floatmax(BigFloat) : product
end
function _primal_update_devex!(workspace::SimplexWorkspace{T}, entering::Int,
                               leaving_row::Int, pivot::T; shared_row::Bool=false) where {T}
    tableau_row = workspace.scratch.tableau_row
    if !shared_row
        unit = _pipeline_unit_rhs!(workspace,leaving_row)
        rho = _checked_basis_solve!(workspace.scratch.rho,workspace,unit;
                                    transposed=true,operation=:weight_btran,unit_row=leaving_row)
        price!(tableau_row, workspace, rho)
    end
    leaving = workspace.basis.basic_indices[leaving_row]
    leaving_weight = _primal_devex_leaving_weight(
        workspace.pricing_weights[entering], pivot,
    )
    for index in eachindex(workspace.basis.states)
        (index == entering || workspace.basis.states[index] == BASIC) && continue
        workspace.pricing_weights[index] = max(
            workspace.pricing_weights[index],
            _primal_devex_candidate_weight(tableau_row[index], leaving_weight),
        )
    end
    workspace.pricing_weights[leaving] = leaving_weight
    return nothing
end

end
