using Test, JSimplex, SparseArrays

@testset "Native kernels validate dimensions before mutating scratch" begin
    for T in (Float32, Float64)
        p = LinearProblem(sparse(T[1 0; 0 1]), zeros(T, 2);
                          row_lower=zeros(T, 2), row_upper=ones(T, 2))
        ws = JSimplex.initialize_workspace(p, SolverOptions(T; verbose=false))
        @test_throws DimensionMismatch JSimplex._dual_row_residual_ratio(ws, zeros(T, 1), 1)
        ws.scratch.tau .= T(7)
        ws.scratch.row_rhs .= T(3)
        @test_throws DimensionMismatch JSimplex._dual_direction_residual_ok!(ws, ones(T, 1), one(T))
        @test ws.scratch.tau == T[7, 7]
        @test ws.scratch.row_rhs == T[3, 3]
        prices = fill(T(9), 3)
        @test_throws DimensionMismatch JSimplex._recompute_reduced_costs!(prices, ws, ones(T, 2))
        @test prices == T[9, 9, 9]
    end
end

# Deliberately non-one-based vectors, without an optional package dependency.
struct KernelOffsetVector{T} <: AbstractVector{T}
    values::Vector{T}
end
Base.size(v::KernelOffsetVector) = size(v.values)
Base.axes(v::KernelOffsetVector) = (0:(length(v.values)-1),)
function Base.getindex(v::KernelOffsetVector, i::Int)
    0 <= i < length(v.values) || throw(BoundsError(v, i))
    return v.values[i+1]
end
function Base.setindex!(v::KernelOffsetVector, x, i::Int)
    0 <= i < length(v.values) || throw(BoundsError(v, i))
    return v.values[i+1] = x
end

@testset "Reduced-cost kernel rejects offset vectors before writes" begin
    p = LinearProblem(sparse([1.0 0; 0 1]), zeros(2);
                      row_lower=zeros(2), row_upper=ones(2))
    ws = JSimplex.initialize_workspace(p, SolverOptions(verbose=false))
    storage = fill(9.0, 4)
    @test_throws ArgumentError JSimplex._recompute_reduced_costs!(KernelOffsetVector(storage), ws, ones(2))
    @test storage == fill(9.0, 4)
    prices = fill(9.0, 4)
    @test_throws ArgumentError JSimplex._recompute_reduced_costs!(prices, ws, KernelOffsetVector(ones(2)))
    @test prices == fill(9.0, 4)
end

@testset "Ordered reduced costs retain generic numeric support" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        p = LinearProblem(sparse(T[1 2; 3 4]), zeros(T, 2);
                          row_lower=zeros(T, 2), row_upper=ones(T, 2))
        ws = JSimplex.initialize_workspace(p, SolverOptions(T; verbose=false))
        prices = fill(T(99), 4)
        JSimplex._recompute_reduced_costs!(prices, ws, T[2, 3])
        @test prices == T[-11, -16, 0, 0]
    end
end
