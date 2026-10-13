using SparseArrays

@testset "Sparse aggregation avoids unused shifts of unbounded rows" begin
function aggregation_unbounded_shift_probe(kind; count=128, T=Float64)
    coefficient = T(kind in (:negative_coefficient,:both_negative) ? -4 : 4)
    rhs = T(kind in (:negative_rhs,:both_negative) ? -4 : 4)
    odd = collect(1:2:2count); even = odd .+ 1
    A = sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(T(2),count),fill(T(1),count),fill(coefficient,count),fill(T(3),count)),2count,2count)
    problem = LinearProblem(A,[isodd(i) ? T(0) : T(2) for i in 1:2count];objective_constant=T(7),
        row_lower=Union{Nothing,T}[isodd(i) ? rhs : kind == :finite ? T(-100) : nothing for i in 1:2count],
        row_upper=Union{Nothing,T}[isodd(i) ? rhs : kind in (:finite,:one_sided) ? T(100) : nothing for i in 1:2count],
        column_lower=Union{Nothing,T}[isodd(i) ? nothing : T(-10) for i in 1:2count],
        column_upper=Union{Nothing,T}[isodd(i) ? nothing : T(10) for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative_coefficient,:negative_rhs,:both_negative,:finite,:one_sided), zero_rhs in (false,true)
        problem,pass = aggregation_unbounded_shift_probe(kind;count=4,T)
        if zero_rhs
            for row in 1:2:8
                problem.row_lower[row] = problem.row_upper[row] = Bound(T(0))
            end
        end
        original = deepcopy(problem)
        result = pass(problem)
        coefficient = problem.A[2,1]
        rhs = JSimplex.bound_value(problem.row_lower[1])
        shift = coefficient*rhs/T(2)
        @test size(result.problem.A) == (4,4)
        @test result.problem.A == sparse(1:4,1:4,fill(T(3)-coefficient/T(2),4),4,4)
        @test result.problem.objective == fill(T(2),4) && result.problem.objective_constant == T(7)
        @test all((kind == :finite ? JSimplex.bound_value(result.problem.row_lower[i]) == T(-100)-shift : !isfinite(result.problem.row_lower[i])) && (kind in (:finite,:one_sided) ? JSimplex.bound_value(result.problem.row_upper[i]) == T(100)-shift : !isfinite(result.problem.row_upper[i])) for i in 1:4)
        @test all((isfinite(problem.row_lower[2i]) || result.problem.row_lower[i] === problem.row_lower[2i]) && (isfinite(problem.row_upper[2i]) || result.problem.row_upper[i] === problem.row_upper[2i]) for i in 1:4)
        @test JSimplex.postsolve_primal(result,fill(T(0),4)) == repeat(T[rhs/T(2),0],4)
        basis = JSimplex.Basis(collect(5:8),[fill(JSimplex.FREE_NONBASIC,4);fill(JSimplex.BASIC,4)])
        @test JSimplex.restore_basis(result,basis).basic_indices == [1,10,3,12,5,14,7,16]
        @test isequal(problem.A.nzval,original.A.nzval) && problem.A.colptr == original.A.colptr && problem.A.rowval == original.A.rowval && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper && problem.objective == original.objective && problem.objective_constant == original.objective_constant
    end
    for (kind,limit) in ((:positive,24_000),(:negative_coefficient,24_000),(:negative_rhs,24_000),(:both_negative,24_000),(:finite,34_150),(:one_sided,29_550))
        problem,pass = aggregation_unbounded_shift_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Unbounded sparse aggregation rows still require exact matrix updates" begin
    for T in (Float32,Float64), direction in (-1,1)
        tiny = direction*nextfloat(zero(T))
        problem = LinearProblem(sparse(T[2 1; tiny 0]),T[0,3];
            row_lower=[T(4),nothing],row_upper=[T(4),nothing],
            column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test isequal(problem.A.nzval,original.A.nzval) && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
end

@testset "Either finite endpoint still requires an exact sparse aggregation shift" begin
    for T in (Float32,Float64), direction in (-1,1), endpoint in (:neither,:lower,:upper)
        tiny = direction*nextfloat(zero(T))
        problem = LinearProblem(sparse(T[1 1; 0.5 1]),T[0,3];
            row_lower=[tiny,endpoint == :lower ? T(0) : nothing],
            row_upper=[tiny,endpoint == :upper ? T(0) : nothing],
            column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        if endpoint == :neither
            @test size(result.problem.A) == (1,1) && result.problem.A[1,1] == T(0.5)
            @test !isfinite(result.problem.row_lower[1]) && !isfinite(result.problem.row_upper[1])
            @test JSimplex.postsolve_primal(result,T[0]) == T[tiny,0]
        else
            @test result.problem === problem
            @test isempty(result.postsolve_stack)
        end
        @test isequal(problem.A.nzval,original.A.nzval) && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
end

@testset "Unbounded sparse aggregation endpoints retain stored BigFloat identity" begin
    for ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            p = LinearProblem(sparse(BigFloat[2 1; 3 2]),BigFloat[0,3];
                row_lower=[BigFloat(4),nothing],row_upper=[BigFloat(4),nothing],
                column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
            p.row_lower[2] = Bound{BigFloat}(nothing)
            p.row_upper[2] = Bound{BigFloat}(nothing)
            p
        end
        saved = deepcopy(problem)
        setprecision(BigFloat,ambient) do
            result = JSimplex.aggregate_sparse_equalities(problem)
            @test size(result.problem.A) == (1,1)
            @test result.problem.row_lower[1] === problem.row_lower[2]
            @test result.problem.row_upper[1] === problem.row_upper[2]
            @test precision(result.problem.row_lower[1].value) == 256
            @test precision(result.problem.row_upper[1].value) == 256
            @test problem.row_lower == saved.row_lower && problem.row_upper == saved.row_upper
        end
    end
end
