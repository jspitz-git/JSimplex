using JSimplex, Serialization, SparseArrays, LinearAlgebra, TOML
@eval JSimplex begin
function _checked_upper_backsolve!(vector::Vector{T}, upper::Vector{PackedUpperColumn{T}},
                           columns=eachindex(upper)) where {T}
    for column_index in Iterators.reverse(columns)
        column = upper[column_index]
        value = vector[column_index] / _upper_value(column, column_index)
        vector[column_index] = value
        for index in eachindex(column.indices)
            row = column.indices[index]
            row == column_index && continue
            vector[row] -= column.values[index] * value
        end
    end
    return vector
end

end
@eval JSimplex begin
function _checked_upper_transpose_solve!(vector::Vector{T}, upper::Vector{PackedUpperColumn{T}},
                                 columns=eachindex(upper)) where {T}
    for column_index in columns
        column = upper[column_index]
        value = vector[column_index]
        for index in eachindex(column.indices)
            row = column.indices[index]
            row == column_index && continue
            value -= column.values[index] * vector[row]
        end
        vector[column_index] = value / _upper_value(column, column_index)
    end
    return vector
end

end
@eval JSimplex begin
function _checked_prepare_spike!(factor::AbstractTriangularBasisFactorization{T},
                         tableau_column::AbstractVector, pivot_row::Integer,
                         zero_tolerance::Real) where {T}
    tolerance = convert(T, zero_tolerance)
    isfinite(tolerance) && tolerance >= zero(T) ||
        throw(ArgumentError("zero_tolerance must be finite and nonnegative"))
    n = _backend_dimension(factor.base)
    length(tableau_column) == n ||
        throw(DimensionMismatch("tableau column length must match the basis dimension"))
    pivot = Int(pivot_row)
    checkbounds(tableau_column, pivot)
    _pivot_magnitude(convert(T, tableau_column[pivot])) > tolerance ||
        throw(LinearAlgebra.ZeroPivotException(pivot))
    position = factor.positions[pivot]
    fill!(factor.spike, zero(T))
    for column_index in 1:n
        column = factor.upper[column_index]
        value = convert(T, tableau_column[factor.column_order[column_index]])
        for index in eachindex(column.indices)
            factor.spike[column.indices[index]] += column.values[index] * value
        end
    end
    return position
end

end

function trial(kernel, f, rhs, direction)
    if kernel === :spike
        return JSimplex._prepare_spike!(f,direction,1,0.0)
    elseif kernel === :back
        copyto!(f.work,rhs); return JSimplex._upper_backsolve!(f.work,f.upper)
    else
        copyto!(f.work,rhs); return JSimplex._upper_transpose_solve!(f.work,f.upper)
    end
end
function checked(kernel, f, rhs, direction)
    if kernel === :spike
        return JSimplex._checked_prepare_spike!(f,direction,1,0.0)
    elseif kernel === :back
        copyto!(f.work,rhs); return JSimplex._checked_upper_backsolve!(f.work,f.upper)
    else
        copyto!(f.work,rhs); return JSimplex._checked_upper_transpose_solve!(f.work,f.upper)
    end
end
function main()
    data=deserialize(ARGS[1]);m,n=size(data.A)
    augmented=hcat(data.A,spdiagm(0=>-ones(m)))
    f=JSimplex.BartelsGolubFactorization(augmented[:,data.basis]);direction=zeros(m)
    for (row,entering) in data.steps
        JSimplex.forward_solve!(direction,f,Vector(augmented[:,entering]))
        JSimplex.replace_column!(f,direction,row)
    end
    direction.=1.0;rhs=ones(m);records=[]
    for kernel in (:spike,:back,:transpose)
        checked(kernel,f,rhs,direction);expected=copy(kernel===:spike ? f.spike : f.work)
        trial(kernel,f,rhs,direction);@assert isequal(expected,kernel===:spike ? f.spike : f.work)
        old=Float64[];new=Float64[]
        for repeat in 1:20
            push!(old,@elapsed(for _ in 1:10;checked(kernel,f,rhs,direction);end))
            push!(new,@elapsed(for _ in 1:10;trial(kernel,f,rhs,direction);end))
        end
        push!(records,Dict("kernel"=>string(kernel),"checked_seconds"=>minimum(old)/10,
            "candidate_seconds"=>minimum(new)/10,"exact_match"=>true))
    end
    TOML.print(stdout,Dict("samples"=>records,"julia"=>string(VERSION),"iteration"=>data.iteration,"updates"=>length(data.steps)))
end
main()
