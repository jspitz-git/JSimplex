using SparseArrays

@testset "Zero-priced elimination preserves objective values and projections" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), coefficient in (2,-2), sparse_pass in (false,true), other_cost in (0,3), constant in (0,7)
        problem = LinearProblem(sparse(T[coefficient 1; (sparse_pass ? 1 : 0) (sparse_pass ? 2 : 1)]),T[-zero(T),other_cost];
            objective_constant=T(constant),row_lower=[T(5),nothing],row_upper=T[5,20],
            column_lower=[T(1),nothing],column_upper=[T(3),nothing])
        original = deepcopy(problem)
        pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
        result = pass(problem)
        last_coefficient = sparse_pass ? (coefficient > 0 ? 3//2 : 5//2) : 1
        last_upper = sparse_pass ? (coefficient > 0 ? 35//2 : 45//2) : 20
        @test result.problem.A == reshape(T[1,last_coefficient],:,1)
        @test result.problem.row_lower == [Bound(T(coefficient > 0 ? -1 : 7)),Bound{T}(nothing)]
        @test result.problem.row_upper == Bound.(T[coefficient > 0 ? 3 : 11,last_upper])
        @test result.problem.objective == T[other_cost]
        @test result.problem.objective_constant == T(constant)
        @test JSimplex.postsolve_primal(result,T[5-2coefficient]) == T[2,5-2coefficient]
        @test problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
        @test problem.column_lower == original.column_lower && problem.column_upper == original.column_upper
        @test problem.objective == original.objective && problem.objective_constant == original.objective_constant
    end
end

@testset "Zero ratios preserve already committed objective updates" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), sparse_pass in (false,true), (first_cost,second_cost,constant,remaining_cost) in ((2,0,9,2),(0,-2,11,2),(0,0,5,3))
        A = sparse(T[2 0 1; 0 -2 1])
        row_lower = [T(4),T(6)]
        row_upper = T[4,6]
        if sparse_pass
            A = vcat(A,sparse(reshape(T[1,1,3],1,3)))
            row_lower = [T(4),T(6),nothing]
            push!(row_upper,T(20))
        end
        problem = LinearProblem(A,T[first_cost,second_cost,3];objective_constant=T(5),
            row_lower,row_upper,column_lower=fill(nothing,3),column_upper=fill(nothing,3))
        original = deepcopy(problem)
        pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
        result = pass(problem)
        @test result.problem.objective == T[remaining_cost]
        @test result.problem.objective_constant == T(constant)
        @test result.problem.A == (sparse_pass ? reshape(T[3],1,1) : ones(T,2,1))
        @test result.problem.row_upper == (sparse_pass ? [Bound(T(21))] : fill(Bound{T}(nothing),2))
        @test JSimplex.postsolve_primal(result,T[2]) == T[1,-2,2]
        @test problem.objective == original.objective && problem.objective_constant == original.objective_constant
    end
end

@testset "Zero objective shortcuts retain exact representation checks" begin
    for kind in (:tiny_price,:constant,:other_cost), coefficient in (2,-2), direction in (-1,1), sparse_pass in (false,true), ambient in (32,64)
        stored = setprecision(BigFloat,256) do
            base = kind == :tiny_price ? 0 : kind == :constant ? 7 : 3
            BigFloat(base) + direction * BigFloat(2)^(-200)
        end
        problem = LinearProblem(sparse(BigFloat[coefficient 2; (sparse_pass ? 1 : 0) (sparse_pass ? 0 : 1)]),BigFloat[0,3];
            objective_constant=kind == :constant ? stored : BigFloat(7),
            row_lower=[BigFloat(5),nothing],row_upper=BigFloat[5,20],
            column_lower=[BigFloat(1),nothing],column_upper=[BigFloat(3),nothing])
        kind == :tiny_price && (problem.objective[1] = stored)
        kind == :other_cost && (problem.objective[2] = stored)
        original = deepcopy(problem)
        setprecision(BigFloat,ambient) do
            pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
            result = pass(problem)
            @test result.problem === problem
            @test isempty(result.postsolve_stack)
            @test problem.objective == original.objective
            @test problem.objective_constant == original.objective_constant
            value = kind == :constant ? problem.objective_constant : problem.objective[kind == :tiny_price ? 1 : 2]
            @test precision(value) == 256
        end
    end
end

@testset "Aggregation avoids zero-ratio objective arithmetic" begin
function aggregation_zero_objective_updates_probe(kind; count=128)
    sparse_pass = kind in (:sparse_positive, :sparse_negative)
    coefficient = kind in (:singleton_negative, :sparse_negative) ? -2.0 : 2.0
    A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
    row_lower = Union{Nothing,Float64}[kind == :inequality ? 0.0 : 5.0 for _ in 1:count]
    row_upper = fill(kind == :inequality ? 1.0 : 5.0,count)
    if sparse_pass
        A = vcat(A,sparse(reshape(vcat(ones(count),2.0),1,count+1)))
        push!(row_lower,nothing); push!(row_upper,1000.0)
    end
    problem = LinearProblem(A,vcat(fill(kind == :nonzero ? 1.0 : 0.0,count),2.0);
        objective_constant=7.0,
        row_lower,row_upper,
        column_lower=vcat(fill(1.0,count),nothing),
        column_upper=vcat(fill(3.0,count),nothing))
    pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
    return problem,pass
end

    for (kind,limit) in ((:singleton_positive,24_000),(:singleton_negative,24_000),
                         (:sparse_positive,43_000),(:sparse_negative,43_000),
                         (:nonzero,28_300),(:inequality,400))
        problem,pass = aggregation_zero_objective_updates_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = pass(problem)
        if kind == :inequality
            @test result.problem === problem
            @test result.problem.objective == vcat(zeros(128),2.0)
            @test result.problem.objective_constant == 7.0
        else
            coefficient = kind in (:singleton_negative,:sparse_negative) ? -2.0 : 2.0
            @test result.problem.objective == [kind == :nonzero ? -62.0 : 2.0]
            @test result.problem.objective_constant == (kind == :nonzero ? 327.0 : 7.0)
            @test JSimplex.postsolve_primal(result,[5-2coefficient]) == vcat(fill(2.0,128),5-2coefficient)
        end
    end
end
