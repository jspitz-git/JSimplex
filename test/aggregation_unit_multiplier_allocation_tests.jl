using SparseArrays

@testset "Unit multipliers preserve row coefficients and bound shifts" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (1,-1), coefficient in (-3,0,3), bounds in (:lower,:upper,:both,:free)
        has_lower = bounds in (:lower,:both)
        has_upper = bounds in (:upper,:both)
        # Keep the stored zero in the pivot column to exercise its multiplier.
        A = sparse([1,1,2,2],[1,2,1,2],T[pivot,1,coefficient,4],2,2)
        problem = LinearProblem(A,T[0,2];objective_constant=T(7),
            row_lower=[T(5),has_lower ? T(-10) : nothing],
            row_upper=[T(5),has_upper ? T(20) : nothing],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        multiplier = coefficient*pivot
        @test size(result.problem.A) == (1,1)
        @test result.problem.A[1,1] == T(4-multiplier)
        @test result.problem.objective == T[2]
        @test result.problem.objective_constant == T(7)
        @test has_lower ? JSimplex.bound_value(result.problem.row_lower[1]) == T(-10-5multiplier) : !isfinite(result.problem.row_lower[1])
        @test has_upper ? JSimplex.bound_value(result.problem.row_upper[1]) == T(20-5multiplier) : !isfinite(result.problem.row_upper[1])
        @test JSimplex.postsolve_primal(result,T[5]) == T[0,5]
        @test problem.A == original.A && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
end

@testset "Tiny unit multipliers preserve exact coefficient and bound updates" begin
    for pivot in (1,-1), direction in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            tiny = direction*BigFloat(2)^(-200)
            LinearProblem(sparse(BigFloat[pivot 1; tiny 0]),BigFloat[0,2];objective_constant=BigFloat(7),
                row_lower=[BigFloat(2),nothing],row_upper=BigFloat[2,0],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        stored = JSimplex._exact_rational(problem.A[2,1])
        setprecision(BigFloat,ambient) do
            result = JSimplex.aggregate_sparse_equalities(problem)
            @test size(result.problem.A) == (1,1)
            @test JSimplex._exact_rational(result.problem.A[1,1]) == -pivot*stored
            @test JSimplex._exact_rational(JSimplex.bound_value(result.problem.row_upper[1])) == -2pivot*stored
            @test JSimplex.postsolve_primal(result,BigFloat[0]) == BigFloat[2pivot,0]
            @test JSimplex._exact_rational(problem.A[2,1]) == stored
            @test precision(problem.A[2,1]) == 256
        end
    end
end

@testset "Unit multipliers retain exact conversion and unit comparisons" begin
    for kind in (:coefficient,:pivot,:matrix), sign in (-1,1), direction in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            stored = sign*(BigFloat(1)+direction*BigFloat(2)^(-200))
            pivot = kind == :pivot ? stored : BigFloat(sign)
            coefficient = kind in (:coefficient,:matrix) ? stored : BigFloat(1)
            LinearProblem(sparse(BigFloat[pivot 1; coefficient 0]),BigFloat[0,2];objective_constant=BigFloat(7),
                row_lower=[BigFloat(1),nothing],row_upper=[BigFloat(1),kind == :matrix ? nothing : BigFloat(0)],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        original = deepcopy(problem)
        original_values = JSimplex._exact_rational.(problem.A.nzval)
        setprecision(BigFloat,ambient) do
            result = JSimplex.aggregate_sparse_equalities(problem)
            @test result.problem === problem
            @test isempty(result.postsolve_stack)
            @test JSimplex._exact_rational.(problem.A.nzval) == original_values
            @test problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
        end
    end
end

@testset "Sparse aggregation avoids unit-pivot multiplier division" begin
function aggregation_unit_multiplier_probe(kind; count=128)
    coefficient = kind in (:negative_positive,:negative_negative) ? -1.0 : kind == :nonunit ? 2.0 : 1.0
    other_coefficient = kind in (:positive_negative,:negative_negative) ? -2.0 : 2.0
    A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
    row_lower = Union{Nothing,Float64}[5.0 for _ in 1:count]
    row_upper = fill(5.0,count)
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

    for (kind,limit) in ((:positive_positive,37_600),(:positive_negative,37_600),
                         (:negative_positive,38_100),(:negative_negative,38_100),
                         (:nonunit,39_700),(:singleton,19_600))
        problem,pass = aggregation_unit_multiplier_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = pass(problem)
        pivot = kind in (:negative_positive,:negative_negative) ? -1.0 : kind == :nonunit ? 2.0 : 1.0
        coefficient = kind in (:positive_negative,:negative_negative) ? -2.0 : 2.0
        multiplier = coefficient/pivot
        @test result.problem.objective == [2.0]
        @test result.problem.objective_constant == 7.0
        @test JSimplex.postsolve_primal(result,[5-2pivot]) == vcat(fill(2.0,128),5-2pivot)
        @test kind == :singleton ? size(result.problem.A) == (128,1) :
            result.problem.A[end,1] == 2-128multiplier &&
            JSimplex.bound_value(result.problem.row_upper[end]) == 1000-640multiplier
    end
end
