using SparseArrays

@testset "Doubleton objective updates skip zero eliminated costs" begin
function doubleton_zero_cost_probe(kind; count=128, T=Float64)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    pivot = T(kind == :inexact_ratio ? 3 : 2)
    cost = kind == :negative_zero ? -zero(T) : T(kind == :nonzero_cost ? 2 : 0)
    rhs = kind == :bound_rejection ? 2tiny : T(kind == :zero_rhs ? 0 : kind == :negative_zero ? -4 : 4)
    affected = kind == :bound_rejection ? T(1)/T(2) : tiny
    rows = vcat(collect(1:count),collect(count+1:2count),collect(1:count),collect(count+1:2count))
    columns = vcat(collect(1:count),collect(1:count),collect(count+1:2count),collect(count+1:2count))
    A = sparse(rows,columns,vcat(fill(pivot,count),fill(affected,count),ones(T,2count)),2count,2count)
    problem = LinearProblem(A,vcat(fill(cost,count),fill(T(3),count));objective_constant=T(7),
        row_lower=vcat(fill(T(rhs),count),fill(kind == :bound_rejection ? zero(T) : nothing,count)),
        row_upper=vcat(fill(T(rhs),count),fill(nothing,count)),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end

    for T in (Float32,Float64), kind in (:positive,:negative_zero,:zero_rhs,:bound_rejection,:nonzero_cost,:inexact_ratio)
        problem,pass = doubleton_zero_cost_probe(kind;count=4,T)
        original = deepcopy(problem)
        result = pass(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test problem.A.nzval == original.A.nzval && problem.objective == original.objective && problem.objective_constant == original.objective_constant && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
    for (kind,limit) in ((:positive,29000),(:negative_zero,29000),(:zero_rhs,27000),(:bound_rejection,32000),(:nonzero_cost,33750),(:inexact_ratio,11300))
        problem,pass = doubleton_zero_cost_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Zero doubleton costs preserve accepted substitutions" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), negative_zero in (false,true), pivot in (-2,2), rhs in (-4,0,4)
        cost = negative_zero ? -zero(T) : zero(T)
        problem = LinearProblem(sparse(T[pivot 1;3 2]),T[cost,3];objective_constant=T(7),
            row_lower=T[rhs,-100],row_upper=T[rhs,100],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        original = deepcopy(problem)
        result = JSimplex.substitute_free_doubleton(problem)
        alpha,beta = T(rhs)/T(pivot),-one(T)/T(pivot)
        @test size(result.problem.A) == (1,1)
        @test result.problem.A[1,1] == T(2)+3beta
        @test result.problem.objective == T[3] && result.problem.objective_constant == T(7)
        @test JSimplex.bound_value(result.problem.row_lower[1]) == T(-100)-3alpha && JSimplex.bound_value(result.problem.row_upper[1]) == T(100)-3alpha
        @test JSimplex.postsolve_primal(result,T[2]) == T[alpha+2beta,2]
        basis = JSimplex.Basis([2],[JSimplex.FREE_NONBASIC,JSimplex.BASIC])
        @test JSimplex.restore_basis(result,basis).basic_indices == [1,4]
        @test isequal(problem.objective,original.objective)
        @test problem.A.nzval == original.A.nzval && problem.objective_constant == original.objective_constant && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
end

@testset "Zero doubleton costs keep output-zero canonicalization" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), negative_cost in (false,true), negative_constant in (false,true)
        cost = negative_cost ? -zero(T) : zero(T)
        constant = negative_constant ? -zero(T) : zero(T)
        problem = LinearProblem(sparse(reshape(T[2,1],1,2)),T[-zero(T),cost];objective_constant=constant,
            row_lower=T[4],row_upper=T[4],column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        result = JSimplex.substitute_free_doubleton(problem)
        @test size(result.problem.A) == (0,1)
        @test iszero(result.problem.objective[1]) && !signbit(result.problem.objective[1])
        @test iszero(result.problem.objective_constant) && !signbit(result.problem.objective_constant)
        @test isequal(problem.objective[2],cost) && isequal(problem.objective_constant,constant)
    end
end

@testset "Zero doubleton costs keep objective representability and precision" begin
    for negative_zero in (false,true), mode in (:simple,:cost,:constant,:both), ambient in (32,64,256)
        problem = setprecision(BigFloat,256) do
            high = BigFloat(3)+BigFloat(2)^(-200)
            cost = negative_zero ? -zero(BigFloat) : zero(BigFloat)
            retained = mode in (:cost,:both) ? high : BigFloat(3)
            constant = mode in (:constant,:both) ? high : BigFloat(7)
            LinearProblem(sparse(reshape(BigFloat[2,1],1,2)),[cost,retained];objective_constant=constant,
                row_lower=BigFloat[4],row_upper=BigFloat[4],column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
        end
        retained = JSimplex._exact_rational(problem.objective[2])
        constant = JSimplex._exact_rational(problem.objective_constant)
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            if mode != :simple && ambient < 256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A) == (0,1)
                @test JSimplex._exact_rational(result.problem.objective[1]) == retained && JSimplex._exact_rational(result.problem.objective_constant) == constant
                @test precision(result.problem.objective[1]) == ambient && precision(result.problem.objective_constant) == ambient
            end
            @test JSimplex._exact_rational(problem.objective[2]) == retained && JSimplex._exact_rational(problem.objective_constant) == constant
            @test precision(problem.objective[2]) == 256 && precision(problem.objective_constant) == 256
        end
    end
end

@testset "Tiny nonzero doubleton costs retain exact contributions" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), direction in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            cost = T in (Float32,Float64) ? direction*2nextfloat(zero(T)) : T(direction*(BigInt(1)//(BigInt(1)<<200)))
            LinearProblem(sparse(reshape(T[2,1],1,2)),T[cost,0];row_lower=T[4],row_upper=T[4],
                column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        end
        cost = JSimplex._exact_rational(problem.objective[1])
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            @test size(result.problem.A) == (0,1)
            @test JSimplex._exact_rational(result.problem.objective[1]) == -cost/2 && !iszero(result.problem.objective[1])
            @test JSimplex._exact_rational(result.problem.objective_constant) == 2cost && !iszero(result.problem.objective_constant)
            @test JSimplex._exact_rational(problem.objective[1]) == cost
        end
    end
    for T in (Float32,Float64), direction in (-1,1)
        cost = direction*nextfloat(zero(T))
        problem = LinearProblem(sparse(reshape(T[2,1],1,2)),T[cost,0];row_lower=T[4],row_upper=T[4],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        result = JSimplex.substitute_free_doubleton(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
    end
end

@testset "Rejected doubletons switch between zero and nonzero costs" begin
    for T in (Float32,Float64), zero_first in (false,true)
        tiny = nextfloat(zero(T))
        first_cost,second_cost = zero_first ? (zero(T),T(2)) : (T(2),zero(T))
        problem = LinearProblem(sparse(T[2 0 1 0;0 2 0 1;tiny 0 1 0]),T[first_cost,second_cost,3,3];objective_constant=T(7),
            row_lower=Union{Nothing,T}[T(4),T(6),nothing],row_upper=Union{Nothing,T}[T(4),T(6),nothing],
            column_lower=Union{Nothing,T}[nothing,nothing,T(-10),T(-10)],column_upper=Union{Nothing,T}[nothing,nothing,T(10),T(10)])
        result = JSimplex.substitute_free_doubleton(problem)
        @test size(result.problem.A) == (2,3)
        @test result.problem.objective == T[first_cost,3,3-second_cost/2]
        @test result.problem.objective_constant == T(7)+3second_cost
        @test JSimplex.postsolve_primal(result,T[1,2,2]) == T[1,2,2,2]
    end
end
