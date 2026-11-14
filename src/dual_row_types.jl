# Lazy, workspace-owned metadata. Never shares numeric arrays with a pivot stage.
# Validity is local to a pricing attempt; every entry/reprice clears both flags.
mutable struct _DualRowContext{T<:Real}
    support::Vector{Int}
    epochs::Vector{UInt64}
    slots::Vector{Int}
    generation::UInt64
    ready::Bool
    support_valid::Bool
    mode::Symbol
    ratio::T
end

_DualRowContext(::Type{T}, m::Int, n::Int) where {T} =
    _DualRowContext(Int[], zeros(UInt64, m+n), zeros(Int, m+n), UInt64(0),
                    false, false, :none, zero(T))
