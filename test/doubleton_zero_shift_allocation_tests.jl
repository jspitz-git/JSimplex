using SparseArrays

@testset "Doubleton avoids zero exact row products" begin
function doubleton_zero_shift_probe(kind; count=128, T=Float64)
    rhs = T(kind in (:nonzero_shift,:no_substitution) ? 4 : 0)
    coefficient = T(kind == :negative ? -3 : 3)
    A = sparse(hcat(vcat(T(2),fill(coefficient,count)),vcat(T(1),fill(T(2),count))))
    lower = Union{Nothing,T}[rhs; fill(kind in (:one_sided,:unbounded) ? nothing : T(-100),count)]
    upper = Union{Nothing,T}[rhs; fill(kind == :unbounded ? nothing : T(100),count)]
    problem = LinearProblem(A,T[2,3];objective_constant=T(7),row_lower=lower,row_upper=upper,
        column_lower=Union{Nothing,T}[kind == :no_substitution ? T(-10) : nothing,T(-10)],
        column_upper=Union{Nothing,T}[kind == :no_substitution ? T(10) : nothing,T(10)])
    return problem,JSimplex.substitute_free_doubleton
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative,:one_sided,:unbounded,:nonzero_shift)
        problem,pass = doubleton_zero_shift_probe(kind;count=4,T)
        original = deepcopy(problem)
        result = pass(problem)
        rhs = JSimplex.bound_value(problem.row_lower[1])
        coefficient = T(kind == :negative ? -3 : 3)
        shift = coefficient*rhs/T(2)
        @test size(result.problem.A) == (4,1)
        @test Matrix(result.problem.A) == fill(T(2)-coefficient/T(2),4,1)
        @test result.problem.objective == T[2] && result.problem.objective_constant == T(7)+rhs
        @test all(kind in (:one_sided,:unbounded) ? !isfinite(bound) : JSimplex.bound_value(bound) == T(-100)-shift for bound in result.problem.row_lower)
        @test all(kind == :unbounded ? !isfinite(bound) : JSimplex.bound_value(bound) == T(100)-shift for bound in result.problem.row_upper)
        @test JSimplex.postsolve_primal(result,T[2]) == T[(rhs-T(2))/T(2),2]
        basis = JSimplex.Basis(collect(2:5),[JSimplex.FREE_NONBASIC;fill(JSimplex.BASIC,4)])
        restored = JSimplex.restore_basis(result,basis)
        @test restored.basic_indices == [1,4,5,6,7]
        @test problem.A.nzval == original.A.nzval && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper && problem.objective == original.objective && problem.objective_constant == original.objective_constant
    end
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        problem,pass = doubleton_zero_shift_probe(:no_substitution;count=4,T)
        result = pass(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
    end
    for (kind,limit) in ((:positive,8_050),(:negative,8_050),(:one_sided,8_050),(:unbounded,8_050),(:nonzero_shift,18_250),(:no_substitution,100))
        problem,pass = doubleton_zero_shift_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Doubleton preserves tiny nonzero exact shifts" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), direction in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            tiny = T in (Float32,Float64) ? direction*nextfloat(zero(T)) : T(direction*(BigInt(1)//(BigInt(1)<<200)))
            LinearProblem(sparse(T[1 1; 2 3]),T[0,3];objective_constant=T(7),
                row_lower=T[tiny,0],row_upper=[tiny,nothing],
                column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        end
        original = JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1]))
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            @test size(result.problem.A) == (1,1)
            @test JSimplex._exact_rational(JSimplex.bound_value(result.problem.row_lower[1])) == -2original
            @test !iszero(JSimplex.bound_value(result.problem.row_lower[1]))
            @test JSimplex.postsolve_primal(result,T[0]) == T[JSimplex.bound_value(problem.row_lower[1]),0]
            @test result.problem.objective == T[3] && result.problem.objective_constant == T(7)
            @test JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1])) == original
        end
    end
end

@testset "Doubleton rejects unrepresentable nonzero exact shifts" begin
    for T in (Float32,Float64), direction in (-1,1), endpoint in (:lower,:upper)
        tiny = direction*nextfloat(zero(T))
        problem = LinearProblem(sparse(T[1 1; 0.5 3]),T[0,3];
            row_lower=[tiny,endpoint == :lower ? T(0) : nothing],
            row_upper=[tiny,endpoint == :upper ? T(0) : nothing],
            column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        original = deepcopy(problem)
        result = JSimplex.substitute_free_doubleton(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test problem.A.nzval == original.A.nzval && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
end
