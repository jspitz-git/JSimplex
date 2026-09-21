using SparseArrays

@testset "Basic presolve reuses exact zero for row shifts" begin
function basic_zero_shift_probe(kind; count=128, T=Float64)
    coefficient = T(kind == :negative ? -3 : 3)
    value = kind == :nonzero ? T(2) : kind == :negative ? -zero(T) : zero(T)
    problem = LinearProblem(sparse(hcat(fill(coefficient,count),fill(T(2),count))),T[2,3];objective_constant=T(7),
        row_lower=fill(kind in (:upper_only,:unbounded) ? nothing : T(-100),count),
        row_upper=fill(kind in (:lower_only,:unbounded) ? nothing : T(100),count),
        column_lower=T[value,-10],column_upper=T[value,10])
    return problem,JSimplex._presolve_basic
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative,:lower_only,:upper_only,:nonzero,:unbounded), cached in (false,true)
        problem,pass = basic_zero_shift_probe(kind;count=4,T)
        selections = [JSimplex._elimination_value(problem,column) for column in 1:2]
        saved_selections = deepcopy(selections)
        original = deepcopy(problem)
        result = cached ? pass(problem;selections) : pass(problem)
        coefficient = problem.A[1,1]
        value = JSimplex.bound_value(problem.column_lower[1])
        shift = coefficient*value
        @test size(result.problem.A) == (4,1)
        @test Matrix(result.problem.A) == fill(T(2),4,1)
        @test result.problem.objective == T[3] && result.problem.objective_constant == T(7)+2value
        @test all((kind in (:upper_only,:unbounded) ? !isfinite(result.problem.row_lower[i]) : JSimplex.bound_value(result.problem.row_lower[i]) == T(-100)-shift) && (kind in (:lower_only,:unbounded) ? !isfinite(result.problem.row_upper[i]) : JSimplex.bound_value(result.problem.row_upper[i]) == T(100)-shift) for i in 1:4)
        @test kind == :nonzero || all(result.problem.row_lower[i] === problem.row_lower[i] && result.problem.row_upper[i] === problem.row_upper[i] for i in 1:4)
        @test isequal(JSimplex.postsolve_primal(result,T[1]),T[value,1])
        basis = JSimplex.Basis(collect(2:5),[JSimplex.FREE_NONBASIC;fill(JSimplex.BASIC,4)])
        restored = JSimplex.restore_basis(result,basis)
        @test restored.basic_indices == [3,4,5,6] && restored.states[1] == JSimplex.AT_LOWER
        @test isequal(problem.A.nzval,original.A.nzval) && problem.A.colptr == original.A.colptr && problem.A.rowval == original.A.rowval && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper && problem.objective == original.objective && problem.objective_constant == original.objective_constant && isequal(selections,saved_selections)
    end
    for (kind,limit) in ((:positive,600),(:negative,600),(:lower_only,600),(:upper_only,600),(:nonzero,12_350),(:unbounded,300))
        problem,pass = basic_zero_shift_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Basic zero-shift shortcut preserves tiny nonzero fixed values" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), direction in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            tiny = T in (Float32,Float64) ? direction*nextfloat(zero(T)) : T(direction*(BigInt(1)//(BigInt(1)<<200)))
            LinearProblem(sparse(reshape(T[2,1],1,2)),T[0,3];objective_constant=T(7),
                row_lower=T[0],row_upper=[nothing],column_lower=T[tiny,-10],column_upper=T[tiny,10])
        end
        original = JSimplex._exact_rational(JSimplex.bound_value(problem.column_lower[1]))
        setprecision(BigFloat,ambient) do
            result = JSimplex._presolve_basic(problem)
            @test size(result.problem.A) == (1,1)
            @test JSimplex._exact_rational(JSimplex.bound_value(result.problem.row_lower[1])) == -2original
            @test !iszero(JSimplex.bound_value(result.problem.row_lower[1]))
            @test JSimplex._exact_rational(JSimplex.postsolve_primal(result,T[0])[1]) == original
            @test result.problem.objective == T[3] && result.problem.objective_constant == T(7)
            @test JSimplex._exact_rational(JSimplex.bound_value(problem.column_lower[1])) == original
        end
    end
end

@testset "Basic nonzero fixed values still reject inexact row shifts" begin
    for T in (Float32,Float64), direction in (-1,1), endpoint in (:lower,:upper,:both)
        tiny = direction*nextfloat(zero(T))
        problem = LinearProblem(sparse(reshape(T[0.5,1],1,2)),T[0,3];
            row_lower=[endpoint in (:lower,:both) ? T(0) : nothing],
            row_upper=[endpoint in (:upper,:both) ? T(0) : nothing],
            column_lower=T[tiny,-10],column_upper=T[tiny,10])
        original = deepcopy(problem)
        result = JSimplex._presolve_basic(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test problem.A.nzval == original.A.nzval && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
end

@testset "Basic zero shifts preserve signed zero and high-precision bounds" begin
    for ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            value = -zero(BigFloat)
            LinearProblem(sparse(reshape(BigFloat[BigFloat(3)+BigFloat(2)^(-200),2],1,2)),BigFloat[2,3];objective_constant=BigFloat(1)/3,
                row_lower=[BigFloat(1)/3],row_upper=[BigFloat(2)/3],column_lower=[value,BigFloat(-10)],column_upper=[value,BigFloat(10)])
        end
        lower_exact = JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1]))
        upper_exact = JSimplex._exact_rational(JSimplex.bound_value(problem.row_upper[1]))
        setprecision(BigFloat,ambient) do
            result = JSimplex._presolve_basic(problem)
            @test size(result.problem.A) == (1,1)
            @test result.problem.row_lower[1] === problem.row_lower[1] && result.problem.row_upper[1] === problem.row_upper[1]
            @test precision(JSimplex.bound_value(result.problem.row_lower[1])) == 256 && precision(JSimplex.bound_value(result.problem.row_upper[1])) == 256
            @test signbit(JSimplex.postsolve_primal(result,BigFloat[0])[1])
            @test result.problem.objective_constant === problem.objective_constant && precision(result.problem.objective_constant) == 256
            @test JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1])) == lower_exact && JSimplex._exact_rational(JSimplex.bound_value(problem.row_upper[1])) == upper_exact
        end
    end
end
