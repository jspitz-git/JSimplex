@enum VariableState::UInt8 BASIC AT_LOWER AT_UPPER FREE_NONBASIC

struct Basis
    basic_indices::Vector{Int}
    states::Vector{VariableState}
end

function Basis(
    basic_indices::AbstractVector{<:Integer},
    states::AbstractVector{VariableState},
)
    return Basis(Int.(basic_indices), collect(states))
end
