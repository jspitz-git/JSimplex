using SparseArrays

@testset "Basic presolve reuses contributions at zero constant" begin
function basic_zero_constant_probe(kind; count=128, T=Float64)
    direction = kind == :negative ? -1 : 1
    values = T[direction*(isodd(i) ? 2 : -2) for i in 1:count]
    cost = kind == :zero_contribution ? zero(T) : T(3)
    constant = kind == :nonzero_constant ? T(7) : kind in (:negative_zero,:zero_contribution) ? -zero(T) : zero(T)
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),fill(count+1,count)),vcat(ones(T,count),fill(T(2),count)),count,count+1)
    problem = LinearProblem(A,vcat(fill(cost,count),T[3]);objective_constant=constant,
        row_lower=fill(kind == :finite_rows ? T(-100) : nothing,count),
        row_upper=fill(kind == :finite_rows ? T(100) : nothing,count),
        column_lower=vcat(values,T[-10]),column_upper=vcat(values,T[10]))
    return problem,JSimplex._presolve_basic
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative,:negative_zero,:finite_rows,:nonzero_constant,:zero_contribution), cached in (false,true)
        problem,pass = basic_zero_constant_probe(kind;count=4,T)
        original = deepcopy(problem)
        selections = [JSimplex._elimination_value(problem,j) for j in 1:5]
        saved_selections = deepcopy(selections)
        result = cached ? pass(problem;selections) : pass(problem)
        values = T[JSimplex.bound_value(problem.column_lower[j]) for j in 1:4]
        @test size(result.problem.A) == (4,1)
        @test Matrix(result.problem.A) == fill(T(2),4,1)
        @test result.problem.objective == T[3]
        @test result.problem.objective_constant == problem.objective_constant
        @test kind != :zero_contribution || result.problem.objective_constant === problem.objective_constant
        @test all(kind == :finite_rows ? JSimplex.bound_value(result.problem.row_lower[i]) == T(-100)-values[i] && JSimplex.bound_value(result.problem.row_upper[i]) == T(100)-values[i] : result.problem.row_lower[i] === problem.row_lower[i] && result.problem.row_upper[i] === problem.row_upper[i] for i in 1:4)
        @test isequal(JSimplex.postsolve_primal(result,T[1]),vcat(values,T[1]))
        basis = JSimplex.Basis(collect(2:5),vcat([JSimplex.FREE_NONBASIC],fill(JSimplex.BASIC,4)))
        restored = JSimplex.restore_basis(result,basis)
        @test restored.basic_indices == collect(6:9)
        @test all(restored.states[j] == JSimplex.AT_LOWER for j in 1:4)
        @test isequal(problem.A.nzval,original.A.nzval) && problem.A.colptr == original.A.colptr && problem.A.rowval == original.A.rowval && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper && isequal(selections,saved_selections)
    end
    for (kind,limit) in ((:positive,8000),(:negative,8000),(:negative_zero,8000),(:finite_rows,17250),(:nonzero_constant,9150),(:zero_contribution,1850))
        problem,pass = basic_zero_constant_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Tiny nonzero constants still participate in exact cancellation" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), direction in (-1,1), ambient in (32,64,256)
        problem = setprecision(BigFloat,256) do
            tiny = T in (Float32,Float64) ? direction*nextfloat(zero(T)) : T(direction*(BigInt(1)//(BigInt(1)<<200)))
            LinearProblem(sparse(reshape(T[1,2],1,2)),T[1,3];objective_constant=tiny,
                row_lower=[nothing],row_upper=[nothing],column_lower=T[-tiny,-10],column_upper=T[-tiny,10])
        end
        expected = JSimplex._exact_rational(problem.objective_constant)
        setprecision(BigFloat,ambient) do
            result = JSimplex._presolve_basic(problem)
            @test size(result.problem.A) == (1,1)
            @test iszero(result.problem.objective_constant)
            @test !signbit(result.problem.objective_constant)
            @test JSimplex._exact_rational(problem.objective_constant) == expected
        end
    end
end

@testset "Tiny nonzero constants cannot be rounded away" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), direction in (-1,1), ambient in (32,64,256)
        problem = setprecision(BigFloat,256) do
            tiny = T in (Float32,Float64) ? direction*nextfloat(zero(T)) : T(direction*(BigInt(1)//(BigInt(1)<<200)))
            LinearProblem(sparse(reshape(T[1,2],1,2)),T[1,3];objective_constant=tiny,
                row_lower=[nothing],row_upper=[nothing],column_lower=T[1,-10],column_upper=T[1,10])
        end
        expected = JSimplex._exact_rational(problem.objective_constant)+1
        setprecision(BigFloat,ambient) do
            result = JSimplex._presolve_basic(problem)
            if T == Rational{BigInt} || (T == BigFloat && ambient == 256)
                @test size(result.problem.A) == (1,1)
                @test JSimplex._exact_rational(result.problem.objective_constant) == expected
            else
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            end
        end
    end
end

@testset "Zero constants retain contribution representability checks" begin
    for direction in (-1,1), ambient in (32,64,256)
        problem = setprecision(BigFloat,256) do
            value = direction*(BigFloat(3)+BigFloat(2)^(-200))
            LinearProblem(sparse(reshape(BigFloat[1,2],1,2)),BigFloat[1,3];objective_constant=-zero(BigFloat),
                row_lower=[nothing],row_upper=[nothing],column_lower=[value,BigFloat(-10)],column_upper=[value,BigFloat(10)])
        end
        expected = JSimplex._exact_rational(JSimplex.bound_value(problem.column_lower[1]))
        setprecision(BigFloat,ambient) do
            result = JSimplex._presolve_basic(problem)
            if ambient < 256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A) == (1,1)
                @test JSimplex._exact_rational(result.problem.objective_constant) == expected
            end
            @test iszero(problem.objective_constant) && signbit(problem.objective_constant) && precision(problem.objective_constant) == 256
        end
    end
    for T in (Float32,Float64), direction in (-1,1)
        value = direction*floatmax(T)
        problem = LinearProblem(sparse(reshape(T[1,2],1,2)),T[2,3];
            row_lower=[nothing],row_upper=[nothing],column_lower=T[value,-10],column_upper=T[value,10])
        result = JSimplex._presolve_basic(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
    end
    for T in (Float32,Float64), direction in (-1,1), side in (:lower,:upper,:both)
        tiny = direction*nextfloat(zero(T))
        problem = LinearProblem(sparse(reshape(T[0.5,2],1,2)),T[2,3];objective_constant=-zero(T),
            row_lower=[side in (:lower,:both) ? zero(T) : nothing],row_upper=[side in (:upper,:both) ? zero(T) : nothing],
            column_lower=T[tiny,-10],column_upper=T[tiny,10])
        result = JSimplex._presolve_basic(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
    end
end
