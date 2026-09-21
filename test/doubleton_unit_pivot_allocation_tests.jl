using SparseArrays

@testset "Doubleton ratios reuse signed-unit pivots" begin
function doubleton_unit_pivot_probe(kind; count=128, T=Float64)
    pivot = T(kind in (:negative,:negative_zero_rhs) ? -1 : kind == :nonunit ? 2 : kind == :inexact_ratio ? 3 : 1)
    rhs = kind == :negative_zero_rhs ? -zero(T) : T(kind == :zero_rhs ? 0 : 4)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(pivot,count),ones(T,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(T(3),count),fill(tiny,count));objective_constant=T(7),
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end

    for T in (Float32,Float64,BigFloat), kind in (:positive,:negative,:zero_rhs,:negative_zero_rhs,:nonunit,:inexact_ratio)
        problem,pass = doubleton_unit_pivot_probe(kind;count=4,T)
        original = deepcopy(problem)
        result = pass(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test problem.A.nzval == original.A.nzval && problem.objective == original.objective && problem.objective_constant == original.objective_constant && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
    for (kind,limit) in ((:positive,22000),(:negative,22000),(:zero_rhs,20500),(:negative_zero_rhs,20500),(:nonunit,25000),(:inexact_ratio,11300))
        problem,pass = doubleton_unit_pivot_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Signed-unit pivots preserve accepted substitutions" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (-1,1), retained in (-3,-1,1,3), rhs in (-4,0,4)
        problem = LinearProblem(sparse(T[pivot retained;3 2]),T[2,3];objective_constant=T(7),
            row_lower=T[rhs,-100],row_upper=T[rhs,100],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        original = deepcopy(problem)
        result = JSimplex.substitute_free_doubleton(problem)
        alpha,beta = T(rhs)/T(pivot),-T(retained)/T(pivot)
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

@testset "Near-unit pivots retain exact division" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), direction in (-1,1), ambient in (32,64,256)
        problem = setprecision(BigFloat,256) do
            pivot = T in (Float32,Float64) ? T(direction)*nextfloat(one(T)) : T(direction*(1+(BigInt(1)//(BigInt(1)<<200))))
            LinearProblem(sparse(reshape(T[pivot,pivot],1,2)),T[2,3];objective_constant=T(7),
                row_lower=T[2pivot],row_upper=T[2pivot],
                column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        end
        pivot = JSimplex._exact_rational(problem.A[1,1])
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            @test size(result.problem.A) == (0,1)
            @test result.problem.objective == T[1] && result.problem.objective_constant == T(11)
            @test JSimplex.postsolve_primal(result,T[2]) == T[0,2]
            @test JSimplex._exact_rational(problem.A[1,1]) == pivot
        end
    end
end

@testset "Unit-pivot reuse retains both ratio representability gates" begin
    for pivot in (-1,1), mode in (:alpha,:beta), ambient in (32,64,256)
        problem = setprecision(BigFloat,256) do
            high = BigFloat(3)+BigFloat(2)^(-200)
            rhs = mode == :alpha ? high : BigFloat(4)
            retained = mode == :beta ? high : BigFloat(1)
            LinearProblem(sparse(reshape([BigFloat(pivot),retained],1,2)),BigFloat[0,3];objective_constant=BigFloat(7),
                row_lower=[rhs],row_upper=[rhs],
                column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
        end
        rhs = JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1]))
        retained = JSimplex._exact_rational(problem.A[1,2])
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            if ambient < 256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A) == (0,1)
                step = only(result.postsolve_stack)
                @test JSimplex._exact_rational(step.alpha) == rhs/pivot && JSimplex._exact_rational(step.beta) == -retained/pivot
            end
            @test JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1])) == rhs && JSimplex._exact_rational(problem.A[1,2]) == retained
        end
    end
end

@testset "Near-unit pivots still reject nonrepresentable ratios" begin
    for direction in (-1,1), mode in (:alpha,:beta), ambient in (32,64,256)
        problem = setprecision(BigFloat,256) do
            pivot = direction*(BigFloat(1)+BigFloat(2)^(-200))
            rhs = mode == :alpha ? BigFloat(4) : 2pivot
            retained = mode == :beta ? BigFloat(1) : pivot
            LinearProblem(sparse(reshape([pivot,retained],1,2)),BigFloat[0,3];
                row_lower=[rhs],row_upper=[rhs],
                column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
        end
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            @test result.problem === problem
            @test isempty(result.postsolve_stack)
        end
    end
end
