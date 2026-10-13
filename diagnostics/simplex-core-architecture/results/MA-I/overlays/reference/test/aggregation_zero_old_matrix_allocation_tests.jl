using SparseArrays

@testset "Zero old coefficients preserve sparse fill and projections" begin
    pairs = ((1,3),(-1,3),(2,3),(-2,3),(2,-3),(-2,-3),(2,1//2),(-2,-1//2))
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), (multiplier,term) in pairs, implied in (false,true)
        problem = LinearProblem(sparse(T[2 term; 2multiplier 0]),T[0,2];objective_constant=T(7),
            row_lower=T[4,-20],row_upper=T[4,20],
            column_lower=[implied ? nothing : T(1),nothing],
            column_upper=[implied ? nothing : T(3),nothing])
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A) == (implied ? 1 : 2,1)
        @test result.problem.A[end,1] == T(-multiplier*term)
        @test result.problem.objective == T[2]
        @test result.problem.objective_constant == T(7)
        @test JSimplex.bound_value(result.problem.row_lower[end]) == T(-20-4multiplier)
        @test JSimplex.bound_value(result.problem.row_upper[end]) == T(20-4multiplier)
        @test JSimplex.postsolve_primal(result,T[0]) == T[2,0]
        @test problem.A.nzval == original.A.nzval && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
end

@testset "Zero-old checks follow committed matrix updates" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), old in (0,3), term in (1,-1)
        problem = LinearProblem(sparse(T[2 0 3; 0 -2 term; 2 2 old]),T[0,0,2];objective_constant=T(7),
            row_lower=[T(4),T(-4),nothing],row_upper=T[4,-4,20],
            column_lower=fill(nothing,3),column_upper=fill(nothing,3))
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A) == (1,1)
        @test result.problem.A[1,1] == T(old-3+term)
        @test JSimplex.bound_value(result.problem.row_upper[1]) == T(12)
        @test result.problem.objective == T[2] && result.problem.objective_constant == T(7)
        @test JSimplex.postsolve_primal(result,T[0]) == T[2,2,0]
        @test problem.A.nzval == original.A.nzval && problem.row_upper == original.row_upper
    end
end

@testset "Zero-old shortcuts retain exact values and rejection" begin
    for kind in (:old,:product), direction in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            delta = direction*BigFloat(2)^(-200)
            old = kind == :old ? delta : BigFloat(0)
            term = kind == :product ? BigFloat(1)+delta : BigFloat(1)
            LinearProblem(sparse(BigFloat[2 term; 4 old]),BigFloat[0,2];objective_constant=BigFloat(7),
                row_lower=[BigFloat(0),nothing],row_upper=BigFloat[0,0],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        original_values = JSimplex._exact_rational.(problem.A.nzval)
        original_bounds = deepcopy(problem.row_upper)
        setprecision(BigFloat,ambient) do
            result = JSimplex.aggregate_sparse_equalities(problem)
            @test result.problem === problem
            @test isempty(result.postsolve_stack)
            @test JSimplex._exact_rational.(problem.A.nzval) == original_values
            @test problem.row_upper == original_bounds
        end
    end
end

@testset "Negated tiny products remain exact sparse entries" begin
    for multiplier in (2,-2), direction in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            tiny = direction*BigFloat(2)^(-200)
            LinearProblem(sparse(BigFloat[2 tiny; 2multiplier 0]),BigFloat[0,2];objective_constant=BigFloat(7),
                row_lower=[BigFloat(0),nothing],row_upper=BigFloat[0,0],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        term = JSimplex._exact_rational(problem.A[1,2])
        setprecision(BigFloat,ambient) do
            result = JSimplex.aggregate_sparse_equalities(problem)
            @test size(result.problem.A) == (1,1)
            @test JSimplex._exact_rational(result.problem.A[1,1]) == -multiplier*term
            @test !iszero(result.problem.A[1,1])
            @test JSimplex.postsolve_primal(result,BigFloat[0]) == BigFloat[0,0]
            @test JSimplex._exact_rational(problem.A[1,2]) == term
            @test precision(problem.A[1,2]) == 256
        end
    end
end

@testset "Unrepresentable fill cannot underflow to zero" begin
    for T in (Float32,Float64), coefficient in (1,-1), direction in (-1,1)
        tiny = direction*nextfloat(zero(T))
        problem = LinearProblem(sparse(T[2 tiny; coefficient 0]),T[0,2];
            row_lower=[T(0),nothing],row_upper=T[0,0],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test problem.A.nzval == original.A.nzval && problem.row_upper == original.row_upper
    end
end

@testset "Sparse fill avoids subtracting from exact zero" begin
function aggregation_zero_old_matrix_probe(kind; count=128)
    multiplier = kind in (:negative_positive,:negative_negative) ? -2.0 : kind == :zero_multiplier ? 0.0 : 2.0
    term = kind in (:positive_negative,:negative_negative) ? -3.0 : 3.0
    old = kind == :nonzero_old ? 2.0 : 0.0
    odd = collect(1:2:2count); even = odd .+ 1
    rows = vcat(odd,odd,even); columns = vcat(odd,even,odd)
    values = vcat(fill(2.0,count),fill(term,count),fill(2multiplier,count))
    if !iszero(old)
        append!(rows,even); append!(columns,even); append!(values,fill(old,count))
    end
    A = sparse(rows,columns,values,2count,2count)
    lower = Union{Nothing,Float64}[isodd(i) ? 5.0 : nothing for i in 1:2count]
    upper = [isodd(i) ? 5.0 : 20.0 for i in 1:2count]
    problem = LinearProblem(A,[isodd(i) ? 0.0 : 2.0 for i in 1:2count];objective_constant=7.0,
        row_lower=lower,row_upper=upper,
        column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
        column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

    for (kind,limit) in ((:positive_positive,45_550),(:positive_negative,45_550),
                         (:negative_positive,45_550),(:negative_negative,45_550),
                         (:nonzero_old,47_000),(:zero_multiplier,35_350))
        problem,pass = aggregation_zero_old_matrix_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = pass(problem)
        multiplier = kind in (:negative_positive,:negative_negative) ? -2.0 : kind == :zero_multiplier ? 0.0 : 2.0
        term = kind in (:positive_negative,:negative_negative) ? -3.0 : 3.0
        old = kind == :nonzero_old ? 2.0 : 0.0
        @test result.problem.objective == fill(2.0,128)
        @test result.problem.objective_constant == 7.0
        @test JSimplex.postsolve_primal(result,fill(1/term,128)) == repeat([2.0,1/term],128)
        @test all(result.problem.A[2i,i] == old-multiplier*term &&
            JSimplex.bound_value(result.problem.row_upper[2i]) == 20-5multiplier for i in 1:128)
    end
end
