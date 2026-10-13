using SparseArrays

@testset "Doubleton zero retained cost allocation guards" begin
function doubleton_zero_retained_cost_probe(kind; count=128, T=Float64)
    pivot = T(kind == :inexact_beta ? 3 : 2)
    cost = T(kind == :negative ? -3 : kind == :unit_positive ? 1 : kind == :unit_negative ? -1 : 3)
    retained_cost = kind in (:negative,:unit_negative) ? -zero(T) : T(kind == :nonzero_retained ? 3 : 0)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(pivot,count),ones(T,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(cost,count),fill(retained_cost,count));objective_constant=tiny,
        row_lower=fill(T(4),count),row_upper=fill(T(4),count),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end
    for T in (Float32,Float64,BigFloat), kind in (:positive,:negative,:unit_positive,:unit_negative,:nonzero_retained,:inexact_beta)
        problem,pass = doubleton_zero_retained_cost_probe(kind;count=4,T)
        original = deepcopy(problem)
        result = pass(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test isequal(problem.A,original.A) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:positive,23000),(:negative,23000),(:unit_positive,19000),(:unit_negative,19500),(:nonzero_retained,25000),(:inexact_beta,11500))
        problem,pass = doubleton_zero_retained_cost_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Zero retained costs preserve transforms and restoration" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), beta in (-1,-1//2,1//2,1), cost in (-3,-1,0,1,3), retained_cost in (zero(T),-zero(T))
        problem = LinearProblem(sparse(T[2 -2beta;3 2]),T[cost,retained_cost];objective_constant=T(7),
            row_lower=T[4,-100],row_upper=T[4,100],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        original = deepcopy(problem)
        result = JSimplex.substitute_free_doubleton(problem)
        @test size(result.problem.A) == (1,1)
        @test result.problem.A[1,1] == 2+3beta
        @test result.problem.objective == T[cost*beta]
        @test !iszero(result.problem.objective[1]) || !signbit(result.problem.objective[1])
        @test result.problem.objective_constant == 7+2cost
        @test JSimplex.bound_value(result.problem.row_lower[1]) == -106 && JSimplex.bound_value(result.problem.row_upper[1]) == 94
        @test JSimplex.postsolve_primal(result,T[2]) == T[2+2beta,2]
        basis = JSimplex.Basis([2],[JSimplex.FREE_NONBASIC,JSimplex.BASIC])
        @test JSimplex.restore_basis(result,basis).basic_indices == [1,4]
        @test isequal(problem.A,original.A) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant)
    end
end

@testset "Zero retained costs keep BigFloat precision gates" begin
    for mode in (:exact,:cost,:constant), ambient in (32,64,256), beta in (-1,-1//2,1//2,1), negative_zero in (false,true)
        problem = setprecision(BigFloat,256) do
            epsilon = BigFloat(2)^(-200)
            constant = BigFloat(7)+(mode == :constant ? epsilon : zero(BigFloat))
            cost = BigFloat(3)+(mode == :cost ? epsilon : zero(BigFloat))
            LinearProblem(sparse(BigFloat[2 -2beta]),[cost,negative_zero ? -zero(BigFloat) : zero(BigFloat)];objective_constant=constant,
                row_lower=[zero(BigFloat)],row_upper=[zero(BigFloat)],
                column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
        end
        original_constant = JSimplex._exact_rational(problem.objective_constant)
        original_cost = JSimplex._exact_rational(problem.objective[1])
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            if mode != :exact && ambient < 256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A) == (0,1)
                @test JSimplex._exact_rational(result.problem.objective[1]) == beta*original_cost
                @test JSimplex._exact_rational(result.problem.objective_constant) == original_constant
                @test precision(result.problem.objective_constant) == ambient && precision(result.problem.objective[1]) == ambient
            end
            @test JSimplex._exact_rational(problem.objective_constant) == original_constant && JSimplex._exact_rational(problem.objective[1]) == original_cost && signbit(problem.objective[2]) == negative_zero
        end
    end
end

@testset "Tiny retained costs and tiny output costs keep exact gates" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), direction in (-1,1)
        tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
        problem = LinearProblem(sparse(T[2 1]),T[3,direction*tiny];objective_constant=T(7),
            row_lower=T[0],row_upper=T[0],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        result = JSimplex.substitute_free_doubleton(problem)
        if T == Rational{BigInt}
            @test size(result.problem.A) == (0,1)
            @test result.problem.objective[1] == direction*tiny-3//2
        else
            @test result.problem === problem
            @test isempty(result.postsolve_stack)
        end
        for multiplier in (1,2)
            small = LinearProblem(sparse(T[2 1]),T[direction*multiplier*tiny,0];objective_constant=T(7),
                row_lower=T[0],row_upper=T[0],
                column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
            reduced = JSimplex.substitute_free_doubleton(small)
            if T in (Float32,Float64) && multiplier == 1
                @test reduced.problem === small
                @test isempty(reduced.postsolve_stack)
            else
                @test size(reduced.problem.A) == (0,1)
                @test JSimplex._exact_rational(reduced.problem.objective[1]) == -direction*multiplier*JSimplex._exact_rational(tiny)/2
            end
        end
    end
end
