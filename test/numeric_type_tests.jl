using JSimplex.LinearAlgebra
using JSimplex.SparseArrays

mutable struct RecursiveNumericRecord{T}
    next::Union{Nothing,RecursiveNumericRecord{T}}
    value::T
end

function abstract_numeric_storage(field, visited=Set{Type}())
    field === Any && return true
    field in visited && return false
    push!(visited, field)
    inspect = nested -> abstract_numeric_storage(nested, visited)
    field isa Union && return any(inspect, Base.uniontypes(field))
    if field <: Number
        return !isconcretetype(field)
    elseif field <: Base.AbstractLock
        # Backend locks hold runtime task/callback metadata, not numeric payloads.
        return false
    elseif field <: AbstractArray
        return !isconcretetype(field) || inspect(eltype(field))
    elseif field <: Union{Tuple,NamedTuple}
        return !isconcretetype(field) || any(inspect, fieldtypes(field))
    elseif field <: AbstractDict
        return !isconcretetype(field) || inspect(keytype(field)) || inspect(valtype(field))
    elseif field <: Factorization || isstructtype(field)
        # Concrete record types can still declare abstract numeric fields.
        return !isconcretetype(field) || any(inspect, fieldtypes(field))
    end
    return false
end

function test_hot_numeric_fields(instance)
    @testset "$(typeof(instance))" begin
        for (name, field) in zip(fieldnames(typeof(instance)), fieldtypes(typeof(instance)))
            @testset "$name" begin
                @test field !== Any
                @test all(isconcretetype, Base.uniontypes(field))
                @test !abstract_numeric_storage(field)
            end
        end
    end
end

# Julia 1.13 Test.@inferred erases type-valued keyword singletons to DataType.
# A positional type argument preserves the exact check on the public reader.
read_numeric_mps(path, ::Type{T}, format::Symbol) where {T} =
    read_mps(path; value_type=T, format)

function test_numeric_inference(::Type{T}) where {T}
    problem = @inferred typed_bounded_problem(T)
    options = @inferred SolverOptions(T)
    relaxed = @inferred JSimplex.relax_integrality(problem)
    presolved = @inferred JSimplex.identity_presolve(relaxed)
    scaling = @inferred JSimplex.identity_scaling(presolved.problem)
    workspace = @inferred JSimplex.initialize_workspace(problem, options)
    factor = workspace.factorization
    run = @inferred JSimplex._solve_continuous_dual(problem, options)
    solution = @inferred solve(problem)
    eta = @inferred JSimplex.PackedEta{T}(Int[1], T[one(T)], 1)
    finite_bound = first(problem.row_upper)

    @test relaxed isa LinearProblem{T}
    @test options isa SolverOptions{T}
    @test scaling isa JSimplex.Scaling{T}
    @test workspace isa JSimplex.SimplexWorkspace{T}
    @test factor isa JSimplex.PFIFactorization{T}
    @test @inferred(bound_value(finite_bound)) isa T
    @test @inferred(JSimplex.forward_solve(
        factor, zeros(T, size(problem.A, 1)))) isa Vector{T}
    @test @inferred(JSimplex.transpose_solve(
        factor, zeros(T, size(problem.A, 1)))) isa Vector{T}
    @test @inferred(JSimplex.recompute!(workspace)) === workspace
    @test @inferred(JSimplex.recompute!(workspace; refactorize=true)) === workspace
    @test @inferred(JSimplex.primal_infeasibility(workspace)) isa T
    @test @inferred(JSimplex.dual_infeasibility(workspace)) isa T
    @test @inferred(JSimplex.postsolve_primal(
        presolved,
        JSimplex.unscale_primal(scaling, zeros(T, size(problem.A, 2))),
    )) isa Vector{T}
    @test @inferred(JSimplex.unscale_dual(
        scaling, zeros(T, size(problem.A, 1)))) isa Vector{T}
    @test run isa JSimplex.DualRunResult{T}
    @test solution isa Solution{T}
    for result in (run, solution)
        @test result.status == OPTIMAL
        @test result.primal isa Vector{T}
        @test result.objective_value isa T
        if T <: Rational
            @test result.primal == T[2, 2]
            @test result.objective_value == T(-29 // 3)
        else
            @test result.primal ≈ T[2, 2]
            @test result.objective_value ≈ T(-29 // 3)
        end
    end

    for instance in (problem, options, workspace, factor, factor.base, scaling,
                     presolved, run, solution, eta, finite_bound,
                     first(problem.row_lower))
        test_hot_numeric_fields(instance)
    end
end

function test_numeric_eta_inference(::Type{T}) where {T}
    factor = @inferred JSimplex.PFIFactorization(sparse(T[2 1; 1 3]))
    replacement = @inferred JSimplex.forward_solve(factor, T[4, -1])
    @test @inferred(JSimplex.replace_column!(
        factor, replacement, 1; zero_tolerance=zero(T))) === factor
    forward = @inferred JSimplex.forward_solve(factor, T[5, 7])
    transposed = @inferred JSimplex.transpose_solve(factor, T[5, 7])
    @test forward isa Vector{T}
    @test transposed isa Vector{T}
    if T <: Rational
        @test forward == T[8 // 13, 33 // 13]
        @test transposed == T[22 // 13, 23 // 13]
    else
        @test forward ≈ T[8 // 13, 33 // 13]
        @test transposed ≈ T[22 // 13, 23 // 13]
    end
    test_hot_numeric_fields(only(factor.updates))
    @test @inferred(JSimplex.refactorize!(factor, sparse(T[4 1; -1 3]))) === factor
    @test isempty(factor.updates)

    empty_factor = @inferred JSimplex.PFIFactorization(spzeros(T, 0, 0))
    @test (@inferred JSimplex.forward_solve(empty_factor, T[])) == T[]
    @test (@inferred JSimplex.transpose_solve(empty_factor, T[])) == T[]
    test_hot_numeric_fields(empty_factor)
    test_hot_numeric_fields(empty_factor.base)
end

@testset "Numeric type stability" begin
    @testset "Storage gates reject erased numeric types" begin
        for field in (Any, Real, Number, AbstractFloat, Rational,
                      Vector{Real}, Vector{Number}, Vector{AbstractFloat},
                      AbstractVector{<:Real}, AbstractVector{Float64}, Matrix{Real},
                      Union{Nothing,Vector{Real}}, Vector{Tuple{String,Real,Int}},
                      Dict{String,Vector{Real}}, Bound{Real}, Factorization{Float64},
                      JSimplex.PFIFactorization{Float64}, JSimplex.DenseLUBackend{Float32})
            @test abstract_numeric_storage(field)
        end
        for field in (Float32, Rational{BigInt}, Vector{Float32}, Bound{Rational{BigInt}},
                      Union{Nothing,Vector{BigFloat}}, Vector{Tuple{String,Float32,Int}},
                      Dict{String,Vector{Rational{BigInt}}}, JSimplex.UMFPACKBackend)
            @test !abstract_numeric_storage(field)
        end
    end

    @testset "Storage gates inspect nested record payloads" begin
        for field in (
            Vector{JSimplex.BoundRecord{Real}},
            Vector{JSimplex.PackedEta{Real}},
            NamedTuple{(:value,),Tuple{Real}},
            Dict{String,Vector{JSimplex.BoundRecord{Real}}},
            NamedTuple{(:bounds,),Tuple{Dict{String,Vector{JSimplex.BoundRecord{Real}}}}},
            Union{Nothing,Vector{JSimplex.PackedEta{Real}}},
            RecursiveNumericRecord{Real},
        )
            @test abstract_numeric_storage(field)
        end
        for field in (
            Vector{JSimplex.BoundRecord{Float32}},
            Vector{JSimplex.PackedEta{Rational{BigInt}}},
            NamedTuple{(:value,),Tuple{Union{Nothing,Float64}}},
            Dict{String,Vector{JSimplex.BoundRecord{BigFloat}}},
            NamedTuple{(:bounds,),Tuple{Dict{String,Vector{JSimplex.BoundRecord{Float64}}}}},
            Union{Nothing,Vector{JSimplex.PackedEta{Float32}}},
            Vector{Union{Nothing,JSimplex.BoundRecord{Float32},JSimplex.BoundRecord{Float64}}},
            RecursiveNumericRecord{Float32},
            ReentrantLock,
        )
            @test !abstract_numeric_storage(field)
        end
    end

    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        @testset "$T" begin
            test_numeric_inference(T)
            test_numeric_eta_inference(T)
        end
    end

    @testset "Public MPS reader inference" begin
        root = joinpath(@__DIR__, "fixtures", "parser")
        exact_path = joinpath(root, "exact-rational.mps")
        fixed_path = joinpath(root, "basic-fixed.mps")
        free_path = joinpath(root, "basic-free.mps")
        @test @inferred(read_mps(exact_path)) isa LinearProblem{Float64}
        @test @inferred(read_mps(fixed_path; format=:fixed)) isa LinearProblem{Float64}
        @test @inferred(read_mps(free_path; format=:free)) isa LinearProblem{Float64}

        # These ordinary callers also require concrete inference with literal keywords.
        @test @inferred((path -> read_mps(path; value_type=Rational{BigInt}))(
            exact_path)) isa LinearProblem{Rational{BigInt}}
        @test @inferred((path -> read_mps(path; value_type=Rational{BigInt}, format=:fixed))(
            fixed_path)) isa LinearProblem{Rational{BigInt}}
        @test @inferred((path -> read_mps(path; value_type=Rational{BigInt}, format=:free))(
            free_path)) isa LinearProblem{Rational{BigInt}}

        for T in (Float32, Float64, BigFloat, Rational{BigInt})
            @testset "$T" begin
                @test @inferred(read_numeric_mps(exact_path, T, :auto)) isa LinearProblem{T}
                @test @inferred(read_numeric_mps(fixed_path, T, :fixed)) isa LinearProblem{T}
                @test @inferred(read_numeric_mps(free_path, T, :free)) isa LinearProblem{T}
                records = @inferred JSimplex._parse_mps_file(exact_path, T; format=:free)
                @test records isa JSimplex.MPSAccumulator{T}
                test_hot_numeric_fields(records)
                test_hot_numeric_fields(JSimplex.BoundRecord{T}(:LO, "X", zero(T), 1))
            end
        end
    end

    @test isempty(Test.detect_ambiguities(JSimplex; recursive=true))
end
