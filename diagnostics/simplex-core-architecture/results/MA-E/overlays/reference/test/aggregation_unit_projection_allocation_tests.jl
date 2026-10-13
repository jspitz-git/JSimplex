using SparseArrays

@testset "Unit projection preserves finite, absent, and inexact bounds" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        for (coefficient, value, expected) in ((1, 2, 5), (-1, 2, 9),
            (1, -2, 9), (-1, -2, 5), (1, 0, 7), (-1, 0, 7),
            (2, 2, 3), (-2, 2, 11))
            rhs, pivot = big(7)//1, big(coefficient)//1
            bound = Bound(T(value))
            saved = deepcopy((rhs, pivot, bound))
            @test JSimplex._project_equality_bound(T, rhs, pivot, bound) == Bound(T(expected))
            @test (rhs, pivot, bound) == saved
        end
        for coefficient in (1, -1, 2, -2)
            @test JSimplex._project_equality_bound(T, big(7)//1, big(coefficient)//1, Bound{T}(nothing)) == Bound{T}(nothing)
        end
        # An exact near-unit coefficient must not be rounded to a unit before multiplication.
        for sign in (-1, 1)
            pivot = sign * (big(1)//1 + big(1)//big(2)^200)
            projected = JSimplex._project_equality_bound(T, big(5)//1, pivot, Bound(T(2)))
            if T == Rational{BigInt}
                @test projected == Bound(big(5)//1 - sign * (big(2)//1 + big(1)//big(2)^199))
            elseif T != BigFloat
                @test isnothing(projected)
            else
                setprecision(BigFloat, 64) do
                    @test isnothing(JSimplex._project_equality_bound(T, big(5)//1, pivot, Bound(T(2))))
                end
            end
        end
    end
end

@testset "Unit projections preserve aggregation rows, costs, and primal restoration" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (1, -1), sparse_pass in (false, true), kind in (:both, :lower, :upper, :free)
        has_lower, has_upper = kind in (:both, :lower), kind in (:both, :upper)
        A = sparse(T[coefficient 1; sparse_pass ? 1 : 0 sparse_pass ? 2 : 1])
        problem = LinearProblem(A,T[2coefficient,3];
            row_lower=[T(5),nothing],row_upper=T[5,20],
            column_lower=[has_lower ? T(1) : nothing,nothing],
            column_upper=[has_upper ? T(3) : nothing,nothing])
        original = deepcopy(problem)
        pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
        result = pass(problem)
        dropped = sparse_pass && kind == :free
        expected_lower = coefficient == 1 ? (has_upper ? T(2) : nothing) : (has_lower ? T(6) : nothing)
        expected_upper = coefficient == 1 ? (has_lower ? T(4) : nothing) : (has_upper ? T(8) : nothing)
        last_coefficient = sparse_pass ? (coefficient == 1 ? 1 : 3) : 1
        last_upper = sparse_pass ? (coefficient == 1 ? 15 : 25) : 20
        @test result.problem.A == reshape(dropped ? T[last_coefficient] : T[1,last_coefficient],:,1)
        @test result.problem.row_lower == (dropped ? [Bound{T}(nothing)] : [Bound{T}(expected_lower),Bound{T}(nothing)])
        @test result.problem.row_upper == (dropped ? [Bound(T(last_upper))] : [Bound{T}(expected_upper),Bound(T(last_upper))])
        @test result.problem.objective == T[1]
        @test result.problem.objective_constant == T(10)
        @test JSimplex.postsolve_primal(result,T[coefficient == 1 ? 3 : 7]) == T[2,coefficient == 1 ? 3 : 7]
        @test problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
        @test problem.column_lower == original.column_lower && problem.column_upper == original.column_upper
        @test problem.A == original.A && problem.objective == original.objective
    end
end

@testset "Unit products retain stored BigFloat precision before projection" begin
    stored = setprecision(BigFloat,256) do
        BigFloat(1) + BigFloat(2)^(-200)
    end
    for coefficient in (1,-1), sparse_pass in (false,true), ambient in (32,64)
        A = sparse(BigFloat[coefficient 2; sparse_pass ? 1 : 0 sparse_pass ? 0 : 1])
        problem = LinearProblem(A,zeros(BigFloat,2);
            row_lower=[BigFloat(5),nothing],row_upper=BigFloat[5,20],
            column_lower=[BigFloat(1),nothing],column_upper=[BigFloat(3),nothing])
        problem.column_lower[1] = Bound(stored)
        original = deepcopy(problem)
        setprecision(BigFloat,ambient) do
            rhs,pivot = big(5)//1,big(coefficient)//1
            @test isnothing(JSimplex._project_equality_bound(BigFloat,rhs,pivot,problem.column_lower[1]))
            pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
            result = pass(problem)
            # The only eligible pivot has an unrepresentable projected endpoint.
            @test result.problem === problem
            @test isempty(result.postsolve_stack)
            @test problem.column_lower == original.column_lower
            @test precision(bound_value(problem.column_lower[1])) == 256
        end
    end
end

@testset "Aggregation skips general products for unit projection coefficients" begin
function aggregation_unit_projection_probe(kind; count=128)
    sparse_pass = kind in (:sparse_positive, :sparse_negative)
    coefficient = kind in (:singleton_negative, :sparse_negative) ? -1.0 : kind == :nonunit ? 2.0 : 1.0
    A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
    row_lower = Union{Nothing,Float64}[5.0 for _ in 1:count]
    row_upper = fill(5.0,count)
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

    for (kind,limit) in ((:singleton_positive,28_000),(:singleton_negative,28_000),
                         (:sparse_positive,47_000),(:sparse_negative,47_000),
                         (:nonunit,29_450),(:free,18_050))
        problem,pass = aggregation_unit_projection_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = pass(problem)
        coefficient = kind in (:singleton_negative,:sparse_negative) ? -1.0 : kind == :nonunit ? 2.0 : 1.0
        @test result.problem.objective == [2-128/coefficient]
        @test result.problem.objective_constant == 128*5/coefficient
        @test JSimplex.postsolve_primal(result,[5-2coefficient]) == vcat(fill(2.0,128),5-2coefficient)
    end
end
