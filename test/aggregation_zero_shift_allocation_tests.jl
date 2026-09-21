using SparseArrays

@testset "Zero right-hand sides preserve matrix substitution without shifting bounds" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (1,-1), coefficient in (-3,0,3), bounds in (:lower,:upper,:both,:free)
        has_lower = bounds in (:lower,:both)
        has_upper = bounds in (:upper,:both)
        # Keep the stored zero in the pivot column to exercise its multiplier.
        A = sparse([1,1,2,2],[1,2,1,2],T[pivot,1,coefficient,4],2,2)
        problem = LinearProblem(A,T[0,2];objective_constant=T(7),
            row_lower=[T(0),has_lower ? T(-10) : nothing],
            row_upper=[T(0),has_upper ? T(20) : nothing],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        multiplier = coefficient*pivot
        @test size(result.problem.A) == (1,1)
        @test result.problem.A[1,1] == T(4-multiplier)
        @test result.problem.objective == T[2]
        @test result.problem.objective_constant == T(7)
        @test has_lower ? JSimplex.bound_value(result.problem.row_lower[1]) == T(-10) : !isfinite(result.problem.row_lower[1])
        @test has_upper ? JSimplex.bound_value(result.problem.row_upper[1]) == T(20) : !isfinite(result.problem.row_upper[1])
        @test JSimplex.postsolve_primal(result,T[0]) == T[0,0]
        @test problem.A == original.A && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
end

@testset "Zero shifts retain stored high-precision bounds" begin
    for kind in (:rhs,:multiplier), pivot in (1,-1), direction in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            rhs = kind == :rhs ? BigFloat(0) : BigFloat(1)
            coefficient = kind == :multiplier ? BigFloat(0) : BigFloat(2)
            stored = BigFloat(7)+direction*BigFloat(2)^(-200)
            A = sparse([1,1,2,2],[1,2,1,2],BigFloat[pivot,1,coefficient,4],2,2)
            LinearProblem(A,BigFloat[0,2];objective_constant=BigFloat(7),
                row_lower=[rhs,nothing],row_upper=[rhs,stored],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        stored = JSimplex._exact_rational(JSimplex.bound_value(problem.row_upper[2]))
        setprecision(BigFloat,ambient) do
            result = JSimplex.aggregate_sparse_equalities(problem)
            @test size(result.problem.A) == (1,1)
            @test JSimplex._exact_rational(JSimplex.bound_value(result.problem.row_upper[1])) == stored
            @test precision(JSimplex.bound_value(result.problem.row_upper[1])) == 256
            @test JSimplex._exact_rational(JSimplex.bound_value(problem.row_upper[2])) == stored
            @test JSimplex.postsolve_primal(result,BigFloat[0]) == BigFloat[kind == :rhs ? 0 : pivot,0]
        end
    end
end

@testset "Tiny nonzero shift factors remain exact" begin
    for kind in (:rhs,:multiplier), pivot in (1,-1), direction in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            tiny = direction*BigFloat(2)^(-200)
            rhs = kind == :rhs ? tiny : BigFloat(2)
            coefficient = kind == :multiplier ? tiny : BigFloat(2)
            LinearProblem(sparse(BigFloat[pivot 1; coefficient 0]),BigFloat[0,2];objective_constant=BigFloat(7),
                row_lower=[rhs,nothing],row_upper=[rhs,BigFloat(0)],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        rhs_exact = JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1]))
        coefficient_exact = JSimplex._exact_rational(problem.A[2,1])
        setprecision(BigFloat,ambient) do
            result = JSimplex.aggregate_sparse_equalities(problem)
            @test size(result.problem.A) == (1,1)
            @test JSimplex._exact_rational(JSimplex.bound_value(result.problem.row_upper[1])) == -pivot*coefficient_exact*rhs_exact
            @test !iszero(JSimplex.bound_value(result.problem.row_upper[1]))
            @test JSimplex._exact_rational.(JSimplex.postsolve_primal(result,BigFloat[0])) == [pivot*rhs_exact,0]
            @test JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1])) == rhs_exact
            @test JSimplex._exact_rational(problem.A[2,1]) == coefficient_exact
        end
    end
end

@testset "Underflowing nonzero shifts still reject a candidate" begin
    for T in (Float32,Float64), pivot in (2,-2), direction in (-1,1)
        tiny = direction*nextfloat(zero(T))
        problem = LinearProblem(sparse(T[pivot 1; 1 0]),T[0,2];
            row_lower=[tiny,nothing],row_upper=T[tiny,0],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test problem.A == original.A && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
end

@testset "Sparse aggregation avoids zero shift products" begin
function aggregation_zero_shift_probe(kind; count=128)
    coefficient = kind in (:negative_positive,:negative_negative) ? -1.0 : 1.0
    other_coefficient = kind in (:positive_negative,:negative_negative) ? -2.0 : 2.0
    A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
    rhs = kind == :nonzero ? 5.0 : 0.0
    row_lower = Union{Nothing,Float64}[rhs for _ in 1:count]
    row_upper = fill(rhs,count)
    if kind != :singleton
        A = vcat(A,sparse(reshape(vcat(fill(other_coefficient,count),2.0),1,count+1)))
        push!(row_lower,nothing); push!(row_upper,1000.0)
    end
    problem = LinearProblem(A,vcat(zeros(count),2.0);objective_constant=7.0,
        row_lower,row_upper,column_lower=vcat(fill(1.0,count),nothing),
        column_upper=vcat(fill(3.0,count),nothing))
    pass = kind == :singleton ? JSimplex.aggregate_singleton_equalities : JSimplex.aggregate_sparse_equalities
    return problem,pass
end

    for (kind,limit) in ((:positive_positive,29_500),(:positive_negative,29_500),
                         (:negative_positive,30_250),(:negative_negative,30_250),
                         (:nonzero,37_400),(:singleton,17_400))
        problem,pass = aggregation_zero_shift_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = pass(problem)
        pivot = kind in (:negative_positive,:negative_negative) ? -1.0 : 1.0
        coefficient = kind in (:positive_negative,:negative_negative) ? -2.0 : 2.0
        rhs = kind == :nonzero ? 5.0 : 0.0
        @test result.problem.objective == [2.0]
        @test result.problem.objective_constant == 7.0
        @test JSimplex.postsolve_primal(result,[rhs-2pivot]) == vcat(fill(2.0,128),rhs-2pivot)
        @test kind == :singleton ? size(result.problem.A) == (128,1) :
            result.problem.A[end,1] == 2-128coefficient/pivot &&
            JSimplex.bound_value(result.problem.row_upper[end]) == 1000-128rhs*coefficient/pivot
    end
end
