# Propagation's native-float arithmetic keeps small exact values in Int128.
# Every overflow check falls back to the original BigInt rational arithmetic;
# the stored floating endpoints still pass through _propagation_bound.
module _SmallExact

const JS = parentmodule(@__MODULE__)
const Q = Rational{BigInt}
const S = Rational{Int128}

struct E <: Real
    v::Union{S,Q}
    E(v::Union{S,Q}, ::Val{:raw}) = new(v)
end

raw(x::Union{S,Q}) = E(x, Val(:raw))
E(x::E) = x
E(x::S) = raw(x)
function E(x::Q)
    n, d = numerator(x), denominator(x)
    if typemin(Int128) < n <= typemax(Int128) && 0 < d <= typemax(Int128)
        return raw(S(Int128(n), Int128(d)))
    end
    return raw(x)
end
E(x::Integer) = typemin(Int128) < x <= typemax(Int128) ? raw(S(Int128(x))) : raw(Q(x))
E(x::Rational) = E(Q(x))

function E(x::T) where {T<:Union{Float32,Float64}}
    !isfinite(x) && return raw(JS._exact_rational(x))
    iszero(x) && return raw(S(0))
    if T === Float64
        bits = reinterpret(UInt64, x)
        exponent = Int((bits >> 52) & 0x7ff)
        mantissa = bits & 0x000fffffffffffff
        if exponent == 0
            exponent = -1074
        else
            mantissa |= UInt64(1) << 52
            exponent -= 1075
        end
    else
        bits = reinterpret(UInt32, x)
        exponent = Int((bits >> 23) & 0xff)
        mantissa = UInt64(bits & 0x007fffff)
        if exponent == 0
            exponent = -149
        else
            mantissa |= UInt64(1) << 23
            exponent -= 150
        end
    end
    shift = trailing_zeros(mantissa)
    mantissa >>= shift
    exponent += shift
    if -126 <= exponent <= 126
        n = Int128(mantissa)
        signbit(x) && (n = -n)
        if exponent >= 0
            num, overflow = Base.mul_with_overflow(n, Int128(1) << exponent)
            !overflow && num != typemin(Int128) && return raw(S(num))
        else
            return raw(S(n, Int128(1) << (-exponent)))
        end
    end
    return raw(JS._exact_rational(x))
end

E(x::Real) = raw(JS._exact_rational(x))
wide(x::E) = x.v isa Q ? x.v : Q(x.v)
is_small(x::E) = x.v isa S
Base.convert(::Type{E}, x::Real) = E(x)
Base.convert(::Type{E}, x::E) = x
Base.zero(::Type{E}) = raw(S(0))
Base.one(::Type{E}) = raw(S(1))
Base.zero(x::E) = zero(E)
Base.one(x::E) = one(E)
Base.iszero(x::E) = iszero(x.v)
Base.isone(x::E) = isone(x.v)
Base.isfinite(x::E) = isfinite(x.v)
Base.numerator(x::E) = numerator(x.v)
Base.denominator(x::E) = denominator(x.v)

@inline function normalized(n::Int128, d::Int128)
    (n == typemin(Int128) || d == typemin(Int128) || d == 0) && return nothing
    if d < 0
        n = -n
        d = -d
    end
    return S(n, d)
end

@inline function small_binary(op, a::S, b::S)
    an, ad = numerator(a), denominator(a)
    bn, bd = numerator(b), denominator(b)
    (ad <= 0 || bd <= 0 || an == typemin(Int128) || bn == typemin(Int128)) && return nothing
    if op == Base.:+ || op == Base.:-
        xd, yd = Base.divgcd(ad, bd)
        x, ox = Base.mul_with_overflow(an, yd)
        ox && return nothing
        y, oy = Base.mul_with_overflow(bn, xd)
        oy && return nothing
        n, on = op == Base.:+ ? Base.add_with_overflow(x, y) : Base.sub_with_overflow(x, y)
        on && return nothing
        d, od = Base.mul_with_overflow(ad, yd)
        od && return nothing
    elseif op == Base.:*
        xn, yd = Base.divgcd(an, bd)
        xd, yn = Base.divgcd(ad, bn)
        n, on = Base.mul_with_overflow(xn, yn)
        on && return nothing
        d, od = Base.mul_with_overflow(xd, yd)
        od && return nothing
    else
        bn == 0 && return nothing
        xn, yn = Base.divgcd(an, bn)
        xd, yd = Base.divgcd(ad, bd)
        n, on = Base.mul_with_overflow(xn, yd)
        on && return nothing
        d, od = Base.mul_with_overflow(xd, yn)
        od && return nothing
    end
    return normalized(n, d)
end

@inline function binary(op, a::E, b::E)
    if a.v isa S && b.v isa S
        value = small_binary(op, a.v, b.v)
        !isnothing(value) && return raw(value)
    end
    return raw(op(wide(a), wide(b)))
end

for op in (:+, :-, :*, :/)
    @eval Base.$op(a::E, b::E) = binary(Base.$op, a, b)
    @eval Base.$op(a::E, b::Real) = Base.$op(a, E(b))
    @eval Base.$op(a::Real, b::E) = Base.$op(E(a), b)
end
Base.:-(a::E) = a.v isa S && numerator(a.v) != typemin(Int128) ? raw(-a.v) : raw(-wide(a))

@inline function comparison(op, a::E, b::E)
    if a.v isa S && b.v isa S
        an, ad = numerator(a.v), denominator(a.v)
        bn, bd = numerator(b.v), denominator(b.v)
        if ad != 0 && bd != 0
            if op == Base.:(==)
                return an == bn && ad == bd
            elseif ad == bd
                return op(an, bn)
            else
                x, ox = Base.mul_with_overflow(an, bd)
                y, oy = Base.mul_with_overflow(bn, ad)
                !ox && !oy && return op(x, y)
            end
        end
    end
    return op(wide(a), wide(b))
end

for op in (:<, :>, :<=, :>=, :(==))
    @eval Base.$op(a::E, b::E) = comparison(Base.$op, a, b)
    @eval Base.$op(a::E, b::Real) = Base.$op(a, E(b))
    @eval Base.$op(a::Real, b::E) = Base.$op(E(a), b)
end

# Same-denominator propagation shortcuts operate on raw numerators. Only Int128
# needs the checked variant: loop counters and the BigInt path keep Base ops.
for (name, op, checked) in ((:add, :+, :add_with_overflow),
                           (:sub, :-, :sub_with_overflow),
                           (:mul, :*, :mul_with_overflow))
    @eval begin
        @inline $name(a, b) = Base.$op(a, b)
        @inline function $name(a::Int128, b::Int128)
            value, overflow = Base.$checked(a, b)
            return overflow ? Base.$op(BigInt(a), BigInt(b)) : value
        end
    end
end

function form(n::Integer, d::Integer)
    if n isa Int128 && d isa Int128
        value = normalized(n, d)
        !isnothing(value) && return raw(value)
    end
    return E(Q(n, d))
end

function cached(cache::Vector{Union{Nothing,E}}, bounds, column::Int)
    value = cache[column]
    if isnothing(value) && isfinite(bounds[column])
        value = E(JS.bound_value(bounds[column]))
        cache[column] = value
    end
    return value
end

function other(total::E, unbounded::Int, term::Union{Nothing,E}, activity_zero=nothing)
    unbounded - isnothing(term) == 0 || return nothing
    (isnothing(term) || iszero(term)) && return total
    iszero(total) && return -term
    total == term && return isnothing(activity_zero) ? zero(E) : activity_zero
    denominator(total) == denominator(term) &&
        return form(sub(numerator(total), numerator(term)), denominator(total))
    return total - term
end

end # module _SmallExact
