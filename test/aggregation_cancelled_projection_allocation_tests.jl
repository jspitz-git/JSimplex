using SparseArrays

@testset "Exact projection cancellation preserves values and representation" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        for (coefficient,value,rhs) in ((2,2,4),(-2,2,-4),(2,-2,-4),(-2,-2,4),
            (1,2,2),(-1,2,-2),(2,1,2),(2,-1,-2),(1//3,3,1),(3//7,4,12//7))
            exact_rhs,pivot = Rational{BigInt}(rhs),Rational{BigInt}(coefficient)
            bound = Bound(T(value))
            saved = deepcopy((exact_rhs,pivot,bound))
            @test JSimplex._project_equality_bound(T,exact_rhs,pivot,bound) == Bound(zero(T))
            @test (exact_rhs,pivot,bound) == saved
        end
        for coefficient in (2,-2)
            pivot = big(coefficient)//1
            @test JSimplex._project_equality_bound(T,big(4)//1,pivot,Bound{T}(nothing)) == Bound{T}(nothing)
            @test JSimplex._project_equality_bound(T,big(4)//1,pivot,Bound(zero(T))) == Bound(T(4))
            @test JSimplex._project_equality_bound(T,big(0)//1,pivot,Bound(T(2))) == Bound(T(coefficient == 2 ? -4 : 4))
        end
        projected = JSimplex._project_equality_bound(T,big(7)//3,big(1)//1,Bound(T(2)))
        @test T == Rational{BigInt} ? projected == Bound(big(1)//3) : isnothing(projected)
    end
end

@testset "Cancelled endpoints preserve aggregation rows and restoration" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), coefficient in (2,-2), sparse_pass in (false,true), kind in (:both,:lower,:fixed,:free)
        has_lower,has_upper = kind != :free,kind in (:both,:fixed)
        high = kind == :fixed ? 2 : 4
        problem = LinearProblem(sparse(T[coefficient 1; (sparse_pass ? 1 : 0) (sparse_pass ? 2 : 1)]),T[2coefficient,3];
            row_lower=[T(2coefficient),nothing],row_upper=T[2coefficient,20],
            column_lower=[has_lower ? T(2) : nothing,nothing],
            column_upper=[has_upper ? T(high) : nothing,nothing])
        original = deepcopy(problem)
        pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
        result = pass(problem)
        dropped = sparse_pass && kind == :free
        expected_lower = coefficient > 0 ? (has_upper ? T(kind == :fixed ? 0 : -4) : nothing) : (has_lower ? zero(T) : nothing)
        expected_upper = coefficient > 0 ? (has_lower ? zero(T) : nothing) : (has_upper ? T(kind == :fixed ? 0 : 4) : nothing)
        last_coefficient = sparse_pass ? (coefficient > 0 ? 3//2 : 5//2) : 1
        last_upper = sparse_pass ? 18 : 20
        @test result.problem.A == reshape(dropped ? T[last_coefficient] : T[1,last_coefficient],:,1)
        @test result.problem.row_lower == (dropped ? [Bound{T}(nothing)] : [Bound{T}(expected_lower),Bound{T}(nothing)])
        @test result.problem.row_upper == (dropped ? [Bound(T(last_upper))] : [Bound{T}(expected_upper),Bound(T(last_upper))])
        @test result.problem.objective == T[1]
        @test result.problem.objective_constant == T(4coefficient)
        @test JSimplex.postsolve_primal(result,T[0]) == T[2,0]
        @test problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
        @test problem.column_lower == original.column_lower && problem.column_upper == original.column_upper
        @test problem.A == original.A && problem.objective == original.objective
    end
end

@testset "Tiny exact projection residuals remain nonzero at lower precision" begin
    for coefficient in (2,-2), direction in (-1,1), sparse_pass in (false,true), ambient in (32,64)
        stored = setprecision(BigFloat,256) do
            BigFloat(2coefficient) + direction * BigFloat(2)^(-200)
        end
        problem = LinearProblem(sparse(BigFloat[coefficient 1; (sparse_pass ? 1 : 0) (sparse_pass ? 0 : 1)]),zeros(BigFloat,2);
            column_lower=[BigFloat(2),nothing],column_upper=[nothing,nothing])
        problem.row_lower[1],problem.row_upper[1] = Bound(stored),Bound(stored)
        original = deepcopy(problem)
        setprecision(BigFloat,ambient) do
            residual = direction * BigFloat(2)^(-200)
            exact_rhs = big(2coefficient)//1 + direction * (big(1)//big(2)^200)
            @test JSimplex._project_equality_bound(BigFloat,exact_rhs,big(coefficient)//1,problem.column_lower[1]) == Bound(residual)
            pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
            result = pass(problem)
            @test size(result.problem.A) == (2,1)
            endpoint = coefficient > 0 ? result.problem.row_upper[1] : result.problem.row_lower[1]
            @test endpoint == Bound(residual)
            @test !iszero(bound_value(endpoint))
            @test JSimplex.postsolve_primal(result,[residual]) == BigFloat[2,residual]
            @test problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
            @test precision(bound_value(problem.row_lower[1])) == 256
        end
    end
end

@testset "Aggregation avoids general subtraction for cancelled projections" begin
function aggregation_cancelled_projection_probe(kind; count=128)
    sparse_pass = kind in (:sparse_positive, :sparse_negative)
    coefficient = kind in (:singleton_negative, :sparse_negative) ? -2.0 : 2.0
    A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
    row_lower = Union{Nothing,Float64}[kind == :unequal ? 5.0 : 2coefficient for _ in 1:count]
    row_upper = fill(kind == :unequal ? 5.0 : 2coefficient,count)
    if sparse_pass
        A = vcat(A,sparse(reshape(vcat(ones(count),2.0),1,count+1)))
        push!(row_lower,nothing); push!(row_upper,1000.0)
    end
    problem = LinearProblem(A,vcat(ones(count),2.0);
        row_lower,row_upper,
        column_lower=vcat(fill(kind == :free ? nothing : 2.0,count),nothing),
        column_upper=vcat(fill(kind == :free ? nothing : 4.0,count),nothing))
    pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
    return problem,pass
end

    for (kind,limit) in ((:singleton_positive,28_300),(:singleton_negative,28_300),
                         (:sparse_positive,47_100),(:sparse_negative,47_100),
                         (:unequal,29_450),(:free,18_000))
        problem,pass = aggregation_cancelled_projection_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = pass(problem)
        coefficient = kind in (:singleton_negative,:sparse_negative) ? -2.0 : 2.0
        rhs = kind == :unequal ? 5.0 : 2coefficient
        @test result.problem.objective == [2-128/coefficient]
        @test result.problem.objective_constant == 128*rhs/coefficient
        @test JSimplex.postsolve_primal(result,[rhs-3coefficient]) == vcat(fill(3.0,128),rhs-3coefficient)
    end
end
