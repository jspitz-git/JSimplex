mutable struct Optimizer{T<:Real} <: MOI.AbstractOptimizer
    primal_tolerance::T
    dual_tolerance::T
    zero_tolerance::T
    iteration_limit::Int
    time_limit::Float64
    refactorization_interval::Int
    verbose::Bool
    algorithm::Symbol
    pricing::Symbol
    silent::Bool
    relax_integrality::Bool
    solution::Union{Nothing,Solution{T}}
    constraint_primals::Vector{T}
end

function Optimizer{T}() where {T<:Real}
    _supported_value_type(T) ||
        throw(ArgumentError("unsupported optimizer value type $T"))
    options = SolverOptions(T)
    return Optimizer{T}(
        options.primal_tolerance,
        options.dual_tolerance,
        options.zero_tolerance,
        options.iteration_limit,
        options.time_limit,
        options.refactorization_interval,
        options.verbose,
        options.algorithm,
        options.pricing,
        false,
        false,
        nothing,
        T[],
    )
end

Optimizer() = Optimizer{Float64}()

function _clear_result!(optimizer::Optimizer{T}) where {T}
    optimizer.solution = nothing
    empty!(optimizer.constraint_primals)
    return
end

MOI.supports_incremental_interface(::Optimizer) = false
MOI.is_empty(optimizer::Optimizer) = isnothing(optimizer.solution) &&
                                     isempty(optimizer.constraint_primals)
MOI.empty!(optimizer::Optimizer) = _clear_result!(optimizer)

function Base.summary(io::IO, ::Optimizer{T}) where {T}
    return print(io, "JSimplex optimizer ($T)")
end

const _MOINumericSet{T} = Union{
    MOI.GreaterThan{T},
    MOI.LessThan{T},
    MOI.EqualTo{T},
    MOI.Interval{T},
}

function MOI.supports_constraint(
    ::Optimizer{T},
    ::Type{MOI.VariableIndex},
    ::Type{<:_MOINumericSet{T}},
) where {T}
    return true
end

function MOI.supports_constraint(
    ::Optimizer,
    ::Type{MOI.VariableIndex},
    ::Type{<:Union{MOI.Integer,MOI.ZeroOne}},
)
    return true
end

function MOI.supports_constraint(
    ::Optimizer{T},
    ::Type{MOI.ScalarAffineFunction{T}},
    ::Type{<:_MOINumericSet{T}},
) where {T}
    return true
end

MOI.supports(
    ::Optimizer{T},
    ::MOI.ObjectiveFunction{MOI.ScalarAffineFunction{T}},
) where {T} = true
MOI.supports(
    ::Optimizer,
    ::MOI.ObjectiveFunction{MOI.VariableIndex},
) = true
