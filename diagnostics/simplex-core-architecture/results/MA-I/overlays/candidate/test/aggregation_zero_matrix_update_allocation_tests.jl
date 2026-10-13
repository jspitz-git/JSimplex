using SparseArrays

@testset "Zero multipliers preserve matrix entries and projections" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (2,-2), term in (1,-3,1//2), old in (0,4), implied in (false,true)
        A = sparse([1,1,2,2],[1,2,1,2],T[pivot,term,0,old],2,2)
        problem = LinearProblem(A,T[0,2];objective_constant=T(7),
            row_lower=T[2pivot,-10],row_upper=T[2pivot,20],
            column_lower=[implied ? nothing : T(1),nothing],
            column_upper=[implied ? nothing : T(3),nothing])
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A) == (implied ? 1 : 2,1)
        @test result.problem.A[end,1] == T(old)
        @test result.problem.objective == T[2]
        @test result.problem.objective_constant == T(7)
        @test JSimplex.bound_value(result.problem.row_lower[end]) == T(-10)
        @test JSimplex.bound_value(result.problem.row_upper[end]) == T(20)
        @test JSimplex.postsolve_primal(result,T[0]) == T[2,0]
        @test problem.A.nzval == original.A.nzval && problem.A.colptr == original.A.colptr && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
end

@testset "Zero matrix updates retain prior committed coefficients" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), coefficients in ((0,2),(2,0))
        A = sparse([1,2,3,3,1,2,3],[1,2,1,2,3,3,3],T[2,-2,coefficients[1],coefficients[2],1,1,3],3,3)
        problem = LinearProblem(A,T[0,0,2];objective_constant=T(7),
            row_lower=[T(4),T(-4),nothing],row_upper=T[4,-4,20],
            column_lower=fill(nothing,3),column_upper=fill(nothing,3))
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A) == (1,1)
        @test result.problem.A[1,1] == T(3-coefficients[1]/2+coefficients[2]/2)
        @test JSimplex.bound_value(result.problem.row_upper[1]) == T(16)
        @test result.problem.objective == T[2] && result.problem.objective_constant == T(7)
        @test JSimplex.postsolve_primal(result,T[0]) == T[2,2,0]
        @test problem.A.nzval == original.A.nzval && problem.row_upper == original.row_upper
    end
end

@testset "Unchanged matrix coefficients still require exact representation" begin
    for pivot in (2,-2), direction in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            stored = BigFloat(3)+direction*BigFloat(2)^(-200)
            A = sparse([1,1,2,2],[1,2,1,2],BigFloat[pivot,1,0,stored],2,2)
            LinearProblem(A,BigFloat[0,2];objective_constant=BigFloat(7),
                row_lower=[BigFloat(2pivot),nothing],row_upper=BigFloat[2pivot,20],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        original_values = JSimplex._exact_rational.(problem.A.nzval)
        original_bounds = deepcopy(problem.row_upper)
        setprecision(BigFloat,ambient) do
            result = JSimplex.aggregate_sparse_equalities(problem)
            @test result.problem === problem
            @test isempty(result.postsolve_stack)
            @test JSimplex._exact_rational.(problem.A.nzval) == original_values
            @test precision(problem.A[2,2]) == 256
            @test problem.row_upper == original_bounds
        end
    end
end

@testset "Tiny nonzero multipliers retain exact matrix updates" begin
    for pivot in (2,-2), direction in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            tiny = direction*BigFloat(2)^(-200)
            LinearProblem(sparse(BigFloat[pivot 1; tiny 0]),BigFloat[0,2];objective_constant=BigFloat(7),
                row_lower=[BigFloat(2),nothing],row_upper=BigFloat[2,0],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        coefficient = JSimplex._exact_rational(problem.A[2,1])
        setprecision(BigFloat,ambient) do
            result = JSimplex.aggregate_sparse_equalities(problem)
            @test size(result.problem.A) == (1,1)
            @test JSimplex._exact_rational(result.problem.A[1,1]) == -coefficient/pivot
            @test !iszero(result.problem.A[1,1])
            @test JSimplex.postsolve_primal(result,BigFloat[0]) == BigFloat[2/pivot,0]
            @test JSimplex._exact_rational(problem.A[2,1]) == coefficient
            @test precision(problem.A[2,1]) == 256
        end
    end
end

@testset "Underflowing matrix changes must not become zero" begin
    for T in (Float32,Float64), pivot in (2,-2), direction in (-1,1)
        tiny = direction*nextfloat(zero(T))
        problem = LinearProblem(sparse(T[pivot 1; tiny 0]),T[0,2];
            row_lower=[T(0),nothing],row_upper=T[0,0],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test problem.A.nzval == original.A.nzval && problem.row_upper == original.row_upper
    end
end

@testset "Sparse aggregation avoids zero matrix-update arithmetic" begin
function aggregation_zero_matrix_update_probe(kind; count=128)
    pivot = kind in (:negative_present,:negative_absent) ? -2.0 : 2.0
    stored = kind == :nonzero ? 2.0 : 0.0
    old_coefficient = kind in (:positive_absent,:negative_absent) ? 0.0 : 2.0
    rows = vcat(collect(1:count),fill(count+1,count),collect(1:count),count+1)
    columns = vcat(collect(1:count),collect(1:count),fill(count+1,count+1))
    values = vcat(fill(pivot,count),fill(stored,count),ones(count),old_coefficient)
    A = sparse(rows,columns,values,count+1,count+1)
    lower = vcat(fill(5.0,count),nothing)
    upper = vcat(fill(5.0,count),1000.0)
    if kind == :singleton
        A = A[1:count,:]; lower = lower[1:count]; upper = upper[1:count]
    end
    problem = LinearProblem(A,vcat(zeros(count),2.0);objective_constant=7.0,
        row_lower=lower,row_upper=upper,column_lower=vcat(fill(1.0,count),nothing),
        column_upper=vcat(fill(3.0,count),nothing))
    pass = kind == :singleton ? JSimplex.aggregate_singleton_equalities : JSimplex.aggregate_sparse_equalities
    return problem,pass
end

    for (kind,limit) in ((:positive_present,31_500),(:negative_present,31_500),
                         (:positive_absent,31_000),(:negative_absent,31_000),
                         (:nonzero,38_550),(:singleton,20_750))
        problem,pass = aggregation_zero_matrix_update_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = pass(problem)
        pivot = kind in (:negative_present,:negative_absent) ? -2.0 : 2.0
        old_coefficient = kind in (:positive_absent,:negative_absent) ? 0.0 : 2.0
        multiplier = kind == :nonzero ? 1.0 : 0.0
        @test result.problem.objective == [2.0]
        @test result.problem.objective_constant == 7.0
        @test JSimplex.postsolve_primal(result,[5-2pivot]) == vcat(fill(2.0,128),5-2pivot)
        @test kind == :singleton ? size(result.problem.A) == (128,1) :
            result.problem.A[end,1] == old_coefficient-128multiplier &&
            JSimplex.bound_value(result.problem.row_upper[end]) == 1000-640multiplier
    end
end
