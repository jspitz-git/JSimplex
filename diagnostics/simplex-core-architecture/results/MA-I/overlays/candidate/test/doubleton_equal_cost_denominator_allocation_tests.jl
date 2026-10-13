using SparseArrays

@testset "Doubleton equal cost denominator allocation guards" begin
function doubleton_equal_cost_denominator_probe(kind; count=128, T=Float64)
    retained_coefficient = T(kind in (:cancel_integer,:sum_integer) ? 2 : 1)
    retained_cost = kind == :cancel_fraction ? T(3)/2 : kind == :sum_fraction ? T(1)/2 : T(kind == :cancel_integer ? 3 : kind == :sum_integer ? 5 : kind == :zero_retained ? 0 : 1)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(T(2),count),fill(retained_coefficient,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(T(3),count),fill(retained_cost,count));objective_constant=tiny,
        row_lower=fill(T(4),count),row_upper=fill(T(4),count),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end
    for T in (Float32,Float64,BigFloat), kind in (:cancel_integer,:cancel_fraction,:sum_integer,:sum_fraction,:unequal_denominator,:zero_retained)
        problem,pass = doubleton_equal_cost_denominator_probe(kind;count=4,T)
        original = deepcopy(problem)
        result = pass(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test isequal(problem.A,original.A) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:cancel_integer,22700),(:cancel_fraction,23550),(:sum_integer,23150),(:sum_fraction,24020),(:unequal_denominator,25000),(:zero_retained,22000))
        problem,pass = doubleton_equal_cost_denominator_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Equal-denominator cost sums preserve canonical results and restoration" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), beta in (-1,-1//2,1//2,1), cost in (-3,3), mode in (:cancel,:same,:partial,:unequal)
        contribution = T(cost)*T(beta)
        retained = mode == :cancel ? -contribution : mode == :same ? contribution : mode == :partial ? -contribution/T(3) : contribution/T(2)
        problem = LinearProblem(sparse(T[2 -2beta;3 2]),T[cost,retained];objective_constant=T(7),
            row_lower=T[4,-100],row_upper=T[4,100],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        original = deepcopy(problem)
        result = JSimplex.substitute_free_doubleton(problem)
        @test size(result.problem.A) == (1,1)
        @test result.problem.A[1,1] == 2+3beta
        @test result.problem.objective == T[retained+contribution]
        @test !iszero(result.problem.objective[1]) || !signbit(result.problem.objective[1])
        @test result.problem.objective_constant == 7+2cost
        @test JSimplex.bound_value(result.problem.row_lower[1]) == -106 && JSimplex.bound_value(result.problem.row_upper[1]) == 94
        @test JSimplex.postsolve_primal(result,T[2]) == T[2+2beta,2]
        basis = JSimplex.Basis([2],[JSimplex.FREE_NONBASIC,JSimplex.BASIC])
        @test JSimplex.restore_basis(result,basis).basic_indices == [1,4]
        @test isequal(problem.A,original.A) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant)
    end
end

@testset "Equal-denominator cost sums preserve BigFloat precision and cancellation tails" begin
    for mode in (:exact,:cancel,:tail,:nonrepresentable), ambient in (32,64,256), direction in (-1,1)
        problem = setprecision(BigFloat,256) do
            epsilon = BigFloat(2)^(-200)
            cost = BigFloat(3)+(mode == :exact ? zero(BigFloat) : epsilon)
            retained = mode == :exact ? BigFloat(5) : mode == :cancel ? -cost : mode == :tail ? -BigFloat(3)+epsilon : BigFloat(5)+epsilon
            LinearProblem(sparse(BigFloat[2 -2]),direction.*[cost,retained];objective_constant=BigFloat(7),
                row_lower=[zero(BigFloat)],row_upper=[zero(BigFloat)],
                column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
        end
        original_costs = JSimplex._exact_rational.(problem.objective)
        expected = sum(original_costs)
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            if mode == :nonrepresentable && ambient < 256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A) == (0,1)
                @test JSimplex._exact_rational(result.problem.objective[1]) == expected
                @test precision(result.problem.objective[1]) == ambient
                @test !iszero(result.problem.objective[1]) || !signbit(result.problem.objective[1])
            end
            @test JSimplex._exact_rational.(problem.objective) == original_costs
        end
    end
end

@testset "Equal-denominator rational costs reduce large non-dyadic sums" begin
    T = Rational{BigInt}
    for denominator_value in (5,7,15,21), factor in (-1,1,2,4)
        cost = T((BigInt(1)<<300)+1,BigInt(denominator_value))
        retained = factor*cost
        problem = LinearProblem(sparse(T[1 -1]),T[cost,retained];objective_constant=zero(T),
            row_lower=T[1],row_upper=T[1],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        saved_costs = deepcopy(problem.objective)
        result = JSimplex.substitute_free_doubleton(problem)
        expected = retained+cost
        @test size(result.problem.A) == (0,1)
        @test result.problem.objective == T[expected] && denominator(result.problem.objective[1]) == denominator(expected)
        @test gcd(numerator(result.problem.objective[1]),denominator(result.problem.objective[1])) == 1
        @test result.problem.objective_constant == cost
        @test JSimplex.postsolve_primal(result,T[2]) == T[3,2]
        @test problem.objective == saved_costs
    end
end
