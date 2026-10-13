using SparseArrays

@testset "Doubleton signed-unit objective ratios allocation guards" begin
function doubleton_unit_objective_ratio_probe(kind; count=128, T=Float64)
    pivot = T(kind == :inexact_beta ? 3 : 2)
    retained = T(kind == :beta_positive ? -2 : kind == :beta_negative ? 2 : 1)
    rhs = T(kind == :alpha_positive ? 2 : kind == :alpha_negative ? -2 : 4)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(pivot,count),fill(retained,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(T(3),count),fill(tiny,count));objective_constant=T(7),
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end
    for T in (Float32,Float64,BigFloat), kind in (:beta_positive,:beta_negative,:alpha_positive,:alpha_negative,:nonunit_ratios,:inexact_beta)
        problem,pass = doubleton_unit_objective_ratio_probe(kind;count=4,T)
        original = deepcopy(problem)
        result = pass(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test isequal(problem.A,original.A) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:beta_positive,23500),(:beta_negative,23750),(:alpha_positive,23500),(:alpha_negative,23750),(:nonunit_ratios,25000),(:inexact_beta,11500))
        problem,pass = doubleton_unit_objective_ratio_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Unit objective ratios preserve transforms and restoration" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), alpha in (-1,0,1,2), beta in (-1,-1//2,1//2,1), cost in (-3,3)
        problem = LinearProblem(sparse(T[2 -2beta;3 2]),T[cost,3];objective_constant=T(7),
            row_lower=T[2alpha,-100],row_upper=T[2alpha,100],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        original = deepcopy(problem)
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

@testset "Unit objective ratio cancellation preserves canonical zeros" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), cost in (-3,3), alpha in (-1,1), beta in (-1,1)
        problem = LinearProblem(sparse(T[2 -2beta]),T[cost,-cost*beta];objective_constant=T(-cost*alpha),
            row_lower=T[2alpha],row_upper=T[2alpha],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        result = JSimplex.substitute_free_doubleton(problem)
        @test size(result.problem.A) == (0,1)
        @test iszero(result.problem.objective[1]) && !signbit(result.problem.objective[1])
        @test iszero(result.problem.objective_constant) && !signbit(result.problem.objective_constant)
    end
end

@testset "Unit objective ratios retain BigFloat precision gates" begin
    for mode in (:exact,:cost,:constant,:eliminated), ambient in (32,64,256), alpha in (-1,1), beta in (-1,1)
        problem = setprecision(BigFloat,256) do
            epsilon = BigFloat(2)^(-200)
            constant = BigFloat(7)+(mode == :constant ? epsilon : zero(BigFloat))
            retained_cost = BigFloat(5)+(mode == :cost ? epsilon : zero(BigFloat))
            cost = BigFloat(3)+(mode == :eliminated ? epsilon : zero(BigFloat))
            LinearProblem(sparse(BigFloat[2 -2beta]),[cost,retained_cost];objective_constant=constant,
                row_lower=BigFloat[2alpha],row_upper=BigFloat[2alpha],
                column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
        end
        original_constant = JSimplex._exact_rational(problem.objective_constant)
        original_costs = JSimplex._exact_rational.(problem.objective)
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            if mode != :exact && ambient < 256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A) == (0,1)
                @test JSimplex._exact_rational(result.problem.objective[1]) == original_costs[2]+beta*original_costs[1]
                @test JSimplex._exact_rational(result.problem.objective_constant) == original_constant+alpha*original_costs[1]
                @test precision(result.problem.objective_constant) == ambient && precision(result.problem.objective[1]) == ambient
            end
            @test JSimplex._exact_rational(problem.objective_constant) == original_constant && JSimplex._exact_rational.(problem.objective) == original_costs
        end
    end
end

@testset "Ratios neighboring signed units retain exact contributions" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), which in (:alpha,:beta), direction in (-1,1), side in (-1,1)
        problem = setprecision(BigFloat,256) do
            delta = T == Float32 ? T(2)^(-18) : T == Float64 ? T(2)^(-46) : T(BigInt(1)//(BigInt(1)<<200))
            ratio = T(direction)*(one(T)+side*delta)
            alpha = which == :alpha ? ratio : T(2)
            beta = which == :beta ? ratio : -T(1)/2
            LinearProblem(sparse(T[2 -2beta]),T[3,3];objective_constant=T(7),
                row_lower=T[2alpha],row_upper=T[2alpha],
                column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        end
        exact_alpha = JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1]))/2
        exact_beta = -JSimplex._exact_rational(problem.A[1,2])/2
        result = JSimplex.substitute_free_doubleton(problem)
        @test size(result.problem.A) == (0,1)
        @test JSimplex._exact_rational(result.problem.objective[1]) == 3+3exact_beta
        @test JSimplex._exact_rational(result.problem.objective_constant) == 7+3exact_alpha
    end
end
