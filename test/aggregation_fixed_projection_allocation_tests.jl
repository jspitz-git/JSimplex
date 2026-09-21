using SparseArrays

@testset "Fixed column projections preserve intervals, objectives, and restoration" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), coefficient in (2,-2), fixed in (-2,0,1,2), sparse_pass in (false,true)
        problem = LinearProblem(sparse(T[coefficient 1; (sparse_pass ? 1 : 0) (sparse_pass ? 2 : 1)]),T[2coefficient,3];
            row_lower=[T(5),nothing],row_upper=T[5,20],
            column_lower=[T(fixed),nothing],column_upper=[T(fixed),nothing])
        original = deepcopy(problem)
        pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
        result = pass(problem)
        endpoint = T(5-coefficient*fixed)
        last_coefficient = sparse_pass ? (coefficient > 0 ? 3//2 : 5//2) : 1
        last_upper = sparse_pass ? (coefficient > 0 ? 35//2 : 45//2) : 20
        @test result.problem.A == reshape(T[1,last_coefficient],:,1)
        @test result.problem.row_lower == [Bound(endpoint),Bound{T}(nothing)]
        @test result.problem.row_upper == [Bound(endpoint),Bound(T(last_upper))]
        @test result.problem.objective == T[1]
        @test result.problem.objective_constant == T(10)
        @test JSimplex.postsolve_primal(result,[endpoint]) == T[fixed,endpoint]
        @test problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
        @test problem.column_lower == original.column_lower && problem.column_upper == original.column_upper
        @test problem.A == original.A && problem.objective == original.objective
    end
end

@testset "Fixed bounds implied by an equality still remove the sparse row" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), coefficient in (2,-2)
        problem = LinearProblem(sparse(T[coefficient 1; 1 2]),T[2coefficient,3];
            row_lower=[T(2coefficient+1),nothing],row_upper=T[2coefficient+1,20],
            column_lower=T[2,1],column_upper=T[2,1])
        result = JSimplex.aggregate_sparse_equalities(problem)
        @test only(result.postsolve_stack).map.rows == [2]
        @test result.problem.A == reshape(T[coefficient > 0 ? 3//2 : 5//2],1,1)
        @test !isfinite(result.problem.row_lower[1])
        @test result.problem.row_upper == [Bound(T(coefficient > 0 ? 35//2 : 37//2))]
        @test result.problem.objective == T[1]
        @test result.problem.objective_constant == T(coefficient > 0 ? 10 : -6)
        @test JSimplex.postsolve_primal(result,T[1]) == T[2,1]
    end
end

@testset "Equal BigFloat bounds may have different stored precisions" begin
    low = setprecision(BigFloat,64) do
        BigFloat(3)/2
    end
    high = setprecision(BigFloat,256) do
        BigFloat(3)/2
    end
    for coefficient in (2,-2), sparse_pass in (false,true), ambient in (32,64)
        problem = LinearProblem(sparse(BigFloat[coefficient 2; (sparse_pass ? 1 : 0) (sparse_pass ? 0 : 1)]),zeros(BigFloat,2);
            row_lower=[BigFloat(5),nothing],row_upper=BigFloat[5,20])
        problem.column_lower[1],problem.column_upper[1] = Bound(low),Bound(high)
        setprecision(BigFloat,ambient) do
            pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
            result = pass(problem)
            @test size(result.problem.A) == (2,1)
            @test result.problem.row_lower[1] == Bound(BigFloat(coefficient > 0 ? 2 : 8))
            @test result.problem.row_upper[1] == result.problem.row_lower[1]
            @test precision(bound_value(problem.column_lower[1])) == 64
            @test precision(bound_value(problem.column_upper[1])) == 256
        end
    end
end

@testset "Near-equal bounds must reject an inexact second projection" begin
    for coefficient in (2,-2), sparse_pass in (false,true), ambient in (32,64), fixed in (false,true)
        stored = setprecision(BigFloat,256) do
            BigFloat(2) + (coefficient > 0 ? -1 : 1)*BigFloat(2)^(-200)
        end
        problem = LinearProblem(sparse(BigFloat[coefficient 2; (sparse_pass ? 1 : 0) (sparse_pass ? 0 : 1)]),zeros(BigFloat,2);
            row_lower=[BigFloat(5),nothing],row_upper=BigFloat[5,20],
            column_lower=[BigFloat(2),nothing],column_upper=[BigFloat(2),nothing])
        if fixed
            problem.column_lower[1],problem.column_upper[1] = Bound(stored),Bound(stored)
        elseif coefficient > 0
            problem.column_lower[1] = Bound(stored)
        else
            problem.column_upper[1] = Bound(stored)
        end
        original = deepcopy(problem)
        setprecision(BigFloat,ambient) do
            pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
            result = pass(problem)
            # With unequal endpoints the first projection is exact and the
            # second is not; treating close endpoints as equal would accept it.
            @test result.problem === problem
            @test isempty(result.postsolve_stack)
            @test problem.column_lower == original.column_lower
            @test problem.column_upper == original.column_upper
        end
    end
end

@testset "Aggregation projects fixed column bounds once" begin
function aggregation_fixed_projection_probe(kind; count=128)
    sparse_pass = kind in (:sparse_positive, :sparse_negative)
    coefficient = kind in (:singleton_negative, :sparse_negative) ? -2.0 : 2.0
    A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
    row_lower = Union{Nothing,Float64}[5.0 for _ in 1:count]
    row_upper = fill(5.0,count)
    if sparse_pass
        A = vcat(A,sparse(reshape(vcat(ones(count),2.0),1,count+1)))
        push!(row_lower,nothing); push!(row_upper,1000.0)
    end
    problem = LinearProblem(A,vcat(ones(count),2.0);
        row_lower,row_upper,
        column_lower=vcat(fill(kind == :free ? nothing : 2.0,count),nothing),
        column_upper=vcat(fill(kind == :free ? nothing : kind == :unequal ? 4.0 : 2.0,count),nothing))
    pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
    return problem,pass
end

    for (kind,limit) in ((:singleton_positive,27_000),(:singleton_negative,27_000),
                         (:sparse_positive,45_900),(:sparse_negative,45_900),
                         (:unequal,29_450),(:free,17_950))
        problem,pass = aggregation_fixed_projection_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = pass(problem)
        coefficient = kind in (:singleton_negative,:sparse_negative) ? -2.0 : 2.0
        @test result.problem.objective == [2-128/coefficient]
        @test result.problem.objective_constant == 128*5/coefficient
        @test JSimplex.postsolve_primal(result,[5-2coefficient]) == vcat(fill(2.0,128),5-2coefficient)
    end
end
