using SparseArrays

@testset "Doubleton ratios reuse an exact zero rhs" begin
function doubleton_zero_alpha_probe(kind; count=128, T=Float64)
    pivot = kind == :negative ? T(-2) : kind == :fractional ? T(1)/T(2) : T(kind == :inexact_beta ? 3 : kind == :unit_pivot ? 1 : 2)
    rhs = kind == :negative ? -zero(T) : T(kind == :nonzero_rhs ? 4 : 0)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(pivot,count),ones(T,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(T(3),count),fill(tiny,count));objective_constant=T(7),
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end

    for T in (Float32,Float64,BigFloat), kind in (:positive,:negative,:fractional,:inexact_beta,:nonzero_rhs,:unit_pivot)
        problem,pass = doubleton_zero_alpha_probe(kind;count=4,T)
        original = deepcopy(problem)
        result = pass(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test problem.A.nzval == original.A.nzval && problem.objective == original.objective && problem.objective_constant == original.objective_constant && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
    for (kind,limit) in ((:positive,22500),(:negative,22500),(:fractional,22500),(:inexact_beta,9500),(:nonzero_rhs,25000),(:unit_pivot,19700))
        problem,pass = doubleton_zero_alpha_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Zero-alpha substitutions preserve row bounds and restoration" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (-2,-1//2,1//2,2), retained in (-1,1), negative_zero in (false,true)
        rhs = negative_zero ? -zero(T) : zero(T)
        problem = LinearProblem(sparse(T[pivot retained;3 2]),T[2,3];objective_constant=T(7),
            row_lower=T[rhs,-100],row_upper=T[rhs,100],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        original = deepcopy(problem)
        result = JSimplex.substitute_free_doubleton(problem)
        beta = -T(retained)/T(pivot)
        @test size(result.problem.A) == (1,1)
        @test result.problem.A[1,1] == T(2)+3beta
        @test result.problem.objective == T[3+2beta] && result.problem.objective_constant == T(7)
        @test result.problem.row_lower[1] === problem.row_lower[2] && result.problem.row_upper[1] === problem.row_upper[2]
        step = only(result.postsolve_stack)
        @test iszero(step.alpha) && !signbit(step.alpha)
        @test JSimplex.postsolve_primal(result,T[2]) == T[2beta,2]
        basis = JSimplex.Basis([2],[JSimplex.FREE_NONBASIC,JSimplex.BASIC])
        @test JSimplex.restore_basis(result,basis).basic_indices == [1,4]
        @test problem.A.nzval == original.A.nzval && problem.objective == original.objective && problem.objective_constant == original.objective_constant && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Tiny nonzero rhs values still produce nonzero alpha" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), direction in (-1,1), pivot in (-2,2), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            tiny = T in (Float32,Float64) ? direction*nextfloat(zero(T)) : T(direction*(BigInt(1)//(BigInt(1)<<200)))
            LinearProblem(sparse(reshape(T[pivot,1],1,2)),T[0,3];objective_constant=T(7),
                row_lower=T[2tiny],row_upper=T[2tiny],
                column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        end
        expected = JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1]))/pivot
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            @test size(result.problem.A) == (0,1)
            step = only(result.postsolve_stack)
            @test JSimplex._exact_rational(step.alpha) == expected && !iszero(step.alpha)
            @test JSimplex._exact_rational(JSimplex.postsolve_primal(result,T[0])[1]) == expected
            @test result.problem.objective == T[3] && result.problem.objective_constant == T(7)
        end
    end
    for T in (Float32,Float64), direction in (-1,1), pivot in (-2,2)
        rhs = direction*nextfloat(zero(T))
        problem = LinearProblem(sparse(reshape(T[pivot,1],1,2)),T[0,3];
            row_lower=T[rhs],row_upper=T[rhs],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        result = JSimplex.substitute_free_doubleton(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
    end
end

@testset "Zero-alpha reuse retains beta and objective representability gates" begin
    for negative_zero in (false,true), mode in (:exact,:beta,:cost,:constant), ambient in (32,64,256)
        problem = setprecision(BigFloat,256) do
            epsilon = BigFloat(2)^(-200)
            pivot = BigFloat(3)+epsilon
            retained = pivot/2+(mode == :beta ? epsilon : zero(BigFloat))
            rhs = negative_zero ? -zero(BigFloat) : zero(BigFloat)
            cost = mode == :cost ? BigFloat(3)+epsilon : BigFloat(3)
            constant = mode == :constant ? BigFloat(7)+epsilon : BigFloat(7)
            LinearProblem(sparse(reshape([pivot,retained],1,2)),[zero(BigFloat),cost];objective_constant=constant,
                row_lower=[rhs],row_upper=[rhs],
                column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
        end
        saved_pivot = JSimplex._exact_rational(problem.A[1,1])
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            if mode == :beta || (mode in (:cost,:constant) && ambient < 256)
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A) == (0,1)
                @test iszero(only(result.postsolve_stack).alpha) && !signbit(only(result.postsolve_stack).alpha)
                @test JSimplex._exact_rational(result.problem.objective[1]) == JSimplex._exact_rational(problem.objective[2]) && JSimplex._exact_rational(result.problem.objective_constant) == JSimplex._exact_rational(problem.objective_constant)
            end
            @test JSimplex._exact_rational(problem.A[1,1]) == saved_pivot
            @test signbit(JSimplex.bound_value(problem.row_lower[1])) == negative_zero && precision(JSimplex.bound_value(problem.row_lower[1])) == 256
        end
    end
end
