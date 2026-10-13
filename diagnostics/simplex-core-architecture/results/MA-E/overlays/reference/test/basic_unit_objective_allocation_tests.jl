using SparseArrays

@testset "Basic presolve reuses units for objective contributions" begin
function basic_unit_objective_probe(kind; count=128, T=Float64)
    cost = T(kind == :positive_cost ? 1 : kind == :negative_cost ? -1 : 3)
    value = T(kind == :positive_value ? 1 : kind == :negative_value ? -1 : kind == :zero_value ? 0 : 2)
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),fill(count+1,count)),vcat(ones(T,count),fill(T(2),count)),count,count+1)
    problem = LinearProblem(A,vcat(fill(cost,count),T[3]);objective_constant=T(7),
        row_lower=fill(nothing,count),row_upper=fill(nothing,count),
        column_lower=vcat(fill(value,count),T[-10]),column_upper=vcat(fill(value,count),T[10]))
    return problem,JSimplex._presolve_basic
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive_cost,:negative_cost,:positive_value,:negative_value,:nonunit,:zero_value), cached in (false,true)
        problem,pass = basic_unit_objective_probe(kind;count=4,T)
        original = deepcopy(problem)
        selections = [JSimplex._elimination_value(problem,j) for j in 1:5]
        saved_selections = deepcopy(selections)
        result = cached ? pass(problem;selections) : pass(problem)
        value = JSimplex.bound_value(problem.column_upper[1])
        @test size(result.problem.A) == (4,1)
        @test Matrix(result.problem.A) == fill(T(2),4,1)
        @test result.problem.objective == T[3]
        @test result.problem.objective_constant == T(7)+4problem.objective[1]*value
        @test kind != :zero_value || result.problem.objective_constant === problem.objective_constant
        @test all(result.problem.row_lower[i] === problem.row_lower[i] && result.problem.row_upper[i] === problem.row_upper[i] for i in 1:4)
        x = T[1]
        @test isequal(JSimplex.postsolve_primal(result,x),T[value,value,value,value,1])
        n = size(result.problem.A,2)
        basis = JSimplex.Basis(collect(n+1:n+4),vcat(fill(JSimplex.FREE_NONBASIC,n),fill(JSimplex.BASIC,4)))
        restored = JSimplex.restore_basis(result,basis)
        @test restored.basic_indices == collect(6:9)
        @test all(restored.states[j] == JSimplex.AT_LOWER for j in 1:4)
        @test isequal(problem.A.nzval,original.A.nzval) && problem.A.colptr == original.A.colptr && problem.A.rowval == original.A.rowval && isequal(problem.objective,original.objective) && problem.objective_constant == original.objective_constant && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper && isequal(selections,saved_selections)
    end
    for (kind,limit) in ((:positive_cost,7000),(:negative_cost,7250),(:positive_value,8200),(:negative_value,8450),(:nonunit,9150),(:zero_value,1500))
        problem,pass = basic_unit_objective_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Near-unit objective operands retain exact residuals" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), operand in (:cost,:value), direction in (-1,1), other in (-3,-1,1,3), ambient in (32,64,256)
        problem = setprecision(BigFloat,256) do
            near = T in (Float32,Float64) ? T(direction)*nextfloat(one(T)) : T(direction*(1+(BigInt(1)//(BigInt(1)<<200))))
            cost,value = operand == :cost ? (near,T(other)) : (T(other),near)
            LinearProblem(sparse(reshape(T[1,2],1,2)),T[cost,3];objective_constant=T(-direction*other),
                row_lower=[nothing],row_upper=[nothing],column_lower=T[value,-10],column_upper=T[value,10])
        end
        cost = JSimplex._exact_rational(problem.objective[1])
        value = JSimplex._exact_rational(JSimplex.bound_value(problem.column_lower[1]))
        expected = cost*value-direction*other
        @test !iszero(expected)
        setprecision(BigFloat,ambient) do
            result = JSimplex._presolve_basic(problem)
            @test size(result.problem.A) == (1,1)
            @test JSimplex._exact_rational(result.problem.objective_constant) == expected
            @test JSimplex._exact_rational(JSimplex.postsolve_primal(result,T[0])[1]) == value
            @test JSimplex._exact_rational(problem.objective[1]) == cost && JSimplex._exact_rational(JSimplex.bound_value(problem.column_lower[1])) == value
        end
    end
end

@testset "Unit objective products preserve constant representability checks" begin
    for operand in (:cost,:value), direction in (-1,1), ambient in (32,64,256)
        problem = setprecision(BigFloat,256) do
            high = BigFloat(3)+BigFloat(2)^(-200)
            cost,value = operand == :cost ? (BigFloat(direction),high) : (high,BigFloat(direction))
            LinearProblem(sparse(reshape(BigFloat[1,2],1,2)),[cost,BigFloat(3)];objective_constant=BigFloat(7),
                row_lower=[nothing],row_upper=[nothing],column_lower=[value,BigFloat(-10)],column_upper=[value,BigFloat(10)])
        end
        expected = JSimplex._exact_rational(problem.objective_constant)+JSimplex._exact_rational(problem.objective[1])*JSimplex._exact_rational(JSimplex.bound_value(problem.column_lower[1]))
        setprecision(BigFloat,ambient) do
            result = JSimplex._presolve_basic(problem)
            if ambient < 256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A) == (1,1)
                @test JSimplex._exact_rational(result.problem.objective_constant) == expected
            end
        end
    end
end

@testset "Unit objective products still check finite row shifts" begin
    for T in (Float32,Float64), cost in (-1,1), direction in (-1,1), side in (:lower,:upper,:both)
        tiny = direction*nextfloat(zero(T))
        problem = LinearProblem(sparse(reshape(T[0.5,2],1,2)),T[cost,3];
            row_lower=[side in (:lower,:both) ? zero(T) : nothing],
            row_upper=[side in (:upper,:both) ? zero(T) : nothing],
            column_lower=T[tiny,-10],column_upper=T[tiny,10])
        result = JSimplex._presolve_basic(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
    end
end
