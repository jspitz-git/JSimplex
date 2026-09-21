using SparseArrays

@testset "Doubleton shifts reuse signed unit operands" begin
function doubleton_unit_shift_probe(kind; count=128, T=Float64)
    rhs = T(kind == :positive_alpha ? 2 : kind == :negative_alpha ? -2 : kind == :zero_alpha ? 0 : 4)
    coefficient = T(kind == :positive_coefficient ? 1 : kind == :negative_coefficient ? -1 : 3)
    A = sparse(hcat(vcat(T(2),fill(coefficient,count)),vcat(T(1),fill(T(2),count))))
    problem = LinearProblem(A,T[2,3];objective_constant=T(7),
        row_lower=vcat(rhs,fill(T(-100),count)),row_upper=vcat(rhs,fill(T(100),count)),
        column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
    return problem,JSimplex.substitute_free_doubleton
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive_coefficient,:negative_coefficient,:positive_alpha,:negative_alpha,:nonunit,:zero_alpha), endpoint in (:both,:lower,:upper,:neither)
        problem,pass = doubleton_unit_shift_probe(kind;count=4,T)
        endpoint in (:upper,:neither) && fill!(view(problem.row_lower,2:5),Bound{T}(nothing))
        endpoint in (:lower,:neither) && fill!(view(problem.row_upper,2:5),Bound{T}(nothing))
        original = deepcopy(problem)
        result = pass(problem)
        rhs = JSimplex.bound_value(problem.row_lower[1])
        coefficient = problem.A[2,1]
        shift = coefficient*rhs/T(2)
        @test size(result.problem.A) == (4,1)
        @test Matrix(result.problem.A) == fill(T(2)-coefficient/T(2),4,1)
        @test result.problem.objective == T[2] && result.problem.objective_constant == T(7)+rhs
        @test all(endpoint in (:upper,:neither) ? !isfinite(bound) : JSimplex.bound_value(bound) == T(-100)-shift for bound in result.problem.row_lower)
        @test all(endpoint in (:lower,:neither) ? !isfinite(bound) : JSimplex.bound_value(bound) == T(100)-shift for bound in result.problem.row_upper)
        @test JSimplex.postsolve_primal(result,T[2]) == T[(rhs-T(2))/T(2),2]
        basis = JSimplex.Basis(collect(2:5),[JSimplex.FREE_NONBASIC;fill(JSimplex.BASIC,4)])
        @test JSimplex.restore_basis(result,basis).basic_indices == [1,4,5,6,7]
        @test problem.A.nzval == original.A.nzval && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper && problem.objective == original.objective && problem.objective_constant == original.objective_constant
    end
    for (kind,limit) in ((:positive_coefficient,17_400),(:negative_coefficient,17_400),(:positive_alpha,17_400),(:negative_alpha,17_400),(:nonunit,18_250),(:zero_alpha,7_850))
        problem,pass = doubleton_unit_shift_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Doubleton near-unit coefficients retain stored precision" begin
    for sign in (-1,1), direction in (-1,1), alpha in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            coefficient = BigFloat(sign)+direction*BigFloat(2)^(-200)
            LinearProblem(sparse(BigFloat[1 1; coefficient sign]),BigFloat[0,3];objective_constant=BigFloat(7),
                row_lower=BigFloat[alpha,alpha*sign],row_upper=[BigFloat(alpha),nothing],
                column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
        end
        original = JSimplex._exact_rational(problem.A[2,1])
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            @test size(result.problem.A) == (1,1)
            @test JSimplex._exact_rational(result.problem.A[1,1]) == sign-original
            @test JSimplex._exact_rational(JSimplex.bound_value(result.problem.row_lower[1])) == alpha*(sign-original)
            @test !iszero(JSimplex.bound_value(result.problem.row_lower[1]))
            @test JSimplex.postsolve_primal(result,BigFloat[0]) == BigFloat[alpha,0]
            @test JSimplex._exact_rational(problem.A[2,1]) == original && precision(problem.A[2,1]) == 256
        end
    end
end

@testset "Doubleton near-unit alpha preserves exact representability checks" begin
    for sign in (-1,1), direction in (-1,1), ambient in (32,64,256)
        problem = setprecision(BigFloat,256) do
            alpha = BigFloat(sign)+direction*BigFloat(2)^(-200)
            LinearProblem(sparse(BigFloat[2 1; 1 2]),BigFloat[0,3];objective_constant=BigFloat(7),
                row_lower=BigFloat[2alpha,sign],row_upper=[2alpha,nothing],
                column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
        end
        original = JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1]))
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            if ambient == 256
                @test size(result.problem.A) == (1,1)
                @test JSimplex._exact_rational(JSimplex.bound_value(result.problem.row_lower[1])) == sign-original/2
                @test !iszero(JSimplex.bound_value(result.problem.row_lower[1]))
            else
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            end
            @test JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1])) == original
        end
    end
end
