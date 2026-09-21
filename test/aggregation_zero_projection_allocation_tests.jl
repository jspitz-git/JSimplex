using SparseArrays

@testset "Zero projection retains exact representation and unbounded semantics" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        for coefficient in (1,-1,2,-2), stored in (zero(T),-zero(T))
            rhs,pivot = big(7)//1,big(coefficient)//1
            bound = Bound(stored)
            saved = deepcopy((rhs,pivot,bound))
            @test JSimplex._project_equality_bound(T,rhs,pivot,bound) == Bound(T(7))
            @test (rhs,pivot,bound) == saved
        end
        for coefficient in (2,-2)
            rhs,pivot = big(1)//3,big(coefficient)//1
            projected = JSimplex._project_equality_bound(T,rhs,pivot,Bound(zero(T)))
            @test T == Rational{BigInt} ? projected == Bound(big(1)//3) : isnothing(projected)
            @test JSimplex._project_equality_bound(T,rhs,pivot,Bound{T}(nothing)) == Bound{T}(nothing)
        end
        for (coefficient,value,expected) in ((2,1,5),(-2,1,9),(2,-1,9),(-2,-1,5))
            @test JSimplex._project_equality_bound(T,big(7)//1,big(coefficient)//1,Bound(T(value))) == Bound(T(expected))
        end
    end
end

@testset "Zero endpoint projections preserve rows, costs, and restoration" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), coefficient in (2,-2), sparse_pass in (false,true), kind in (:lower,:upper,:fixed)
        low = kind == :upper ? -3 : 0
        high = kind == :lower ? 3 : 0
        problem = LinearProblem(sparse(T[coefficient 1; (sparse_pass ? 1 : 0) (sparse_pass ? 2 : 1)]),T[2coefficient,3];
            row_lower=[T(5),nothing],row_upper=T[5,20],
            column_lower=[T(low),nothing],column_upper=[T(high),nothing])
        original = deepcopy(problem)
        pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
        result = pass(problem)
        expected_lower,expected_upper = kind == :fixed ? (5,5) :
            (kind == :lower) == (coefficient > 0) ? (-1,5) : (5,11)
        last_coefficient = sparse_pass ? (coefficient > 0 ? 3//2 : 5//2) : 1
        last_upper = sparse_pass ? (coefficient > 0 ? 35//2 : 45//2) : 20
        @test result.problem.A == reshape(T[1,last_coefficient],:,1)
        @test result.problem.row_lower == [Bound(T(expected_lower)),Bound{T}(nothing)]
        @test result.problem.row_upper == Bound.(T[expected_upper,last_upper])
        @test result.problem.objective == T[1]
        @test result.problem.objective_constant == T(10)
        @test JSimplex.postsolve_primal(result,T[5]) == T[0,5]
        @test problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
        @test problem.column_lower == original.column_lower && problem.column_upper == original.column_upper
        @test problem.A == original.A && problem.objective == original.objective
    end
end

@testset "Tiny nonzero BigFloat bounds do not take the zero projection shortcut" begin
    for coefficient in (2,-2), direction in (-1,1), sparse_pass in (false,true), ambient in (32,64)
        stored = setprecision(BigFloat,256) do
            direction * BigFloat(2)^(-200)
        end
        problem = LinearProblem(sparse(BigFloat[coefficient 2; (sparse_pass ? 1 : 0) (sparse_pass ? 0 : 1)]),zeros(BigFloat,2);
            row_lower=[BigFloat(5),nothing],row_upper=BigFloat[5,20],
            column_lower=[BigFloat(0),nothing],column_upper=[BigFloat(3),nothing])
        problem.column_lower[1] = Bound(stored)
        original = deepcopy(problem)
        setprecision(BigFloat,ambient) do
            @test isnothing(JSimplex._project_equality_bound(BigFloat,big(5)//1,big(coefficient)//1,problem.column_lower[1]))
            pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
            result = pass(problem)
            @test result.problem === problem
            @test isempty(result.postsolve_stack)
            @test problem.column_lower == original.column_lower
            @test precision(bound_value(problem.column_lower[1])) == 256
        end
    end
end

@testset "Aggregation avoids exact arithmetic for zero projected bounds" begin
function aggregation_zero_projection_probe(kind; count=128)
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
        column_lower=vcat(fill(kind == :free ? nothing : kind == :nonzero ? 1.0 : 0.0,count),nothing),
        column_upper=vcat(fill(kind == :free ? nothing : 3.0,count),nothing))
    pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
    return problem,pass
end

    for (kind,limit) in ((:singleton_positive,27_000),(:singleton_negative,27_000),
                         (:sparse_positive,46_000),(:sparse_negative,46_000),
                         (:nonzero,29_450),(:free,17_950))
        problem,pass = aggregation_zero_projection_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = pass(problem)
        coefficient = kind in (:singleton_negative,:sparse_negative) ? -2.0 : 2.0
        @test result.problem.objective == [2-128/coefficient]
        @test result.problem.objective_constant == 128*5/coefficient
        @test JSimplex.postsolve_primal(result,[5-coefficient]) == vcat(fill(1.0,128),5-coefficient)
    end
end
