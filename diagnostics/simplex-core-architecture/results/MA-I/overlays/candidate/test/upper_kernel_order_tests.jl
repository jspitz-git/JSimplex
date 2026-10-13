# Retain the former scalar loop as a numerical-order reference, including the
# fallback for a stored diagonal that is not the last entry of a column.
function upper_order_reference!(x, upper, columns, transposed, order=nothing)
    for j in (transposed ? columns : Iterators.reverse(columns))
        c = upper[j]
        diagonal = isnothing(order) ? j : order.order[j]
        ids = isnothing(order) ? c.indices : c.indices.ids
        value = transposed ? x[diagonal] : x[diagonal] / JSimplex._upper_diagonal(c, j)
        transposed || (x[diagonal] = value)
        for k in eachindex(ids)
            row = ids[k]
            row == diagonal && continue
            if transposed
                value -= c.values[k] * x[row]
            else
                x[row] -= c.values[k] * value
            end
        end
        transposed && (x[diagonal] = value / JSimplex._upper_diagonal(c, j))
    end
    x
end

@testset "Upper solve preserves coefficient order and fallback" begin
    for T in (Float16, Float32, Float64, BigFloat, Rational{Int}, Rational{BigInt}),
        stable in (false, true), transposed in (false, true)
        order = JSimplex.UpperRowOrder(4)
        if stable
            JSimplex._rotate_upper_order!(order, 1, 4)
        end
        for layout in (:triangular, :diagonal_not_last)
            rows = [[1], [1,2], [1,2,3], [1,2,3,4]]
            values = [T[2], T[1//4,2], T[1//8,-1//4,2], T[1//2,-1//8,1//4,2]]
            if layout === :diagonal_not_last
                push!(rows[2],4); push!(values[2],T(1//8))
            end
            upper = [JSimplex.PackedUpperColumn{T}(
                stable ? JSimplex.UpperRowIndices(order.order[r],order) : r,v)
                for (r,v) in zip(rows,values)]
            for columns in (1:4, [1,3,4], Int[]), rhs in (T[1,-2,3,0],zeros(T,4))
                expected=copy(rhs); actual=copy(rhs)
                upper_order_reference!(expected,upper,columns,transposed,stable ? order : nothing)
                if stable
                    if transposed
                        JSimplex._stable_upper_transpose_solve!(actual,upper,columns,order)
                    else
                        JSimplex._stable_upper_backsolve_physical!(actual,upper,columns,order)
                    end
                else
                    solve! = transposed ? JSimplex._upper_transpose_solve! : JSimplex._upper_backsolve!
                    solve!(actual,upper,columns)
                end
                @test isequal(actual,expected)
            end
        end
    end
end
