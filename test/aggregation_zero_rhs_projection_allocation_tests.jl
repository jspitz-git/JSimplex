using SparseArrays

@testset "Zero RHS projection preserves signed products and missing bounds" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        for (coefficient,value,expected) in ((1,2,-2),(-1,2,2),(2,3,-6),(-2,3,6),
            (1,-2,2),(-1,-2,-2),(2,-3,6),(-2,-3,-6),(2//3,3,-2),(-2//3,3,2))
            rhs,pivot = big(0)//1,Rational{BigInt}(coefficient)
            bound = Bound(T(value))
            saved = deepcopy((rhs,pivot,bound))
            @test JSimplex._project_equality_bound(T,rhs,pivot,bound) == Bound(T(expected))
            @test (rhs,pivot,bound) == saved
        end
        for coefficient in (2,-2)
            pivot = big(coefficient)//1
            @test JSimplex._project_equality_bound(T,big(0)//1,pivot,Bound{T}(nothing)) == Bound{T}(nothing)
            @test JSimplex._project_equality_bound(T,big(0)//1,pivot,Bound(-zero(T))) == Bound(zero(T))
            @test JSimplex._project_equality_bound(T,big(5)//1,pivot,Bound(T(2))) == Bound(T(coefficient == 2 ? 1 : 9))
        end
        # Even with a zero RHS, a nonrepresentable exact product must be rejected.
        projected = JSimplex._project_equality_bound(T,big(0)//1,big(1)//3,Bound(T(1)))
        @test T == Rational{BigInt} ? projected == Bound(-big(1)//3) : isnothing(projected)
    end
end

@testset "Zero RHS projections preserve aggregated intervals and restoration" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), coefficient in (2,-2), sparse_pass in (false,true), kind in (:both,:lower,:upper,:free,:fixed)
        has_lower,has_upper = kind in (:both,:lower,:fixed),kind in (:both,:upper,:fixed)
        low,high = kind == :fixed ? (2,2) : (1,3)
        problem = LinearProblem(sparse(T[coefficient 1; (sparse_pass ? 1 : 0) (sparse_pass ? 2 : 1)]),T[2coefficient,3];
            row_lower=[-zero(T),nothing],row_upper=T[0,20],
            column_lower=[has_lower ? T(low) : nothing,nothing],
            column_upper=[has_upper ? T(high) : nothing,nothing])
        original = deepcopy(problem)
        pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
        result = pass(problem)
        dropped = sparse_pass && kind == :free
        expected_lower = coefficient == 2 ? (has_upper ? T(kind == :fixed ? -4 : -6) : nothing) : (has_lower ? T(kind == :fixed ? 4 : 2) : nothing)
        expected_upper = coefficient == 2 ? (has_lower ? T(kind == :fixed ? -4 : -2) : nothing) : (has_upper ? T(kind == :fixed ? 4 : 6) : nothing)
        last_coefficient = sparse_pass ? (coefficient == 2 ? 3//2 : 5//2) : 1
        @test result.problem.A == reshape(dropped ? T[last_coefficient] : T[1,last_coefficient],:,1)
        @test result.problem.row_lower == (dropped ? [Bound{T}(nothing)] : [Bound{T}(expected_lower),Bound{T}(nothing)])
        @test result.problem.row_upper == (dropped ? [Bound(T(20))] : [Bound{T}(expected_upper),Bound(T(20))])
        @test result.problem.objective == T[1]
        @test result.problem.objective_constant == zero(T)
        @test JSimplex.postsolve_primal(result,T[coefficient == 2 ? -4 : 4]) == T[2,coefficient == 2 ? -4 : 4]
        @test problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
        @test problem.column_lower == original.column_lower && problem.column_upper == original.column_upper
        @test problem.A == original.A && problem.objective == original.objective
    end
end

@testset "Tiny nonzero RHS values retain their exact effect on projection" begin
    for coefficient in (2,-2), direction in (-1,1), sparse_pass in (false,true), ambient in (32,64)
        stored = setprecision(BigFloat,256) do
            direction * BigFloat(2)^(-200)
        end
        problem = LinearProblem(sparse(BigFloat[coefficient 2; (sparse_pass ? 1 : 0) (sparse_pass ? 0 : 1)]),zeros(BigFloat,2);
            row_lower=[BigFloat(0),nothing],row_upper=BigFloat[0,20],
            column_lower=[BigFloat(1),nothing],column_upper=[BigFloat(3),nothing])
        problem.row_lower[1],problem.row_upper[1] = Bound(stored),Bound(stored)
        original = deepcopy(problem)
        setprecision(BigFloat,ambient) do
            rhs = direction * (big(1)//big(2)^200)
            @test isnothing(JSimplex._project_equality_bound(BigFloat,rhs,big(coefficient)//1,problem.column_lower[1]))
            pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
            result = pass(problem)
            @test result.problem === problem
            @test isempty(result.postsolve_stack)
            @test problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
            @test precision(bound_value(problem.row_lower[1])) == 256
        end
    end
end

@testset "Aggregation negates products for zero right-hand sides" begin
function aggregation_zero_rhs_projection_probe(kind; count=128)
    sparse_pass = kind in (:sparse_positive, :sparse_negative)
    coefficient = kind in (:singleton_negative, :sparse_negative) ? -2.0 : 2.0
    A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
    row_lower = Union{Nothing,Float64}[kind == :nonzero ? 5.0 : 0.0 for _ in 1:count]
    row_upper = fill(kind == :nonzero ? 5.0 : 0.0,count)
    if sparse_pass
        A = vcat(A,sparse(reshape(vcat(ones(count),2.0),1,count+1)))
        push!(row_lower,nothing); push!(row_upper,1000.0)
    end
    problem = LinearProblem(A,vcat(ones(count),2.0);
        row_lower,row_upper,
        column_lower=vcat(fill(kind == :free ? nothing : 1.0,count),nothing),
        column_upper=vcat(fill(kind == :free ? nothing : 3.0,count),nothing))
    pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
    return problem,pass
end

    for (kind,limit) in ((:singleton_positive,27_000),(:singleton_negative,27_000),
                         (:sparse_positive,41_000),(:sparse_negative,41_000),
                         (:nonzero,29_450),(:free,16_850))
        problem,pass = aggregation_zero_rhs_projection_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = pass(problem)
        coefficient = kind in (:singleton_negative,:sparse_negative) ? -2.0 : 2.0
        rhs = kind == :nonzero ? 5.0 : 0.0
        @test result.problem.objective == [2-128/coefficient]
        @test result.problem.objective_constant == 128*rhs/coefficient
        @test JSimplex.postsolve_primal(result,[rhs-2coefficient]) == vcat(fill(2.0,128),rhs-2coefficient)
    end
end
