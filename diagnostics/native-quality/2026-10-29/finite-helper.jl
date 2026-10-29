_finite_values(values,::Val{P}) where P =
    all(value -> isfinite(value) && (!P || value > zero(value)),values)

function _finite_values(values::Vector{T},::Val{P}) where {T<:Union{Float32,Float64},P}
    valid = true
    # A boolean reduction vectorizes without changing any floating arithmetic.
    # Every value still participates, including the final partial vector block.
    @inbounds @simd for i in eachindex(values)
        value = values[i]
        valid &= isfinite(value) & (!P || value > zero(T))
    end
    return valid
end

