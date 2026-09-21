using SparseArrays

@testset "Basic presolve sums objective terms with equal denominators" begin
function basic_equal_denominator_probe(kind; count=128, T=Float64)
    values = T[kind in (:cancel_positive,:cancel_negative) ? (kind == :cancel_negative ? -1 : 1)*(isodd(i) ? 2 : -2) : 2 for i in 1:count]
    cost = T(kind == :zero_contribution ? 0 : kind == :negative_sum ? -3 : 3)
    constant = kind in (:cancel_positive,:cancel_negative) ? zero(T) : kind == :zero_contribution ? -zero(T) : kind == :unequal_denominator ? T(1)/T(2) : T(kind == :negative_sum ? -7 : 7)
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),fill(count+1,count)),vcat(ones(T,count),fill(T(2),count)),count,count+1)
    problem = LinearProblem(A,vcat(fill(cost,count),T[3]);objective_constant=constant,
        row_lower=fill(nothing,count),row_upper=fill(nothing,count),
        column_lower=vcat(values,T[-10]),column_upper=vcat(values,T[10]))
    return problem,JSimplex._presolve_basic
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:cancel_positive,:cancel_negative,:positive_sum,:negative_sum,:unequal_denominator,:zero_contribution), cached in (false,true)
        problem,pass = basic_equal_denominator_probe(kind;count=4,T)
        original = deepcopy(problem)
        selections = [JSimplex._elimination_value(problem,j) for j in 1:5]
        saved_selections = deepcopy(selections)
        result = cached ? pass(problem;selections) : pass(problem)
        values = T[JSimplex.bound_value(problem.column_lower[j]) for j in 1:4]
        @test size(result.problem.A) == (4,1)
        @test Matrix(result.problem.A) == fill(T(2),4,1)
        @test result.problem.objective == T[3]
        @test result.problem.objective_constant == problem.objective_constant+sum(problem.objective[i]*values[i] for i in 1:4)
        @test kind != :zero_contribution || result.problem.objective_constant === problem.objective_constant
        @test all(result.problem.row_lower[i] === problem.row_lower[i] && result.problem.row_upper[i] === problem.row_upper[i] for i in 1:4)
        @test isequal(JSimplex.postsolve_primal(result,T[1]),vcat(values,T[1]))
        basis = JSimplex.Basis(collect(2:5),vcat([JSimplex.FREE_NONBASIC],fill(JSimplex.BASIC,4)))
        restored = JSimplex.restore_basis(result,basis)
        @test restored.basic_indices == collect(6:9)
        @test all(restored.states[j] == JSimplex.AT_LOWER for j in 1:4)
        @test isequal(problem.A.nzval,original.A.nzval) && problem.A.colptr == original.A.colptr && problem.A.rowval == original.A.rowval && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper && isequal(selections,saved_selections)
    end
    for (kind,limit) in ((:cancel_positive,7300),(:cancel_negative,7300),(:positive_sum,8800),(:negative_sum,8800),(:unequal_denominator,9400),(:zero_contribution,1850))
        problem,pass = basic_equal_denominator_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Equal objective denominators reduce fractional sums canonically" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), denominator_value in (1,2,4,8,16), direction in (-1,1), other in (-3,-1,1,3)
        constant = T(direction)/T(denominator_value)
        value = T(other)/T(denominator_value)
        problem = LinearProblem(sparse(reshape(T[1,2],1,2)),T[1,3];objective_constant=constant,
            row_lower=[nothing],row_upper=[nothing],column_lower=T[value,-10],column_upper=T[value,10])
        expected = JSimplex._exact_rational(constant)+JSimplex._exact_rational(value)
        result = JSimplex._presolve_basic(problem)
        @test size(result.problem.A) == (1,1)
        @test JSimplex._exact_rational(result.problem.objective_constant) == expected
        @test denominator(JSimplex._exact_rational(result.problem.objective_constant)) == denominator(expected)
        @test JSimplex.postsolve_primal(result,T[0]) == T[value,0]
        @test problem.objective_constant === constant
    end
end

@testset "Objective reduction changes denominators across eliminations" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        values = T[1//4,-1//4,-1//4]
        A = sparse([1,2,3,1,2,3],[1,2,3,4,4,4],T[1,1,1,2,2,2],3,4)
        problem = LinearProblem(A,T[1,1,1,3];objective_constant=T(1//4),
            row_lower=fill(nothing,3),row_upper=fill(nothing,3),
            column_lower=vcat(values,T[-10]),column_upper=vcat(values,T[10]))
        result = JSimplex._presolve_basic(problem)
        @test size(result.problem.A) == (3,1)
        @test iszero(result.problem.objective_constant) && !signbit(result.problem.objective_constant)
        @test JSimplex.postsolve_primal(result,T[1]) == vcat(values,T[1])
    end
end

@testset "Equal objective denominators preserve high-precision residuals and rejection" begin
    for direction in (-1,1), cancel in (false,true), ambient in (32,64,256)
        problem = setprecision(BigFloat,256) do
            epsilon = BigFloat(2)^(-200)
            constant = direction*(BigFloat(1)+epsilon)
            value = direction*((cancel ? BigFloat(-1) : BigFloat(2))+epsilon)
            LinearProblem(sparse(reshape(BigFloat[1,2],1,2)),BigFloat[1,3];objective_constant=constant,
                row_lower=[nothing],row_upper=[nothing],column_lower=[value,BigFloat(-10)],column_upper=[value,BigFloat(10)])
        end
        old = JSimplex._exact_rational(problem.objective_constant)
        value = JSimplex._exact_rational(JSimplex.bound_value(problem.column_lower[1]))
        @test denominator(old) == denominator(value)
        setprecision(BigFloat,ambient) do
            result = JSimplex._presolve_basic(problem)
            if cancel || ambient == 256
                @test size(result.problem.A) == (1,1)
                @test JSimplex._exact_rational(result.problem.objective_constant) == old+value
                @test !iszero(result.problem.objective_constant)
            else
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            end
            @test JSimplex._exact_rational(problem.objective_constant) == old && JSimplex._exact_rational(JSimplex.bound_value(problem.column_lower[1])) == value
        end
    end
    for T in (Float32,Float64), direction in (-1,1)
        value = direction*floatmax(T)
        problem = LinearProblem(sparse(reshape(T[1,2],1,2)),T[1,3];objective_constant=value,
            row_lower=[nothing],row_upper=[nothing],column_lower=T[value,-10],column_upper=T[value,10])
        result = JSimplex._presolve_basic(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
    end
end
