using SparseArrays

@testset "Doubleton ratios share the exact pivot" begin
function doubleton_shared_pivot_probe(kind; count=128, T=Float64)
    pivot = kind == :negative ? T(-2) : kind == :fractional ? T(1)/T(2) : T(kind == :inexact_ratio ? 3 : 2)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(pivot,count),ones(T,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(T(3),count),fill(tiny,count));objective_constant=T(7),
        row_lower=fill(T(4),count),row_upper=fill(T(kind == :inequality ? 5 : 4),count),
        column_lower=vcat(fill(kind == :no_substitution ? T(-10) : nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(kind == :no_substitution ? T(10) : nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end

    for T in (Float32,Float64,BigFloat), kind in (:positive,:negative,:fractional,:inexact_ratio,:no_substitution,:inequality)
        problem,pass = doubleton_shared_pivot_probe(kind;count=4,T)
        original = deepcopy(problem)
        result = pass(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test problem.A.nzval == original.A.nzval && problem.objective == original.objective && problem.objective_constant == original.objective_constant && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
    for (kind,limit) in ((:positive,25000),(:negative,25000),(:fractional,25000),(:inexact_ratio,11800),(:no_substitution,100),(:inequality,100))
        problem,pass = doubleton_shared_pivot_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Shared doubleton pivots preserve accepted substitutions" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (-2,-1,-1//2,1//2,1,2), rhs in (-4,0,4)
        problem = LinearProblem(sparse(T[pivot 1;3 2]),T[2,3];objective_constant=T(7),
            row_lower=T[rhs,-100],row_upper=T[rhs,100],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        original = deepcopy(problem)
        result = JSimplex.substitute_free_doubleton(problem)
        alpha,beta = T(rhs)/T(pivot),-one(T)/T(pivot)
        @test size(result.problem.A) == (1,1)
        @test result.problem.A[1,1] == T(2)+3beta
        @test result.problem.objective == T[3+2beta]
        @test result.problem.objective_constant == T(7)+2alpha
        @test JSimplex.bound_value(result.problem.row_lower[1]) == T(-100)-3alpha && JSimplex.bound_value(result.problem.row_upper[1]) == T(100)-3alpha
        @test JSimplex.postsolve_primal(result,T[2]) == T[alpha+2beta,2]
        basis = JSimplex.Basis([2],[JSimplex.FREE_NONBASIC,JSimplex.BASIC])
        @test JSimplex.restore_basis(result,basis).basic_indices == [1,4]
        @test problem.A.nzval == original.A.nzval && problem.objective == original.objective && problem.objective_constant == original.objective_constant && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
end

@testset "Shared doubleton pivots retain stored BigFloat precision and exact ratio gates" begin
    for direction in (-1,1), mode in (:exact,:inexact_alpha,:inexact_beta), ambient in (32,64,256)
        problem = setprecision(BigFloat,256) do
            epsilon = BigFloat(2)^(-200)
            pivot = direction*(BigFloat(3)+epsilon)
            rhs = 2pivot+(mode == :inexact_alpha ? 4epsilon : zero(BigFloat))
            retained = pivot/2+(mode == :inexact_beta ? epsilon : zero(BigFloat))
            LinearProblem(sparse(reshape([pivot,retained],1,2)),BigFloat[2,3];objective_constant=BigFloat(7),
                row_lower=[rhs],row_upper=[rhs],
                column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
        end
        pivot = JSimplex._exact_rational(problem.A[1,1])
        retained = JSimplex._exact_rational(problem.A[1,2])
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            if mode == :exact
                @test size(result.problem.A) == (0,1)
                @test result.problem.objective == BigFloat[2] && result.problem.objective_constant == BigFloat(11)
                @test JSimplex.postsolve_primal(result,BigFloat[2]) == BigFloat[1,2]
            else
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            end
            @test JSimplex._exact_rational(problem.A[1,1]) == pivot && JSimplex._exact_rational(problem.A[1,2]) == retained
            @test precision(problem.A[1,1]) == 256 && precision(problem.A[1,2]) == 256
        end
    end
end

@testset "Rejected doubletons do not reuse the previous pivot" begin
    for T in (Float32,Float64,BigFloat)
        problem = LinearProblem(sparse(T[3 0 1 0;0 -2 0 1]),T[3,-5,3,3];objective_constant=T(7),
            row_lower=T[4,6],row_upper=T[4,6],
            column_lower=Union{Nothing,T}[nothing,nothing,T(-10),T(-10)],
            column_upper=Union{Nothing,T}[nothing,nothing,T(10),T(10)])
        result = JSimplex.substitute_free_doubleton(problem)
        @test size(result.problem.A) == (1,3)
        @test result.problem.objective == T[3,3,1//2]
        @test result.problem.objective_constant == T(22)
        @test JSimplex.postsolve_primal(result,T[1,2,2]) == T[1,-2,2,2]
    end
end
