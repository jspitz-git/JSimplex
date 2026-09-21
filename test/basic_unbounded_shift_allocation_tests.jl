using SparseArrays

@testset "Basic presolve avoids unused shifts of unbounded rows" begin
function basic_unbounded_shift_probe(kind; count=128, T=Float64)
    coefficient = T(kind in (:negative_coefficient,:both_negative) ? -3 : 3)
    value = T(kind in (:negative_value,:both_negative) ? -2 : 2)
    problem = LinearProblem(sparse(hcat(fill(coefficient,count),fill(T(2),count))),T[2,3];objective_constant=T(7),
        row_lower=fill(kind == :finite ? T(-100) : nothing,count),
        row_upper=fill(kind in (:finite,:one_sided) ? T(100) : nothing,count),
        column_lower=T[value,-10],column_upper=T[value,10])
    return problem,JSimplex._presolve_basic
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative_coefficient,:negative_value,:both_negative,:finite,:one_sided), zero_value in (false,true)
        problem,pass = basic_unbounded_shift_probe(kind;count=4,T)
        if zero_value
            problem.column_lower[1] = problem.column_upper[1] = Bound(T(0))
        end
        original = deepcopy(problem)
        result = pass(problem)
        coefficient = problem.A[1,1]
        value = JSimplex.bound_value(problem.column_lower[1])
        shift = coefficient*value
        @test size(result.problem.A) == (4,1)
        @test Matrix(result.problem.A) == fill(T(2),4,1)
        @test result.problem.objective == T[3] && result.problem.objective_constant == T(7)+2value
        @test all((kind == :finite ? JSimplex.bound_value(result.problem.row_lower[i]) == T(-100)-shift : !isfinite(result.problem.row_lower[i])) && (kind in (:finite,:one_sided) ? JSimplex.bound_value(result.problem.row_upper[i]) == T(100)-shift : !isfinite(result.problem.row_upper[i])) for i in 1:4)
        @test all((isfinite(problem.row_lower[i]) || result.problem.row_lower[i] === problem.row_lower[i]) && (isfinite(problem.row_upper[i]) || result.problem.row_upper[i] === problem.row_upper[i]) for i in 1:4)
        @test JSimplex.postsolve_primal(result,T[1]) == T[value,1]
        basis = JSimplex.Basis(collect(2:5),[JSimplex.FREE_NONBASIC;fill(JSimplex.BASIC,4)])
        restored = JSimplex.restore_basis(result,basis)
        @test restored.basic_indices == [3,4,5,6] && restored.states[1] == JSimplex.AT_LOWER
        @test isequal(problem.A.nzval,original.A.nzval) && problem.A.colptr == original.A.colptr && problem.A.rowval == original.A.rowval && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper && problem.objective == original.objective && problem.objective_constant == original.objective_constant
    end
    for (kind,limit) in ((:positive,1_800),(:negative_coefficient,1_800),(:negative_value,1_800),(:both_negative,1_800),(:finite,12_350),(:one_sided,7_750))
        problem,pass = basic_unbounded_shift_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Basic presolve still checks every finite endpoint" begin
    for T in (Float32,Float64), direction in (-1,1), endpoint in (:neither,:lower,:upper,:both)
        tiny = direction*nextfloat(zero(T))
        problem = LinearProblem(sparse(reshape(T[tiny,1],1,2)),T[0,3];
            row_lower=[endpoint in (:lower,:both) ? T(0) : nothing],
            row_upper=[endpoint in (:upper,:both) ? T(0) : nothing],
            column_lower=T[0.5,-10],column_upper=T[0.5,10])
        original = deepcopy(problem)
        result = JSimplex._presolve_basic(problem)
        if endpoint == :neither
            @test size(result.problem.A) == (1,1) && result.problem.A[1,1] == T(1)
            @test !isfinite(result.problem.row_lower[1]) && !isfinite(result.problem.row_upper[1])
            @test JSimplex.postsolve_primal(result,T[0]) == T[0.5,0]
        else
            @test result.problem === problem
            @test isempty(result.postsolve_stack)
        end
        @test isequal(problem.A.nzval,original.A.nzval) && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
end

@testset "Unbounded basic rows still require an exact objective constant" begin
    for T in (Float32,Float64), direction in (-1,1)
        tiny = direction*nextfloat(zero(T))
        problem = LinearProblem(sparse(reshape(T[3,1],1,2)),T[tiny,3];
            row_lower=[nothing],row_upper=[nothing],
            column_lower=T[0.5,-10],column_upper=T[0.5,10])
        original = deepcopy(problem)
        result = JSimplex._presolve_basic(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test problem.objective == original.objective && problem.objective_constant == original.objective_constant && problem.A.nzval == original.A.nzval
    end
end

@testset "Unbounded basic rows preserve stored BigFloat values" begin
    for ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            value = BigFloat(2)+BigFloat(2)^(-200)
            LinearProblem(sparse(reshape(BigFloat[3,2],1,2)),BigFloat[0,3];objective_constant=BigFloat(1)/3,
                row_lower=[nothing],row_upper=[nothing],column_lower=[value,BigFloat(-10)],column_upper=[value,BigFloat(10)])
        end
        original = JSimplex._exact_rational(JSimplex.bound_value(problem.column_lower[1]))
        setprecision(BigFloat,ambient) do
            result = JSimplex._presolve_basic(problem)
            @test size(result.problem.A) == (1,1)
            @test result.problem.row_lower[1] === problem.row_lower[1] && result.problem.row_upper[1] === problem.row_upper[1]
            @test precision(result.problem.row_lower[1].value) == 256 && precision(result.problem.row_upper[1].value) == 256
            @test JSimplex._exact_rational(JSimplex.postsolve_primal(result,BigFloat[0])[1]) == original
            @test result.problem.objective_constant === problem.objective_constant && precision(result.problem.objective_constant) == 256
            @test JSimplex._exact_rational(JSimplex.bound_value(problem.column_lower[1])) == original
        end
    end
end
