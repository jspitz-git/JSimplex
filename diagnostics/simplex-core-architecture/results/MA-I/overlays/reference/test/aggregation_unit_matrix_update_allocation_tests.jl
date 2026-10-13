using SparseArrays

@testset "Unit matrix products preserve coefficients and projections" begin
    pairs = ((1,3),(-1,3),(1,-3),(-1,-3),(3,1),(3,-1),(-3,1),(-3,-1))
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), (multiplier,term) in pairs, old in (0,4), implied in (false,true)
        problem = LinearProblem(sparse(T[2 term; 2multiplier old]),T[0,2];objective_constant=T(7),
            row_lower=T[4,-20],row_upper=T[4,20],
            column_lower=[implied ? nothing : T(1),nothing],
            column_upper=[implied ? nothing : T(3),nothing])
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A) == (implied ? 1 : 2,1)
        @test result.problem.A[end,1] == T(old-multiplier*term)
        @test result.problem.objective == T[2]
        @test result.problem.objective_constant == T(7)
        @test JSimplex.bound_value(result.problem.row_lower[end]) == T(-20-4multiplier)
        @test JSimplex.bound_value(result.problem.row_upper[end]) == T(20-4multiplier)
        @test JSimplex.postsolve_primal(result,T[0]) == T[2,0]
        @test problem.A.nzval == original.A.nzval && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
end

@testset "Sequential unit products retain committed matrix updates" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), terms in ((1,3),(3,1),(-1,3),(3,-1))
        A = sparse(T[2 0 terms[1]; 0 -2 terms[2]; 2 2 5])
        problem = LinearProblem(A,T[0,0,2];objective_constant=T(7),
            row_lower=[T(4),T(-4),nothing],row_upper=T[4,-4,20],
            column_lower=fill(nothing,3),column_upper=fill(nothing,3))
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A) == (1,1)
        @test result.problem.A[1,1] == T(5-terms[1]+terms[2])
        @test JSimplex.bound_value(result.problem.row_upper[1]) == T(12)
        @test result.problem.objective == T[2] && result.problem.objective_constant == T(7)
        @test JSimplex.postsolve_primal(result,T[0]) == T[2,2,0]
        @test problem.A.nzval == original.A.nzval && problem.row_upper == original.row_upper
    end
end

@testset "Unit matrix products retain tiny exact changes" begin
    for kind in (:term,:multiplier), unit in (1,-1), direction in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            tiny = direction*BigFloat(2)^(-200)
            term = kind == :term ? tiny : BigFloat(unit)
            multiplier = kind == :multiplier ? tiny : BigFloat(unit)
            LinearProblem(sparse(BigFloat[2 term; 2multiplier 0]),BigFloat[0,2];objective_constant=BigFloat(7),
                row_lower=[BigFloat(0),nothing],row_upper=BigFloat[0,0],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        original_values = JSimplex._exact_rational.(problem.A.nzval)
        expected = -JSimplex._exact_rational(problem.A[2,1])*JSimplex._exact_rational(problem.A[1,2])/2
        setprecision(BigFloat,ambient) do
            result = JSimplex.aggregate_sparse_equalities(problem)
            @test size(result.problem.A) == (1,1)
            @test JSimplex._exact_rational(result.problem.A[1,1]) == expected
            @test !iszero(result.problem.A[1,1])
            @test JSimplex.bound_value(result.problem.row_upper[1]) == 0
            @test JSimplex.postsolve_primal(result,BigFloat[0]) == BigFloat[0,0]
            @test JSimplex._exact_rational.(problem.A.nzval) == original_values
        end
    end
end

@testset "Unit matrix shortcuts use exact comparisons and negation" begin
    for kind in (:unit_multiplier,:unit_term,:near_multiplier,:near_term), sign in (-1,1), direction in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            stored = sign*(BigFloat(1)+direction*BigFloat(2)^(-200))
            term = kind in (:unit_multiplier,:near_term) ? stored : BigFloat(kind == :unit_term ? sign : 2)
            multiplier = kind in (:unit_term,:near_multiplier) ? stored : BigFloat(kind == :unit_multiplier ? sign : 2)
            LinearProblem(sparse(BigFloat[2 term; 2multiplier 0]),BigFloat[0,2];objective_constant=BigFloat(7),
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

@testset "Sparse aggregation avoids unit matrix products" begin
function aggregation_unit_matrix_update_probe(kind; count=128)
    multiplier = kind == :multiplier_positive ? 1.0 : kind == :multiplier_negative ? -1.0 : kind == :zero ? 0.0 : 2.0
    term = kind == :term_positive ? 1.0 : kind == :term_negative ? -1.0 : 3.0
    rows = vcat(collect(1:count),fill(count+1,count),collect(1:count),count+1)
    columns = vcat(collect(1:count),collect(1:count),fill(count+1,count+1))
    values = vcat(fill(2.0,count),fill(2multiplier,count),fill(term,count),2.0)
    A = sparse(rows,columns,values,count+1,count+1)
    problem = LinearProblem(A,vcat(zeros(count),2.0);objective_constant=7.0,
        row_lower=vcat(fill(5.0,count),nothing),row_upper=vcat(fill(5.0,count),2000.0),
        column_lower=vcat(fill(1.0,count),nothing),column_upper=vcat(fill(3.0,count),nothing))
    return problem,JSimplex.aggregate_sparse_equalities
end

    for (kind,limit) in ((:multiplier_positive,37_600),(:multiplier_negative,37_850),
                         (:term_positive,38_750),(:term_negative,38_750),
                         (:nonunit,39_700),(:zero,29_450))
        problem,pass = aggregation_unit_matrix_update_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = pass(problem)
        multiplier = kind == :multiplier_positive ? 1.0 : kind == :multiplier_negative ? -1.0 : kind == :zero ? 0.0 : 2.0
        term = kind == :term_positive ? 1.0 : kind == :term_negative ? -1.0 : 3.0
        @test result.problem.objective == [2.0]
        @test result.problem.objective_constant == 7.0
        @test JSimplex.postsolve_primal(result,[1/term]) == vcat(fill(2.0,128),1/term)
        @test result.problem.A[end,1] == 2-128multiplier*term &&
            JSimplex.bound_value(result.problem.row_upper[end]) == 2000-640multiplier
    end
end
