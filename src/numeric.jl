_supported_value_type(::Type{T}) where {T} =
    isconcretetype(T) && (T <: AbstractFloat || T <: Rational)

_is_exact(::Type{<:Rational}) = Val(true)
_is_exact(::Type{<:AbstractFloat}) = Val(false)

_typed_ratio(::Type{T}, numerator::Integer, denominator::Integer) where {T<:Real} =
    T(numerator // denominator)

struct Bound{T<:Real}
    value::T
    bounded::Bool

    function Bound{T}(value::T, bounded::Bool) where {T<:Real}
        bounded && !isfinite(value) &&
            throw(ArgumentError("a finite bound must contain a finite value"))
        return new{T}(bounded ? value : zero(T), bounded)
    end
end

Bound(value::T) where {T<:Real} = Bound{T}(value, true)
Bound{T}(value::Real) where {T<:Real} = Bound{T}(T(value), true)
Bound{T}(::Nothing) where {T<:Real} = Bound{T}(zero(T), false)

_finite_bound(::Type{T}, value) where {T<:Real} = Bound{T}(T(value), true)
_unbounded_bound(::Type{T}) where {T<:Real} = Bound{T}(zero(T), false)

Base.isfinite(bound::Bound) = bound.bounded
Base.:(==)(left::Bound, right::Bound) =
    left.bounded == right.bounded && (!left.bounded || left.value == right.value)
Base.isequal(left::Bound, right::Bound) =
    left.bounded == right.bounded && (!left.bounded || isequal(left.value, right.value))
Base.hash(bound::Bound, seed::UInt) =
    bound.bounded ? hash(bound.value, hash(true, hash(:Bound, seed))) :
                    hash(false, hash(:Bound, seed))

function bound_value(bound::Bound)
    isfinite(bound) || throw(ArgumentError("an unbounded bound has no finite value"))
    return bound.value
end

function _normalize_bound(::Type{T}, input, side::Symbol, label::AbstractString) where {T<:Real}
    _supported_value_type(T) || throw(ArgumentError("unsupported value type for $label: $T"))
    input isa Bound && !isfinite(input) && return _unbounded_bound(T)
    input === nothing && return _unbounded_bound(T)
    input isa Bound && return _finite_bound(T, bound_value(input))

    input isa Real || throw(ArgumentError("$label must be a real value or nothing"))
    if isnan(input)
        throw(ArgumentError("$label cannot be NaN"))
    elseif isinf(input)
        if input > 0
            side === :upper || throw(ArgumentError("$label cannot be +Inf"))
        else
            side === :lower || throw(ArgumentError("$label cannot be -Inf"))
        end
        return _unbounded_bound(T)
    end
    return _finite_bound(T, input)
end
