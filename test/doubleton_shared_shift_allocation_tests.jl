using SparseArrays

@testset "Doubleton row bounds share one exact shift" begin
function doubleton_shared_shift_probe(kind; count=128, T=Float64)
    rhs = T(kind == :negative ? -4 : kind == :zero_shift ? 0 : 4)
    A = sparse(hcat(vcat(T(2),fill(T(3),count)),vcat(T(1),fill(T(2),count))))
    lower = Union{Nothing,T}[rhs; fill(kind in (:one_sided,:unbounded) ? nothing : T(-100),count)]
    upper = Union{Nothing,T}[rhs; fill(kind == :unbounded ? nothing : T(100),count)]
    problem = LinearProblem(A,T[2,3];objective_constant=T(7),row_lower=lower,row_upper=upper,
        column_lower=Union{Nothing,T}[kind == :no_substitution ? T(-10) : nothing,T(-10)],
        column_upper=Union{Nothing,T}[kind == :no_substitution ? T(10) : nothing,T(10)])
    return problem,JSimplex.substitute_free_doubleton
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative,:zero_shift,:one_sided,:unbounded)
        problem,pass = doubleton_shared_shift_probe(kind;count=4,T)
        original = deepcopy(problem)
        result = pass(problem)
        rhs = JSimplex.bound_value(problem.row_lower[1])
        shift = T(3)*rhs/T(2)
        @test size(result.problem.A) == (4,1)
        @test Matrix(result.problem.A) == fill(T(1)/T(2),4,1)
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
        problem,pass = doubleton_shared_shift_probe(:no_substitution;count=4,T)
        result = pass(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
    end
    for (kind,limit) in ((:positive,18_650),(:negative,18_650),(:zero_shift,9_000),(:one_sided,14_050),(:unbounded,9_450),(:no_substitution,100))
        problem,pass = doubleton_shared_shift_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end
