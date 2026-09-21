using SparseArrays

@testset "Unit shift factors preserve bounds and matrix substitution" begin
    pairs = ((1,3),(-1,3),(1,-3),(-1,-3),(3,1),(3,-1),(-3,1),(-3,-1))
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), (multiplier,rhs) in pairs, bounds in (:lower,:upper,:both,:free)
        has_lower = bounds in (:lower,:both)
        has_upper = bounds in (:upper,:both)
        problem = LinearProblem(sparse(T[2 1; 2multiplier 4]),T[0,2];objective_constant=T(7),
            row_lower=[T(rhs),has_lower ? T(-10) : nothing],
            row_upper=[T(rhs),has_upper ? T(20) : nothing],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        shift = multiplier*rhs
        @test size(result.problem.A) == (1,1)
        @test result.problem.A[1,1] == T(4-multiplier)
        @test result.problem.objective == T[2]
        @test result.problem.objective_constant == T(7)
        @test has_lower ? JSimplex.bound_value(result.problem.row_lower[1]) == T(-10-shift) : !isfinite(result.problem.row_lower[1])
        @test has_upper ? JSimplex.bound_value(result.problem.row_upper[1]) == T(20-shift) : !isfinite(result.problem.row_upper[1])
        @test JSimplex.postsolve_primal(result,T[0]) == T[rhs/2,0]
        @test problem.A == original.A && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
end

@testset "Unit shift factors preserve tiny exact values" begin
    for kind in (:rhs,:multiplier), unit in (1,-1), direction in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            tiny = direction*BigFloat(2)^(-200)
            rhs = kind == :rhs ? tiny : BigFloat(unit)
            multiplier = kind == :multiplier ? tiny : BigFloat(unit)
            LinearProblem(sparse(BigFloat[2 1; 2multiplier 0]),BigFloat[0,2];objective_constant=BigFloat(7),
                row_lower=[rhs,nothing],row_upper=[rhs,BigFloat(0)],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        rhs_exact = JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1]))
        coefficient_exact = JSimplex._exact_rational(problem.A[2,1])
        setprecision(BigFloat,ambient) do
            result = JSimplex.aggregate_sparse_equalities(problem)
            @test size(result.problem.A) == (1,1)
            @test JSimplex._exact_rational(JSimplex.bound_value(result.problem.row_upper[1])) == -coefficient_exact*rhs_exact/2
            @test !iszero(JSimplex.bound_value(result.problem.row_upper[1]))
            @test JSimplex._exact_rational.(JSimplex.postsolve_primal(result,BigFloat[0])) == [rhs_exact/2,0]
            @test JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1])) == rhs_exact
            @test JSimplex._exact_rational(problem.A[2,1]) == coefficient_exact
        end
    end
end

@testset "Unit shift shortcuts retain exact conversion and comparisons" begin
    for kind in (:unit_multiplier,:unit_rhs,:near_multiplier,:near_rhs), sign in (-1,1), direction in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            stored = sign*(BigFloat(1)+direction*BigFloat(2)^(-200))
            rhs = kind in (:unit_multiplier,:near_rhs) ? stored : BigFloat(kind == :unit_rhs ? sign : 2)
            multiplier = kind in (:unit_rhs,:near_multiplier) ? stored : BigFloat(kind == :unit_multiplier ? sign : 2)
            LinearProblem(sparse(BigFloat[2 1; 2multiplier 0]),BigFloat[0,2];objective_constant=BigFloat(7),
                row_lower=[rhs,nothing],row_upper=[rhs,BigFloat(0)],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        original_rhs = JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1]))
        original_values = JSimplex._exact_rational.(problem.A.nzval)
        setprecision(BigFloat,ambient) do
            result = JSimplex.aggregate_sparse_equalities(problem)
            @test result.problem === problem
            @test isempty(result.postsolve_stack)
            @test JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1])) == original_rhs
            @test JSimplex._exact_rational.(problem.A.nzval) == original_values
        end
    end
end

@testset "Sparse aggregation avoids unit shift products" begin
function aggregation_unit_shift_probe(kind; count=128)
    multiplier = kind == :multiplier_negative ? -1.0 : kind == :multiplier_positive ? 1.0 : 2.0
    rhs = kind == :rhs_positive ? 1.0 : kind == :rhs_negative ? -1.0 : kind == :zero ? 0.0 : 5.0
    A = hcat(sparse(1:count,1:count,fill(2.0,count),count,count),sparse(ones(count,1)))
    A = vcat(A,sparse(reshape(vcat(fill(2multiplier,count),2.0),1,count+1)))
    problem = LinearProblem(A,vcat(zeros(count),2.0);objective_constant=7.0,
        row_lower=vcat(fill(rhs,count),nothing),row_upper=vcat(fill(rhs,count),1000.0),
        column_lower=vcat(fill(1.0,count),nothing),column_upper=vcat(fill(3.0,count),nothing))
    return problem,JSimplex.aggregate_sparse_equalities
end

    for (kind,limit) in ((:multiplier_positive,38_750),(:multiplier_negative,38_750),
                         (:rhs_positive,38_750),(:rhs_negative,38_750),
                         (:nonunit,39_700),(:zero,31_750))
        problem,pass = aggregation_unit_shift_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = pass(problem)
        multiplier = kind == :multiplier_negative ? -1.0 : kind == :multiplier_positive ? 1.0 : 2.0
        rhs = kind == :rhs_positive ? 1.0 : kind == :rhs_negative ? -1.0 : kind == :zero ? 0.0 : 5.0
        @test result.problem.objective == [2.0]
        @test result.problem.objective_constant == 7.0
        @test JSimplex.postsolve_primal(result,[rhs-4]) == vcat(fill(2.0,128),rhs-4)
        @test result.problem.A[end,1] == 2-128multiplier &&
            JSimplex.bound_value(result.problem.row_upper[end]) == 1000-128rhs*multiplier
    end
end
