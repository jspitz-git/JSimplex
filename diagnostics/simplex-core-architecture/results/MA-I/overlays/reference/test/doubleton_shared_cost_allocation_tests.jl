using SparseArrays

@testset "Doubleton objective updates share the exact eliminated cost" begin
function doubleton_shared_cost_probe(kind; count=128, T=Float64)
    pivot = T(kind == :inexact_ratio ? 3 : 2)
    cost = kind == :negative ? T(-3) : kind == :fractional ? T(3)/T(2) : T(3)
    rhs = T(kind == :zero_rhs ? 0 : 4)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(pivot,count),ones(T,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(cost,count),fill(tiny,count));objective_constant=T(7),
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=vcat(fill(kind == :no_substitution ? T(-10) : nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(kind == :no_substitution ? T(10) : nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end

    for T in (Float32,Float64,BigFloat), kind in (:positive,:negative,:fractional,:zero_rhs,:inexact_ratio,:no_substitution)
        problem,pass = doubleton_shared_cost_probe(kind;count=4,T)
        original = deepcopy(problem)
        result = pass(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test problem.A.nzval == original.A.nzval && problem.objective == original.objective && problem.objective_constant == original.objective_constant && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
    for (kind,limit) in ((:positive,26500),(:negative,26500),(:fractional,26500),(:zero_rhs,25250),(:inexact_ratio,12800),(:no_substitution,100))
        problem,pass = doubleton_shared_cost_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Shared doubleton costs preserve accepted objective and row updates" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), cost in (-3,-1,0,1,3,3//2), rhs in (-4,0,4)
        problem = LinearProblem(sparse(T[2 1;3 2]),T[cost,3];objective_constant=T(7),
            row_lower=T[rhs,-100],row_upper=T[rhs,100],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        original = deepcopy(problem)
        result = JSimplex.substitute_free_doubleton(problem)
        alpha = T(rhs)/T(2)
        @test size(result.problem.A) == (1,1)
        @test result.problem.A[1,1] == T(1)/T(2)
        @test result.problem.objective == T[3-T(cost)/2]
        @test result.problem.objective_constant == T(7)+T(cost)*alpha
        @test JSimplex.bound_value(result.problem.row_lower[1]) == T(-100)-3alpha && JSimplex.bound_value(result.problem.row_upper[1]) == T(100)-3alpha
        @test JSimplex.postsolve_primal(result,T[2]) == T[alpha-1,2]
        basis = JSimplex.Basis([2],[JSimplex.FREE_NONBASIC,JSimplex.BASIC])
        @test JSimplex.restore_basis(result,basis).basic_indices == [1,4]
        @test problem.A.nzval == original.A.nzval && problem.objective == original.objective && problem.objective_constant == original.objective_constant && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
end

@testset "Shared doubleton cost conversion preserves stored BigFloat precision" begin
    for direction in (-1,1), mode in (:cancel,:reject_cost,:reject_constant), ambient in (32,64,256)
        problem = setprecision(BigFloat,256) do
            cost = direction*(BigFloat(3)+BigFloat(2)^(-200))
            retained_cost = mode == :reject_cost ? zero(BigFloat) : cost/2
            constant = mode == :reject_constant ? zero(BigFloat) : -2cost
            LinearProblem(sparse(reshape(BigFloat[2,1],1,2)),[cost,retained_cost];objective_constant=constant,
                row_lower=BigFloat[4],row_upper=BigFloat[4],
                column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
        end
        cost = JSimplex._exact_rational(problem.objective[1])
        expected_cost = JSimplex._exact_rational(problem.objective[2])-cost/2
        expected_constant = JSimplex._exact_rational(problem.objective_constant)+2cost
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            if mode == :cancel || ambient == 256
                @test size(result.problem.A) == (0,1)
                @test JSimplex._exact_rational(result.problem.objective[1]) == expected_cost
                @test JSimplex._exact_rational(result.problem.objective_constant) == expected_constant
            else
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            end
            @test JSimplex._exact_rational(problem.objective[1]) == cost && precision(problem.objective[1]) == 256
        end
    end
end

@testset "Rejected doubletons do not reuse the previous candidate cost" begin
    for T in (Float32,Float64)
        tiny = nextfloat(zero(T))
        problem = LinearProblem(sparse(T[2 0 1 0;0 2 0 1]),T[3,-5,tiny,3];objective_constant=T(7),
            row_lower=T[4,6],row_upper=T[4,6],
            column_lower=Union{Nothing,T}[nothing,nothing,T(-10),T(-10)],
            column_upper=Union{Nothing,T}[nothing,nothing,T(10),T(10)])
        result = JSimplex.substitute_free_doubleton(problem)
        @test size(result.problem.A) == (1,3)
        @test result.problem.objective == T[3,tiny,11//2]
        @test result.problem.objective_constant == T(-8)
        @test JSimplex.postsolve_primal(result,T[1,2,2]) == T[1,2,2,2]
    end
end
