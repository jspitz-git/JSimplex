using SparseArrays

@testset "Doubleton zero objective constant allocation guards" begin
function doubleton_zero_constant_probe(kind; count=128, T=Float64)
    cost = T(kind == :negative ? -3 : kind == :unit_positive ? 1 : kind == :unit_negative ? -1 : 3)
    constant = kind in (:negative,:unit_negative,:zero_alpha) ? -zero(T) : T(kind == :nonzero_constant ? 7 : 0)
    rhs = T(kind == :zero_alpha ? 0 : 4)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(T(2),count),ones(T,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(cost,count),fill(tiny,count));objective_constant=constant,
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end
    for T in (Float32,Float64,BigFloat), kind in (:positive,:negative,:unit_positive,:unit_negative,:nonzero_constant,:zero_alpha)
        problem,pass = doubleton_zero_constant_probe(kind;count=4,T)
        original = deepcopy(problem)
        result = pass(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test isequal(problem.A,original.A) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:positive,23000),(:negative,23000),(:unit_positive,19000),(:unit_negative,19500),(:nonzero_constant,25000),(:zero_alpha,20500))
        problem,pass = doubleton_zero_constant_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Zero objective constants preserve transforms and restoration" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), alpha in (-2,-1,0,1,2), cost in (-3,-1,0,1,3), constant in (zero(T),-zero(T))
        rhs = iszero(alpha) && signbit(constant) ? -zero(T) : T(2alpha)
        problem = LinearProblem(sparse(T[2 1;3 2]),T[cost,3];objective_constant=constant,
            row_lower=T[rhs,-100],row_upper=T[rhs,100],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        original = deepcopy(problem)
        result = JSimplex.substitute_free_doubleton(problem)
        @test size(result.problem.A) == (1,1)
        @test result.problem.A[1,1] == T(1)/2
        @test result.problem.objective == T[3-cost/2]
        @test result.problem.objective_constant == cost*alpha
        @test !iszero(result.problem.objective_constant) || !signbit(result.problem.objective_constant)
        @test JSimplex.bound_value(result.problem.row_lower[1]) == -100-3alpha && JSimplex.bound_value(result.problem.row_upper[1]) == 100-3alpha
        @test JSimplex.postsolve_primal(result,T[2]) == T[alpha-1,2]
        basis = JSimplex.Basis([2],[JSimplex.FREE_NONBASIC,JSimplex.BASIC])
        @test JSimplex.restore_basis(result,basis).basic_indices == [1,4]
        @test isequal(problem.A,original.A) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant)
    end
end

@testset "Zero objective constants keep BigFloat precision gates" begin
    for mode in (:exact,:cost,:constant), ambient in (32,64,256), alpha in (-2,-1,1,2), negative_zero in (false,true)
        problem = setprecision(BigFloat,256) do
            epsilon = BigFloat(2)^(-200)
            cost = BigFloat(3)+(mode == :constant ? epsilon : zero(BigFloat))
            retained_cost = mode == :cost ? BigFloat(5)+epsilon : cost/2
            LinearProblem(sparse(BigFloat[2 1]),[cost,retained_cost];objective_constant=negative_zero ? -zero(BigFloat) : zero(BigFloat),
                row_lower=BigFloat[2alpha],row_upper=BigFloat[2alpha],
                column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
        end
        original_costs = JSimplex._exact_rational.(problem.objective)
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            if mode != :exact && ambient < 256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A) == (0,1)
                @test JSimplex._exact_rational(result.problem.objective[1]) == original_costs[2]-original_costs[1]/2
                @test JSimplex._exact_rational(result.problem.objective_constant) == alpha*original_costs[1]
                @test precision(result.problem.objective_constant) == ambient && precision(result.problem.objective[1]) == ambient
            end
            @test JSimplex._exact_rational.(problem.objective) == original_costs && signbit(problem.objective_constant) == negative_zero && precision(problem.objective_constant) == 256
        end
    end
end

@testset "Tiny constants and tiny constant updates retain exact gates" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), direction in (-1,1)
        tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
        problem = LinearProblem(sparse(T[2 1]),T[3,3];objective_constant=direction*tiny,
            row_lower=T[4],row_upper=T[4],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        result = JSimplex.substitute_free_doubleton(problem)
        if T == Rational{BigInt}
            @test size(result.problem.A) == (0,1)
            @test result.problem.objective_constant == direction*tiny+6
        else
            @test result.problem === problem
            @test isempty(result.postsolve_stack)
        end
        for cost in (1//2,2)
            small = LinearProblem(sparse(T[2 1]),T[cost,3];objective_constant=zero(T),
                row_lower=T[direction*2tiny],row_upper=T[direction*2tiny],
                column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
            reduced = JSimplex.substitute_free_doubleton(small)
            if T in (Float32,Float64) && cost == 1//2
                @test reduced.problem === small
                @test isempty(reduced.postsolve_stack)
            else
                @test size(reduced.problem.A) == (0,1)
                @test JSimplex._exact_rational(reduced.problem.objective_constant) == direction*cost*JSimplex._exact_rational(tiny)
            end
        end
    end
end
