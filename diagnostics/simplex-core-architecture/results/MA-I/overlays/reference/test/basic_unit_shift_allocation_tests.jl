using SparseArrays

@testset "Basic presolve reuses signed units for row shifts" begin
function basic_unit_shift_probe(kind; count=128, T=Float64)
    coefficient = T(kind == :positive_coefficient ? 1 : kind == :negative_coefficient ? -1 : 3)
    value = T(kind == :positive_value ? 1 : kind == :negative_value ? -1 : kind == :zero_value ? 0 : 2)
    problem = LinearProblem(sparse(hcat(fill(coefficient,count),fill(T(2),count))),T[2,3];objective_constant=T(7),
        row_lower=fill(T(-100),count),row_upper=fill(T(100),count),
        column_lower=T[value,-10],column_upper=T[value,10])
    return problem,JSimplex._presolve_basic
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive_coefficient,:negative_coefficient,:positive_value,:negative_value,:nonunit,:zero_value), cached in (false,true)
        problem,pass = basic_unit_shift_probe(kind;count=4,T)
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
        @test all(JSimplex.bound_value(result.problem.row_lower[i]) == T(-100)-shift && JSimplex.bound_value(result.problem.row_upper[i]) == T(100)-shift for i in 1:4)
        @test kind != :zero_value || all(result.problem.row_lower[i] === problem.row_lower[i] && result.problem.row_upper[i] === problem.row_upper[i] for i in 1:4)
        @test isequal(JSimplex.postsolve_primal(result,T[1]),T[value,1])
        basis = JSimplex.Basis(collect(2:5),[JSimplex.FREE_NONBASIC;fill(JSimplex.BASIC,4)])
        restored = JSimplex.restore_basis(result,basis)
        @test restored.basic_indices == [3,4,5,6] && restored.states[1] == JSimplex.AT_LOWER
        @test isequal(problem.A.nzval,original.A.nzval) && problem.A.colptr == original.A.colptr && problem.A.rowval == original.A.rowval && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper && problem.objective == original.objective && problem.objective_constant == original.objective_constant && isequal(selections,saved_selections)
    end
    for (kind,limit) in ((:positive_coefficient,10_000),(:negative_coefficient,10_250),(:positive_value,11_300),(:negative_value,11_550),(:nonunit,12_350),(:zero_value,600))
        problem,pass = basic_unit_shift_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Basic unit shifts preserve one-sided and unbounded rows" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), coefficient in (-3,-1,0,1,3), value in (-1,1), endpoint in (:neither,:lower,:upper,:both)
        problem = LinearProblem(sparse(reshape(T[coefficient,2],1,2)),T[0,3];
            row_lower=[endpoint in (:lower,:both) ? T(-100) : nothing],
            row_upper=[endpoint in (:upper,:both) ? T(100) : nothing],
            column_lower=T[value,-10],column_upper=T[value,10])
        result = JSimplex._presolve_basic(problem)
        @test size(result.problem.A) == (1,1)
        for (side,bound) in ((:row_lower,-100),(:row_upper,100))
            old = getfield(problem,side)[1]
            new = getfield(result.problem,side)[1]
            @test isfinite(old) ? JSimplex.bound_value(new) == T(bound-coefficient*value) : new === old
        end
        @test JSimplex.postsolve_primal(result,T[2]) == T[value,2]
    end
end

@testset "Basic unit comparisons preserve near-unit exact residuals" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), operand in (:coefficient,:value), direction in (-1,1), other in (-3,-1,1,3), ambient in (32,64,256)
        problem = setprecision(BigFloat,256) do
            near = T in (Float32,Float64) ? T(direction)*nextfloat(one(T)) : T(direction*(1+(BigInt(1)//(BigInt(1)<<200))))
            coefficient,value = operand == :coefficient ? (near,T(other)) : (T(other),near)
            LinearProblem(sparse(reshape(T[coefficient,2],1,2)),T[0,3];
                row_lower=T[direction*other],row_upper=[nothing],column_lower=T[value,-10],column_upper=T[value,10])
        end
        coefficient = JSimplex._exact_rational(problem.A[1,1])
        value = JSimplex._exact_rational(JSimplex.bound_value(problem.column_lower[1]))
        expected = direction*other-coefficient*value
        @test !iszero(expected)
        setprecision(BigFloat,ambient) do
            result = JSimplex._presolve_basic(problem)
            @test size(result.problem.A) == (1,1)
            @test JSimplex._exact_rational(JSimplex.bound_value(result.problem.row_lower[1])) == expected
            @test JSimplex._exact_rational(JSimplex.postsolve_primal(result,T[0])[1]) == value
            @test JSimplex._exact_rational(problem.A[1,1]) == coefficient && JSimplex._exact_rational(JSimplex.bound_value(problem.column_lower[1])) == value
        end
    end
end

@testset "Basic unit products retain representability rejection" begin
    for operand in (:coefficient,:value), direction in (-1,1), ambient in (32,64), endpoint in (:lower,:upper,:both)
        problem = setprecision(BigFloat,256) do
            high = BigFloat(3)+BigFloat(2)^(-200)
            coefficient,value = operand == :coefficient ? (BigFloat(direction),high) : (high,BigFloat(direction))
            LinearProblem(sparse(reshape(BigFloat[coefficient,2],1,2)),BigFloat[0,3];
                row_lower=[endpoint in (:lower,:both) ? BigFloat(-100) : nothing],
                row_upper=[endpoint in (:upper,:both) ? BigFloat(100) : nothing],
                column_lower=[value,BigFloat(-10)],column_upper=[value,BigFloat(10)])
        end
        setprecision(BigFloat,ambient) do
            result = JSimplex._presolve_basic(problem)
            @test result.problem === problem
            @test isempty(result.postsolve_stack)
        end
    end
end
