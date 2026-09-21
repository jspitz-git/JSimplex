using SparseArrays

@testset "Zero objective numerators preserve aggregation across pivot types" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), coefficient in (2,-2,1,-1,1//2,-1//2), sparse_pass in (false,true)
        problem = LinearProblem(sparse(T[coefficient 1; (sparse_pass ? 1 : 0) (sparse_pass ? 2 : 1)]),T[-zero(T),3];
            objective_constant=T(7),row_lower=[T(5),nothing],row_upper=T[5,20],
            column_lower=[T(1),nothing],column_upper=[T(3),nothing])
        original = deepcopy(problem)
        pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
        result = pass(problem)
        @test size(result.problem.A) == (2,1)
        @test result.problem.objective == T[3]
        @test result.problem.objective_constant == T(7)
        @test JSimplex.postsolve_primal(result,T[5-2coefficient]) == T[2,5-2coefficient]
        @test problem.objective == original.objective
        @test problem.objective_constant == original.objective_constant
        @test problem.row_lower == original.row_lower && problem.column_lower == original.column_lower
    end
end

@testset "A nonzero subnormal objective must not disappear during division" begin
    for T in (Float32,Float64), coefficient in (2,-2), direction in (-1,1), sparse_pass in (false,true)
        tiny = direction*nextfloat(zero(T))
        problem = LinearProblem(sparse(T[coefficient 1; (sparse_pass ? 1 : 0) (sparse_pass ? 0 : 1)]),T[tiny,0];
            row_lower=[T(1),nothing],row_upper=T[1,20],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original = deepcopy(problem)
        pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
        result = pass(problem)
        # The new constant would be half of the smallest nonzero value in T;
        # exact division must retain it and reject its inexact representation.
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test problem.objective == original.objective
        @test problem.objective_constant == original.objective_constant
    end
end

@testset "Tiny nonzero BigFloat ratios still update the objective" begin
    for coefficient in (2,-2), direction in (-1,1), sparse_pass in (false,true), ambient in (32,64)
        tiny = setprecision(BigFloat,256) do
            direction*BigFloat(2)^(-200)
        end
        problem = LinearProblem(sparse(BigFloat[coefficient 2; (sparse_pass ? 1 : 0) (sparse_pass ? 0 : 1)]),BigFloat[0,0];
            row_lower=[BigFloat(2),nothing],row_upper=BigFloat[2,20],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        problem.objective[1] = tiny
        original = deepcopy(problem)
        setprecision(BigFloat,ambient) do
            pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
            result = pass(problem)
            expected_constant = (coefficient > 0 ? direction : -direction)*BigFloat(2)^(-200)
            @test size(result.problem.A) == (sparse_pass ? (1,1) : (2,1))
            @test result.problem.objective_constant == expected_constant
            @test result.problem.objective == [-expected_constant]
            @test !iszero(result.problem.objective_constant)
            @test JSimplex.postsolve_primal(result,BigFloat[0]) == BigFloat[coefficient > 0 ? 1 : -1,0]
            @test problem.objective == original.objective
            @test precision(problem.objective[1]) == 256
        end
    end
end

@testset "Aggregation avoids exact division of zero objective prices" begin
function aggregation_zero_objective_ratio_probe(kind; count=128)
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

    for (kind,limit) in ((:singleton_positive,20_900),(:singleton_negative,20_900),
                         (:sparse_positive,39_650),(:sparse_negative,39_650),
                         (:nonzero,28_300),(:inequality,400))
        problem,pass = aggregation_zero_objective_ratio_probe(kind)
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
