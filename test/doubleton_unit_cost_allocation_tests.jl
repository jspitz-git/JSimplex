using SparseArrays

@testset "Doubleton signed-unit costs allocation guards" begin
function doubleton_unit_cost_probe(kind; count=128, T=Float64)
    pivot = T(kind == :inexact_beta ? 3 : 2)
    rhs = kind in (:zero_positive,:zero_negative) ? zero(T) : T(4)
    cost = T(kind in (:negative,:zero_negative) ? -1 : kind == :nonunit_cost ? 3 : 1)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(pivot,count),ones(T,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(cost,count),fill(tiny,count));objective_constant=T(7),
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end
    for T in (Float32,Float64,BigFloat), kind in (:positive,:negative,:zero_positive,:zero_negative,:nonunit_cost,:inexact_beta)
        problem,pass = doubleton_unit_cost_probe(kind;count=4,T)
        original = deepcopy(problem)
        result = pass(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test isequal(problem.A,original.A) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:positive,22000),(:negative,22500),(:zero_positive,18300),(:zero_negative,18550),(:nonunit_cost,25000),(:inexact_beta,11500))
        problem,pass = doubleton_unit_cost_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Signed-unit doubleton costs preserve objective and restoration" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (-2,2), retained in (-1,1), cost in (-1,1), rhs in (T(-4),-zero(T),T(4))
        problem = LinearProblem(sparse(T[pivot retained;3 2]),T[cost,3];objective_constant=T(7),
            row_lower=T[rhs,-100],row_upper=T[rhs,100],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        original = deepcopy(problem)
        alpha,beta = rhs/T(pivot),-T(retained)/T(pivot)
        result = JSimplex.substitute_free_doubleton(problem)
        @test size(result.problem.A) == (1,1)
        @test result.problem.A[1,1] == 2+3beta
        @test result.problem.objective == T[3+cost*beta]
        @test result.problem.objective_constant == 7+cost*alpha
        @test JSimplex.bound_value(result.problem.row_lower[1]) == -100-3alpha && JSimplex.bound_value(result.problem.row_upper[1]) == 100-3alpha
        @test JSimplex.postsolve_primal(result,T[2]) == T[alpha+2beta,2]
        basis = JSimplex.Basis([2],[JSimplex.FREE_NONBASIC,JSimplex.BASIC])
        @test JSimplex.restore_basis(result,basis).basic_indices == [1,4]
        @test isequal(problem.A,original.A) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant)
    end
end

@testset "Signed-unit cost contributions preserve canonical objective zeros" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), cost in (-1,1), rhs in (zero(T),-zero(T),T(4))
        alpha = rhs/T(2)
        constant = iszero(rhs) ? -zero(T) : -T(cost)*alpha
        problem = LinearProblem(sparse(T[2 1]),T[cost,T(cost)/2];objective_constant=constant,
            row_lower=T[rhs],row_upper=T[rhs],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        result = JSimplex.substitute_free_doubleton(problem)
        @test size(result.problem.A) == (0,1)
        @test iszero(result.problem.objective[1]) && !signbit(result.problem.objective[1])
        @test iszero(result.problem.objective_constant) && !signbit(result.problem.objective_constant)
    end
end

@testset "Signed-unit costs retain BigFloat objective precision gates" begin
    for mode in (:exact,:cost,:constant), ambient in (32,64,256), cost in (-1,1), rhs in (0,4)
        problem = setprecision(BigFloat,256) do
            epsilon = BigFloat(2)^(-200)
            constant = BigFloat(7)+(mode == :constant ? epsilon : zero(BigFloat))
            retained_cost = BigFloat(3)+(mode == :cost ? epsilon : zero(BigFloat))
            LinearProblem(sparse(BigFloat[2 1]),BigFloat[cost,retained_cost];objective_constant=constant,
                row_lower=BigFloat[rhs],row_upper=BigFloat[rhs],
                column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
        end
        original_constant = JSimplex._exact_rational(problem.objective_constant)
        original_cost = JSimplex._exact_rational(problem.objective[2])
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            if mode != :exact && ambient < 256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A) == (0,1)
                @test JSimplex._exact_rational(result.problem.objective[1]) == original_cost-cost//2
                @test JSimplex._exact_rational(result.problem.objective_constant) == original_constant+cost*rhs//2
                @test precision(result.problem.objective_constant) == ambient && precision(result.problem.objective[1]) == ambient
            end
            @test JSimplex._exact_rational(problem.objective_constant) == original_constant && JSimplex._exact_rational(problem.objective[2]) == original_cost
        end
    end
end

@testset "Costs neighboring signed units retain exact contributions" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), direction in (-1,1), side in (-1,1)
        problem = setprecision(BigFloat,256) do
            delta = T == Float32 ? T(2)^(-20) : T == Float64 ? T(2)^(-48) : T(BigInt(1)//(BigInt(1)<<200))
            cost = T(direction)*(one(T)+side*delta)
            LinearProblem(sparse(T[2 1]),T[cost,3];objective_constant=T(7),
                row_lower=T[4],row_upper=T[4],
                column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        end
        exact_cost = JSimplex._exact_rational(problem.objective[1])
        result = JSimplex.substitute_free_doubleton(problem)
        @test size(result.problem.A) == (0,1)
        @test JSimplex._exact_rational(result.problem.objective[1]) == 3-exact_cost/2
        @test JSimplex._exact_rational(result.problem.objective_constant) == 7+2exact_cost
    end
end
