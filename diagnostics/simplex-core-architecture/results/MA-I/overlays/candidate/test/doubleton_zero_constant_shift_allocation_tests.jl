using SparseArrays

@testset "Doubleton zero constant shift allocation guards" begin
function doubleton_zero_constant_shift_probe(kind; count=128, T=Float64)
    pivot = kind == :negative ? T(-2) : kind == :fractional ? T(1)/T(2) : T(kind == :unit_pivot ? 1 : kind == :inexact_beta ? 3 : 2)
    rhs = kind == :negative ? -zero(T) : T(kind == :nonzero_rhs ? 4 : 0)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(pivot,count),ones(T,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(T(3),count),fill(tiny,count));objective_constant=T(7),
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end
    for T in (Float32,Float64,BigFloat), kind in (:positive,:negative,:fractional,:unit_pivot,:nonzero_rhs,:inexact_beta)
        problem,pass = doubleton_zero_constant_shift_probe(kind;count=4,T)
        original = deepcopy(problem)
        result = pass(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test isequal(problem.A,original.A) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:positive,21000),(:negative,21000),(:fractional,21000),(:unit_pivot,18300),(:nonzero_rhs,25000),(:inexact_beta,9500))
        problem,pass = doubleton_zero_constant_shift_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Zero constant shifts retain output values and canonical signs" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (-2,-1,1,2), cost in (-3,3), rhs in (zero(T),-zero(T)), constant in (T(7),-zero(T))
        problem = LinearProblem(sparse(T[pivot 1;3 2]),T[cost,3];objective_constant=constant,
            row_lower=T[rhs,-100],row_upper=T[rhs,100],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        original = deepcopy(problem)
        result = JSimplex.substitute_free_doubleton(problem)
        beta = -T(1)/T(pivot)
        @test size(result.problem.A) == (1,1)
        @test result.problem.A[1,1] == 2+3beta
        @test result.problem.objective == T[3+cost*beta]
        @test result.problem.objective_constant == constant && (!iszero(constant) || !signbit(result.problem.objective_constant))
        @test isequal(result.problem.row_lower[1],problem.row_lower[2]) && isequal(result.problem.row_upper[1],problem.row_upper[2])
        @test JSimplex.postsolve_primal(result,T[2]) == T[2beta,2]
        basis = JSimplex.Basis([2],[JSimplex.FREE_NONBASIC,JSimplex.BASIC])
        @test JSimplex.restore_basis(result,basis).basic_indices == [1,4]
        @test isequal(problem.A,original.A) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant)
    end
end

@testset "Zero constant shifts keep BigFloat precision gates" begin
    for mode in (:exact,:cost,:constant), ambient in (32,64,256), negative_zero in (false,true)
        problem = setprecision(BigFloat,256) do
            epsilon = BigFloat(2)^(-200)
            constant = mode == :constant ? BigFloat(7)+epsilon : negative_zero ? -zero(BigFloat) : BigFloat(7)
            retained_cost = mode == :cost ? BigFloat(3)+epsilon : BigFloat(3)
            LinearProblem(sparse(BigFloat[2 1]),BigFloat[3,retained_cost];objective_constant=constant,
                row_lower=[negative_zero ? -zero(BigFloat) : zero(BigFloat)],row_upper=[zero(BigFloat)],
                column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
        end
        original_constant = JSimplex._exact_rational(problem.objective_constant)
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            if mode != :exact && ambient < 256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A) == (0,1)
                @test JSimplex._exact_rational(result.problem.objective_constant) == original_constant
                @test precision(result.problem.objective_constant) == ambient
                @test !iszero(result.problem.objective_constant) || !signbit(result.problem.objective_constant)
            end
            @test JSimplex._exact_rational(problem.objective_constant) == original_constant && precision(problem.objective_constant) == 256
        end
    end
end

@testset "Tiny nonzero constant shifts are retained or rejected exactly" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), direction in (-1,1), cost in (1//2,2)
        tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<200))
        problem = LinearProblem(sparse(T[2 1]),T[cost,3];objective_constant=zero(T),
            row_lower=T[direction*2tiny],row_upper=T[direction*2tiny],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        result = JSimplex.substitute_free_doubleton(problem)
        if T in (Float32,Float64) && cost == 1//2
            @test result.problem === problem
            @test isempty(result.postsolve_stack)
        else
            @test size(result.problem.A) == (0,1)
            @test JSimplex._exact_rational(result.problem.objective_constant) == direction*JSimplex._exact_rational(tiny)*cost
        end
    end
end
