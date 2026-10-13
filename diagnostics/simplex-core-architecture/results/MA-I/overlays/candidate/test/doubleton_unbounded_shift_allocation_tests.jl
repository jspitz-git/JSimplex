using SparseArrays

@testset "Doubleton avoids unused shifts of unbounded rows" begin
function doubleton_unbounded_shift_probe(kind; count=128, T=Float64)
    coefficient = T(kind in (:negative_coefficient,:both_negative) ? -3 : 3)
    rhs = T(kind in (:negative_alpha,:both_negative) ? -4 : 4)
    A = sparse(hcat(vcat(T(2),fill(coefficient,count)),vcat(T(1),fill(T(2),count))))
    problem = LinearProblem(A,T[2,3];objective_constant=T(7),
        row_lower=Union{Nothing,T}[rhs;fill(kind == :finite ? T(-100) : nothing,count)],
        row_upper=Union{Nothing,T}[rhs;fill(kind in (:finite,:one_sided) ? T(100) : nothing,count)],
        column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
    return problem,JSimplex.substitute_free_doubleton
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative_coefficient,:negative_alpha,:both_negative,:finite,:one_sided), zero_rhs in (false,true)
        problem,pass = doubleton_unbounded_shift_probe(kind;count=4,T)
        if zero_rhs
            problem.row_lower[1] = problem.row_upper[1] = Bound(T(0))
        end
        original = deepcopy(problem)
        result = pass(problem)
        coefficient = problem.A[2,1]
        rhs = JSimplex.bound_value(problem.row_lower[1])
        shift = coefficient*rhs/T(2)
        @test size(result.problem.A) == (4,1)
        @test Matrix(result.problem.A) == fill(T(2)-coefficient/T(2),4,1)
        @test result.problem.objective == T[2] && result.problem.objective_constant == T(7)+rhs
        @test all((kind == :finite ? JSimplex.bound_value(result.problem.row_lower[i]) == T(-100)-shift : !isfinite(result.problem.row_lower[i])) && (kind in (:finite,:one_sided) ? JSimplex.bound_value(result.problem.row_upper[i]) == T(100)-shift : !isfinite(result.problem.row_upper[i])) for i in 1:4)
        @test all((isfinite(problem.row_lower[i+1]) || result.problem.row_lower[i] === problem.row_lower[i+1]) && (isfinite(problem.row_upper[i+1]) || result.problem.row_upper[i] === problem.row_upper[i+1]) for i in 1:4)
        @test JSimplex.postsolve_primal(result,T[2]) == T[(rhs-T(2))/T(2),2]
        basis = JSimplex.Basis(collect(2:5),[JSimplex.FREE_NONBASIC;fill(JSimplex.BASIC,4)])
        @test JSimplex.restore_basis(result,basis).basic_indices == [1,4,5,6,7]
        @test isequal(problem.A.nzval,original.A.nzval) && problem.A.colptr == original.A.colptr && problem.A.rowval == original.A.rowval && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper && problem.objective == original.objective && problem.objective_constant == original.objective_constant
    end
    for (kind,limit) in ((:positive,8_200),(:negative_coefficient,8_200),(:negative_alpha,8_200),(:both_negative,8_200),(:finite,18_250),(:one_sided,13_650))
        problem,pass = doubleton_unbounded_shift_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Unbounded doubleton rows still require exact matrix updates" begin
    for T in (Float32,Float64), direction in (-1,1)
        tiny = direction*nextfloat(zero(T))
        problem = LinearProblem(sparse(T[2 1; tiny 0]),T[0,3];
            row_lower=[T(4),nothing],row_upper=[T(4),nothing],
            column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        original = deepcopy(problem)
        result = JSimplex.substitute_free_doubleton(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test isequal(problem.A.nzval,original.A.nzval) && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
end

@testset "Either finite endpoint still requires an exact doubleton shift" begin
    for T in (Float32,Float64), direction in (-1,1), endpoint in (:neither,:lower,:upper)
        tiny = direction*nextfloat(zero(T))
        problem = LinearProblem(sparse(T[1 1; 0.5 1]),T[0,3];
            row_lower=[tiny,endpoint == :lower ? T(0) : nothing],
            row_upper=[tiny,endpoint == :upper ? T(0) : nothing],
            column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        original = deepcopy(problem)
        result = JSimplex.substitute_free_doubleton(problem)
        if endpoint == :neither
            @test size(result.problem.A) == (1,1) && result.problem.A[1,1] == T(0.5)
            @test !isfinite(result.problem.row_lower[1]) && !isfinite(result.problem.row_upper[1])
            @test JSimplex.postsolve_primal(result,T[0]) == T[tiny,0]
        else
            @test result.problem === problem
            @test isempty(result.postsolve_stack)
        end
        @test isequal(problem.A.nzval,original.A.nzval) && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
end

@testset "Unbounded doubleton endpoints retain stored BigFloat identity" begin
    for ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            p = LinearProblem(sparse(BigFloat[2 1; 3 2]),BigFloat[0,3];
                row_lower=[BigFloat(4),nothing],row_upper=[BigFloat(4),nothing],
                column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
            p.row_lower[2] = Bound{BigFloat}(nothing)
            p.row_upper[2] = Bound{BigFloat}(nothing)
            p
        end
        saved = deepcopy(problem)
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            @test size(result.problem.A) == (1,1)
            @test result.problem.row_lower[1] === problem.row_lower[2]
            @test result.problem.row_upper[1] === problem.row_upper[2]
            @test precision(result.problem.row_lower[1].value) == 256
            @test precision(result.problem.row_upper[1].value) == 256
            @test problem.row_lower == saved.row_lower && problem.row_upper == saved.row_upper
        end
    end
end
