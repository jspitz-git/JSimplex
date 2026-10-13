using SparseArrays

@testset "Basic presolve skips zero objective contributions" begin
function basic_zero_objective_probe(kind; count=128, T=Float64)
    cost = T(kind in (:zero_cost,:negative_zero_cost) ? 0 : kind == :negative_zero_value ? -3 : 3)
    kind == :negative_zero_cost && (cost = -zero(T))
    value = kind == :negative_zero_value ? -zero(T) : T(kind == :zero_value ? 0 : kind == :negative_zero_cost ? -2 : 2)
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),fill(count+1,count)),vcat(ones(T,count),fill(T(2),count)),count,count+1)
    problem = LinearProblem(A,vcat(fill(cost,count),T[3]);objective_constant=T(7),
        row_lower=fill(nothing,count),row_upper=fill(nothing,count),
        column_lower=vcat(fill(kind == :no_elimination ? T(-2) : value,count),T[-10]),
        column_upper=vcat(fill(value,count),T[10]))
    return problem,JSimplex._presolve_basic
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:zero_cost,:negative_zero_cost,:zero_value,:negative_zero_value,:nonzero,:no_elimination), cached in (false,true)
        problem,pass = basic_zero_objective_probe(kind;count=4,T)
        original = deepcopy(problem)
        selections = [JSimplex._elimination_value(problem,j) for j in 1:5]
        saved_selections = deepcopy(selections)
        result = cached ? pass(problem;selections) : pass(problem)
        value = JSimplex.bound_value(problem.column_upper[1])
        eliminated = kind != :no_elimination
        @test size(result.problem.A) == (4,eliminated ? 1 : 5)
        @test eliminated ? Matrix(result.problem.A) == fill(T(2),4,1) : result.problem === problem
        @test result.problem.objective == (eliminated ? T[3] : problem.objective)
        @test result.problem.objective_constant == T(7)+(eliminated ? 4problem.objective[1]*value : zero(T))
        @test kind == :nonzero || result.problem.objective_constant === problem.objective_constant
        @test all(result.problem.row_lower[i] === problem.row_lower[i] && result.problem.row_upper[i] === problem.row_upper[i] for i in 1:4)
        x = eliminated ? T[1] : T[value,value,value,value,1]
        @test isequal(JSimplex.postsolve_primal(result,x),T[value,value,value,value,1])
        n = size(result.problem.A,2)
        basis = JSimplex.Basis(collect(n+1:n+4),vcat(fill(JSimplex.FREE_NONBASIC,n),fill(JSimplex.BASIC,4)))
        restored = JSimplex.restore_basis(result,basis)
        @test restored.basic_indices == collect(6:9)
        @test !eliminated || all(restored.states[j] == JSimplex.AT_LOWER for j in 1:4)
        @test isequal(problem.A.nzval,original.A.nzval) && problem.A.colptr == original.A.colptr && problem.A.rowval == original.A.rowval && isequal(problem.objective,original.objective) && problem.objective_constant == original.objective_constant && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper && isequal(selections,saved_selections)
    end
    for (kind,limit) in ((:zero_cost,3000),(:negative_zero_cost,3000),(:zero_value,3000),(:negative_zero_value,3000),(:nonzero,9150),(:no_elimination,150))
        problem,pass = basic_zero_objective_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Zero objective contributions retain stored BigFloat values" begin
    for operand in (:cost,:value), negative in (false,true), ambient in (32,64,256)
        problem = setprecision(BigFloat,256) do
            z = negative ? -zero(BigFloat) : zero(BigFloat)
            high = BigFloat(1)/3
            cost,value = operand == :cost ? (z,high) : (high,z)
            LinearProblem(sparse(reshape(BigFloat[1,2],1,2)),[cost,BigFloat(3)];objective_constant=high,
                row_lower=[nothing],row_upper=[nothing],column_lower=[value,BigFloat(-10)],column_upper=[value,BigFloat(10)])
        end
        original_cost = JSimplex._exact_rational(problem.objective[1])
        original_value = JSimplex._exact_rational(JSimplex.bound_value(problem.column_lower[1]))
        setprecision(BigFloat,ambient) do
            result = JSimplex._presolve_basic(problem)
            @test size(result.problem.A) == (1,1)
            @test result.problem.objective_constant === problem.objective_constant
            @test precision(result.problem.objective_constant) == 256
            restored = JSimplex.postsolve_primal(result,BigFloat[1])[1]
            @test JSimplex._exact_rational(restored) == original_value
            @test signbit(restored) == signbit(JSimplex.bound_value(problem.column_lower[1]))
            @test JSimplex._exact_rational(problem.objective[1]) == original_cost
        end
    end
end

@testset "Tiny nonzero objective contributions stay nonzero" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), operand in (:cost,:value), direction in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            tiny = T in (Float32,Float64) ? direction*nextfloat(zero(T)) : T(direction*(BigInt(1)//(BigInt(1)<<200)))
            cost,value = operand == :cost ? (tiny,T(2)) : (T(2),tiny)
            LinearProblem(sparse(reshape(T[1,2],1,2)),T[cost,3];
                row_lower=[nothing],row_upper=[nothing],column_lower=T[value,-10],column_upper=T[value,10])
        end
        expected = JSimplex._exact_rational(problem.objective[1])*JSimplex._exact_rational(JSimplex.bound_value(problem.column_lower[1]))
        setprecision(BigFloat,ambient) do
            result = JSimplex._presolve_basic(problem)
            @test size(result.problem.A) == (1,1)
            @test JSimplex._exact_rational(result.problem.objective_constant) == expected
            @test !iszero(result.problem.objective_constant)
        end
    end
end

@testset "Zero-contribution shortcut preserves rejection and row checks" begin
    for T in (Float32,Float64), operand in (:cost,:value), direction in (-1,1)
        tiny = direction*nextfloat(zero(T))
        cost,value = operand == :cost ? (tiny,T(0.5)) : (T(0.5),tiny)
        problem = LinearProblem(sparse(reshape(T[1,2],1,2)),T[cost,3];
            row_lower=[nothing],row_upper=[nothing],column_lower=T[value,-10],column_upper=T[value,10])
        result = JSimplex._presolve_basic(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        # Even zero objective cost must not bypass a nonrepresentable row shift.
        problem = LinearProblem(sparse(reshape(T[0.5,2],1,2)),T[0,3];
            row_lower=T[0],row_upper=[nothing],column_lower=T[tiny,-10],column_upper=T[tiny,10])
        result = JSimplex._presolve_basic(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
    end
end
