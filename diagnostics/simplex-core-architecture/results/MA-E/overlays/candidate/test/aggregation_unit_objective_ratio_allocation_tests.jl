using SparseArrays

@testset "Unit objective ratios preserve costs and restoration" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), coefficient in (1,-1), price in (-3,0,3), sparse_pass in (false,true)
        problem = LinearProblem(sparse(T[coefficient 1; (sparse_pass ? 1 : 0) (sparse_pass ? 2 : 1)]),T[price,3];
            objective_constant=T(7),row_lower=[T(5),nothing],row_upper=T[5,20],
            column_lower=[T(1),nothing],column_upper=[T(3),nothing])
        original = deepcopy(problem)
        pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
        result = pass(problem)
        ratio = price*coefficient
        @test size(result.problem.A) == (2,1)
        @test result.problem.objective == T[3-ratio]
        @test result.problem.objective_constant == T(7+5ratio)
        @test JSimplex.postsolve_primal(result,T[5-2coefficient]) == T[2,5-2coefficient]
        @test !isempty(result.postsolve_stack)
        @test problem.objective == original.objective
        @test problem.objective_constant == original.objective_constant
        @test problem.row_lower == original.row_lower && problem.column_lower == original.column_lower
    end
end

@testset "Sequential unit ratios retain previously committed costs" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), prices in ((2,3),(3,2)), sparse_pass in (false,true)
        A = sparse(T[1 0 1; 0 -1 1])
        lower = Union{Nothing,T}[4,6]
        upper = T[4,6]
        if sparse_pass
            A = vcat(A,sparse(reshape(T[1,1,3],1,3)))
            push!(lower,nothing); push!(upper,T(20))
        end
        problem = LinearProblem(A,T[prices[1],prices[2],5];objective_constant=T(7),
            row_lower=lower,row_upper=upper,column_lower=fill(nothing,3),column_upper=fill(nothing,3))
        pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
        result = pass(problem)
        @test result.problem.objective == T[5-prices[1]+prices[2]]
        @test result.problem.objective_constant == T(7+4prices[1]-6prices[2])
        @test JSimplex.postsolve_primal(result,T[2]) == T[2,-4,2]
        @test problem.objective == T[prices[1],prices[2],5]
    end
end

@testset "Tiny unit-ratio BigFloat prices remain exact" begin
    for coefficient in (1,-1), direction in (-1,1), sparse_pass in (false,true), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            LinearProblem(sparse(BigFloat[coefficient 2; (sparse_pass ? 1 : 0) (sparse_pass ? 0 : 1)]),
                BigFloat[direction*BigFloat(2)^(-200),0];
                row_lower=[BigFloat(2),nothing],row_upper=BigFloat[2,20],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        original_price = JSimplex._exact_rational(problem.objective[1])
        setprecision(BigFloat,ambient) do
            pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
            result = pass(problem)
            expected = 2coefficient*original_price
            @test JSimplex._exact_rational(result.problem.objective_constant) == expected
            @test JSimplex._exact_rational(only(result.problem.objective)) == -expected
            @test !iszero(result.problem.objective_constant)
            @test JSimplex.postsolve_primal(result,BigFloat[0]) == BigFloat[2coefficient,0]
            @test JSimplex._exact_rational(problem.objective[1]) == original_price
            @test precision(problem.objective[1]) == 256
        end
    end
end

@testset "Unit ratio shortcuts retain exact prices and pivot comparisons" begin
    for kind in (:price,:pivot), sign in (-1,1), direction in (-1,1), sparse_pass in (false,true), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            stored = sign*(BigFloat(1)+direction*BigFloat(2)^(-200))
            coefficient = kind == :pivot ? stored : BigFloat(sign)
            price = kind == :price ? stored : BigFloat(1)
            LinearProblem(sparse(BigFloat[coefficient 1; (sparse_pass ? 1 : 0) (sparse_pass ? 0 : 1)]),BigFloat[price,0];
                row_lower=[BigFloat(1),nothing],row_upper=BigFloat[1,20],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        original_price = JSimplex._exact_rational(problem.objective[1])
        original_coefficient = JSimplex._exact_rational(problem.A[1,1])
        setprecision(BigFloat,ambient) do
            pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
            result = pass(problem)
            @test result.problem === problem
            @test isempty(result.postsolve_stack)
            @test JSimplex._exact_rational(problem.objective[1]) == original_price
            @test JSimplex._exact_rational(problem.A[1,1]) == original_coefficient
        end
    end
end

@testset "Aggregation avoids unit-pivot objective division" begin
function aggregation_unit_objective_ratio_probe(kind; count=128)
    sparse_pass = kind in (:sparse_positive, :sparse_negative)
    coefficient = kind in (:singleton_negative, :sparse_negative) ? -1.0 : kind == :nonunit ? 2.0 : 1.0
    A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
    row_lower = Union{Nothing,Float64}[5.0 for _ in 1:count]
    row_upper = fill(5.0,count)
    if sparse_pass
        A = vcat(A,sparse(reshape(vcat(ones(count),2.0),1,count+1)))
        push!(row_lower,nothing); push!(row_upper,1000.0)
    end
    problem = LinearProblem(A,vcat(fill(kind == :zero ? 0.0 : 1.0,count),2.0);
        objective_constant=7.0,
        row_lower,row_upper,
        column_lower=vcat(fill(1.0,count),nothing),
        column_upper=vcat(fill(3.0,count),nothing))
    pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
    return problem,pass
end

    for (kind,limit) in ((:singleton_positive,26_500),(:singleton_negative,27_000),
                         (:sparse_positive,45_400),(:sparse_negative,45_900),
                         (:nonunit,28_300),(:zero,19_600))
        problem,pass = aggregation_unit_objective_ratio_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = pass(problem)
        coefficient = kind in (:singleton_negative,:sparse_negative) ? -1.0 : kind == :nonunit ? 2.0 : 1.0
        ratio = kind == :zero ? 0.0 : 1/coefficient
        @test result.problem.objective == [2-128ratio]
        @test result.problem.objective_constant == 7+640ratio
        @test JSimplex.postsolve_primal(result,[5-2coefficient]) == vcat(fill(2.0,128),5-2coefficient)
    end
end
